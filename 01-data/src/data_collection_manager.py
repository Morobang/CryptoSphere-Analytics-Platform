"""
CoinMarketCap data collection module.

Encapsulates the logic from 02-notebooks/01-data-acquisition/01-api_data_collection.ipynb
so it can be called from main.py and scheduled jobs without notebook overhead.

Usage:
    from data_collection_manager import DataCollectionManager

    collector = DataCollectionManager()
    result = collector.collect_and_store()
    print(result)
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyodbc
from dotenv import load_dotenv
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

load_dotenv()

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).resolve().parents[1] / "raw"
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
CMC_PARAMS = {"start": "1", "limit": "10", "convert": "USD"}


class CollectionResult:
    def __init__(self):
        self.timestamp = datetime.utcnow()
        self.api_success = False
        self.csv_rows_written = 0
        self.db_rows_written = 0
        self.batch_id = None
        self.error = None

    def __repr__(self):
        return (
            f"CollectionResult(time={self.timestamp.isoformat()}, "
            f"api={self.api_success}, csv={self.csv_rows_written}, "
            f"db={self.db_rows_written}, batch={self.batch_id}, "
            f"error={self.error})"
        )


class DataCollectionManager:
    """
    Collects top-10 crypto data from CoinMarketCap and stores it in:
      - CSV files (01-data/raw/) in append mode
      - SQL Server Bronze layer via stored procedures
    """

    def __init__(self):
        self.api_key = os.getenv("COINMARKETCAP_API_KEY")
        self.sql_server = os.getenv("SQL_SERVER", "localhost")
        self.sql_database = os.getenv("SQL_DATABASE", "cryptosphere_analytics")
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────────────

    def collect_and_store(self) -> CollectionResult:
        """Run one full collection cycle: fetch → save CSV → save SQL."""
        result = CollectionResult()

        df_crypto, df_status = self._fetch_from_api()
        if df_crypto is None:
            result.error = "API fetch failed"
            return result

        result.api_success = True
        logger.info("Fetched %d crypto records from API", len(df_crypto))

        result.csv_rows_written = self._save_to_csv(df_crypto, df_status)

        batch_id, db_rows = self._save_to_database(df_crypto, df_status)
        result.batch_id = batch_id
        result.db_rows_written = db_rows

        return result

    # ── Private: API fetch ─────────────────────────────────────────────────────

    def _fetch_from_api(self):
        if not self.api_key:
            logger.error("COINMARKETCAP_API_KEY not set in environment")
            return None, None

        session = Session()
        session.headers.update({
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": self.api_key,
        })

        try:
            response = session.get(CMC_URL, params=CMC_PARAMS, timeout=30)
            response.raise_for_status()
        except (ConnectionError, Timeout, TooManyRedirects) as exc:
            logger.error("API request failed: %s", exc)
            return None, None

        data = json.loads(response.text)
        df_crypto = pd.json_normalize(data["data"], sep="_")
        df_status = pd.json_normalize(data["status"], sep="_")
        df_crypto["collection_timestamp"] = datetime.utcnow().isoformat()
        df_status["collection_timestamp"] = datetime.utcnow().isoformat()

        return df_crypto, df_status

    # ── Private: CSV storage ───────────────────────────────────────────────────

    def _save_to_csv(self, df_crypto: pd.DataFrame, df_status: pd.DataFrame) -> int:
        written = 0
        for df, filename in [
            (df_crypto, "cryptocurrency_data.csv"),
            (df_status, "api_status.csv"),
        ]:
            path = RAW_DATA_DIR / filename
            file_exists = path.exists()
            df.to_csv(path, mode="a", header=not file_exists, index=False)
            written += len(df)
            logger.debug("Wrote %d rows to %s (append=%s)", len(df), filename, file_exists)
        return written

    # ── Private: SQL Server storage ────────────────────────────────────────────

    def _get_connection(self):
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={self.sql_server};"
            f"DATABASE={self.sql_database};"
            "Trusted_Connection=yes;"
        )
        try:
            return pyodbc.connect(conn_str)
        except Exception as exc:
            logger.warning("SQL Server not available: %s", exc)
            return None

    def _save_to_database(self, df_crypto: pd.DataFrame, df_status: pd.DataFrame):
        conn = self._get_connection()
        if conn is None:
            return None, 0

        batch_id = None
        rows_written = 0

        try:
            cursor = conn.cursor()

            # Step 1: insert API status, get batch_id
            status_row = df_status.iloc[0]
            cursor.execute(
                """
                EXEC bronze.sp_insert_api_status
                    @timestamp = ?, @error_code = ?, @error_message = ?,
                    @elapsed = ?, @credit_count = ?, @notice = ?,
                    @total_count = ?, @api_endpoint = ?,
                    @request_parameters = ?, @response_size_bytes = ?,
                    @records_processed = ?
                """,
                (
                    _clean(status_row.get("timestamp")),
                    _clean(status_row.get("error_code", 0)),
                    _clean(status_row.get("error_message")),
                    _clean(status_row.get("elapsed")),
                    _clean(status_row.get("credit_count")),
                    _clean(status_row.get("notice")),
                    _clean(status_row.get("total_count")),
                    CMC_URL,
                    str(CMC_PARAMS),
                    None,
                    len(df_crypto),
                ),
            )
            row = cursor.fetchone()
            if row and row[2] == "SUCCESS":
                batch_id = row[1]
            else:
                logger.error("Status insert failed: %s", row)
                conn.rollback()
                return None, 0

            # Step 2: insert crypto records linked to batch_id
            for _, crypto_row in df_crypto.iterrows():
                cursor.execute(
                    """
                    EXEC bronze.sp_insert_cryptocurrency_data
                        @batch_id = ?, @id = ?, @name = ?, @symbol = ?,
                        @slug = ?, @num_market_pairs = ?, @date_added = ?,
                        @max_supply = ?, @circulating_supply = ?,
                        @total_supply = ?, @infinite_supply = ?,
                        @platform = ?, @platform_id = ?, @platform_name = ?,
                        @platform_symbol = ?, @platform_slug = ?,
                        @platform_token_address = ?, @cmc_rank = ?,
                        @self_reported_circulating_supply = ?,
                        @self_reported_market_cap = ?, @tvl_ratio = ?,
                        @last_updated = ?, @quote_USD_price = ?,
                        @quote_USD_volume_24h = ?,
                        @quote_USD_volume_change_24h = ?,
                        @quote_USD_percent_change_1h = ?,
                        @quote_USD_percent_change_24h = ?,
                        @quote_USD_percent_change_7d = ?,
                        @quote_USD_percent_change_30d = ?,
                        @quote_USD_percent_change_60d = ?,
                        @quote_USD_percent_change_90d = ?,
                        @quote_USD_market_cap = ?,
                        @quote_USD_market_cap_dominance = ?,
                        @quote_USD_fully_diluted_market_cap = ?,
                        @quote_USD_tvl = ?,
                        @quote_USD_last_updated = ?, @tags = ?
                    """,
                    (
                        batch_id,
                        _clean(crypto_row.get("id")),
                        _clean(crypto_row.get("name")),
                        _clean(crypto_row.get("symbol")),
                        _clean(crypto_row.get("slug")),
                        _clean(crypto_row.get("num_market_pairs")),
                        _clean(crypto_row.get("date_added")),
                        _clean(crypto_row.get("max_supply")),
                        _clean(crypto_row.get("circulating_supply")),
                        _clean(crypto_row.get("total_supply")),
                        _clean(crypto_row.get("infinite_supply")),
                        _clean(crypto_row.get("platform")),
                        _clean(crypto_row.get("platform_id")),
                        _clean(crypto_row.get("platform_name")),
                        _clean(crypto_row.get("platform_symbol")),
                        _clean(crypto_row.get("platform_slug")),
                        _clean(crypto_row.get("platform_token_address")),
                        _clean(crypto_row.get("cmc_rank")),
                        _clean(crypto_row.get("self_reported_circulating_supply")),
                        _clean(crypto_row.get("self_reported_market_cap")),
                        _clean(crypto_row.get("tvl_ratio")),
                        _clean(crypto_row.get("last_updated")),
                        _clean(crypto_row.get("quote_USD_price")),
                        _clean(crypto_row.get("quote_USD_volume_24h")),
                        _clean(crypto_row.get("quote_USD_volume_change_24h")),
                        _clean(crypto_row.get("quote_USD_percent_change_1h")),
                        _clean(crypto_row.get("quote_USD_percent_change_24h")),
                        _clean(crypto_row.get("quote_USD_percent_change_7d")),
                        _clean(crypto_row.get("quote_USD_percent_change_30d")),
                        _clean(crypto_row.get("quote_USD_percent_change_60d")),
                        _clean(crypto_row.get("quote_USD_percent_change_90d")),
                        _clean(crypto_row.get("quote_USD_market_cap")),
                        _clean(crypto_row.get("quote_USD_market_cap_dominance")),
                        _clean(crypto_row.get("quote_USD_fully_diluted_market_cap")),
                        _clean(crypto_row.get("quote_USD_tvl")),
                        _clean(crypto_row.get("quote_USD_last_updated")),
                        _clean(crypto_row.get("tags")),
                    ),
                )
                row = cursor.fetchone()
                if row and row[2] == "SUCCESS":
                    rows_written += 1
                else:
                    logger.warning(
                        "Failed to insert %s: %s",
                        crypto_row.get("symbol"),
                        row[3] if row else "no result",
                    )

            conn.commit()
            logger.info(
                "DB insert complete: batch=%s, rows=%d", batch_id, rows_written
            )

        except Exception as exc:
            logger.error("Database error: %s", exc)
            conn.rollback()
            return None, 0
        finally:
            conn.close()

        return batch_id, rows_written


def _clean(value):
    """Convert pandas NaN / None to SQL NULL; stringify complex types."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (list, dict)):
        return str(value)
    return value
