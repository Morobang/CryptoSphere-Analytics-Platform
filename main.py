"""
CryptoSphere Analytics Platform — CLI entry point.

Commands:
    collect     Fetch current top-10 crypto data and store (CSV + SQL)
    etl         Run Bronze → Silver → Gold SQL ETL pipeline
    schedule    Start the collection scheduler (runs every 4 hours)
    status      Show how much data is currently stored

Usage:
    python main.py collect
    python main.py etl
    python main.py schedule
    python main.py status
"""

import argparse
import logging
import sys
from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_collect(_args):
    """Fetch data from CoinMarketCap and write to CSV + SQL Bronze layer."""
    sys.path.insert(0, str(Path("01-data/src").resolve()))
    from data_collection_manager import DataCollectionManager

    collector = DataCollectionManager()
    result = collector.collect_and_store()

    if result.api_success:
        print(f"Collected:  {result.csv_rows_written} rows → CSV")
        print(f"           {result.db_rows_written} rows → SQL (batch {result.batch_id})")
    else:
        print(f"Collection failed: {result.error}")
        sys.exit(1)


def cmd_etl(_args):
    """Run the Silver and Gold ETL stored procedures."""
    import os
    import pyodbc
    from dotenv import load_dotenv

    load_dotenv()
    server = os.getenv("SQL_SERVER", "localhost")
    database = os.getenv("SQL_DATABASE", "cryptosphere_analytics")

    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    )

    try:
        conn = pyodbc.connect(conn_str)
    except Exception as exc:
        print(f"Cannot connect to SQL Server: {exc}")
        sys.exit(1)

    steps = [
        ("Silver ETL", "EXEC silver.sp_run_silver_etl"),
        ("Gold ETL",   "EXEC gold.sp_run_gold_etl"),
    ]

    with conn:
        cursor = conn.cursor()
        for label, sql in steps:
            try:
                cursor.execute(sql)
                conn.commit()
                print(f"{label}: OK")
            except Exception as exc:
                print(f"{label}: FAILED — {exc}")
                logger.error("%s failed: %s", label, exc)

    conn.close()


def cmd_schedule(_args):
    """Start the APScheduler job that collects data every 4 hours."""
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler(timezone="UTC")

    @scheduler.scheduled_job("interval", hours=4, id="crypto_collect")
    def collect_job():
        sys.path.insert(0, str(Path("01-data/src").resolve()))
        from data_collection_manager import DataCollectionManager
        result = DataCollectionManager().collect_and_store()
        logger.info("Scheduled collect: %s", result)

    print("Scheduler started. Collecting every 4 hours. Press Ctrl+C to stop.")
    logger.info("Scheduler started (interval=4h)")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


def cmd_status(_args):
    """Show how much data is currently in the raw CSV files."""
    import pandas as pd

    raw_dir = Path("01-data/raw")
    files = {
        "cryptocurrency_data.csv": "Crypto snapshots",
        "api_status.csv":          "API call log",
    }

    for filename, label in files.items():
        path = raw_dir / filename
        if path.exists():
            df = pd.read_csv(path)
            print(f"{label}: {len(df):,} rows  ({path})")
        else:
            print(f"{label}: not found ({path})")


# ── Dispatch ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CryptoSphere Analytics Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    sub.add_parser("collect",  help="Fetch current crypto data and store it")
    sub.add_parser("etl",      help="Run Bronze → Silver → Gold ETL")
    sub.add_parser("schedule", help="Start scheduled collection (every 4 hours)")
    sub.add_parser("status",   help="Show current data volume")

    args = parser.parse_args()

    dispatch = {
        "collect":  cmd_collect,
        "etl":      cmd_etl,
        "schedule": cmd_schedule,
        "status":   cmd_status,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
