"""
collect.py — runs one full Bronze + Silver collection cycle.

Run from the project root:
    python 03-pipeline/collect.py

What it does:
    1. Fetches top-10 crypto data from CoinMarketCap
    2. Appends raw data to 01-data/bronze/crypto_raw.csv
    3. Cleans and enriches it, appends to 01-data/silver/crypto_clean.csv
    4. Logs the result to logs/collect.log

You can run this manually or schedule it (see schedule.py).
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

# ── Setup ──────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "collect.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

BRONZE_CRYPTO = ROOT / "01-data" / "bronze" / "crypto_raw.csv"
BRONZE_API    = ROOT / "01-data" / "bronze" / "api_calls.csv"
SILVER        = ROOT / "01-data" / "silver" / "crypto_clean.csv"

STABLECOINS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "FRAX"}

CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
CMC_PARAMS = {"start": "1", "limit": "10", "convert": "USD"}


# ── Bronze: fetch and store raw data ──────────────────────────────────────────

def fetch_from_api() -> dict:
    api_key = os.getenv("COINMARKETCAP_API_KEY")
    if not api_key:
        raise RuntimeError("COINMARKETCAP_API_KEY not set in .env")

    response = requests.get(
        CMC_URL,
        params=CMC_PARAMS,
        headers={"Accepts": "application/json", "X-CMC_PRO_API_KEY": api_key},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def save_bronze(raw: dict) -> pd.DataFrame:
    collected_at = datetime.now(timezone.utc).isoformat()

    df = pd.json_normalize(raw["data"], sep="_")
    df["collected_at"] = collected_at

    status = pd.json_normalize(raw["status"], sep="_")
    status["collected_at"] = collected_at
    status["endpoint"] = CMC_URL
    status["coins_returned"] = len(df)

    _append_csv(df, BRONZE_CRYPTO)
    _append_csv(status, BRONZE_API)

    log.info("Bronze: saved %d rows (snapshot: %s)", len(df), collected_at)
    return df


# ── Silver: clean and enrich Bronze data ──────────────────────────────────────

def build_silver(bronze_df: pd.DataFrame) -> pd.DataFrame:
    df = bronze_df.copy()

    # Fix timestamps
    for col in ["collected_at", "last_updated", "quote_USD_last_updated", "date_added"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

    # Flags
    df["is_stablecoin"] = df["symbol"].isin(STABLECOINS)
    df["is_token"] = df["platform_id"].notna()

    # Log returns
    for pct_col, log_col in [
        ("quote_USD_percent_change_1h",  "log_return_1h"),
        ("quote_USD_percent_change_24h", "log_return_24h"),
        ("quote_USD_percent_change_7d",  "log_return_7d"),
    ]:
        df[log_col] = np.log(1 + df[pct_col] / 100)

    # Ratios
    df["volume_to_mcap"]     = df["quote_USD_volume_24h"] / df["quote_USD_market_cap"]
    df["supply_utilization"] = df["circulating_supply"] / df["max_supply"]

    # Dedup
    df = df.drop_duplicates(subset=["symbol", "collected_at"])

    # Validate
    assert (df["quote_USD_price"] > 0).all(), "Negative prices in Silver"
    assert (df["quote_USD_market_cap"] > 0).all(), "Negative market caps in Silver"

    _append_csv(df, SILVER)
    log.info("Silver: saved %d rows", len(df))
    return df


# ── Helpers ────────────────────────────────────────────────────────────────────

def _append_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    df.to_csv(path, mode="a", header=not file_exists, index=False)


def bronze_row_count() -> int:
    return pd.read_csv(BRONZE_CRYPTO).shape[0] if BRONZE_CRYPTO.exists() else 0


# ── Entry point ────────────────────────────────────────────────────────────────

def run():
    log.info("Collection starting")
    try:
        raw = fetch_from_api()
        bronze_df = save_bronze(raw)
        build_silver(bronze_df)
        total = bronze_row_count()
        log.info("Done. Bronze total: %d rows (%d snapshots)", total, total // 10)
    except Exception as exc:
        log.error("Collection failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    run()
