"""
schedule.py — runs the collection pipeline on a schedule.

Run from the project root:
    python 03-pipeline/schedule.py

Collects every 4 hours. With the free CoinMarketCap tier (333 credits/day),
4 hours = 6 runs/day = 6 credits/day. Well within the limit.

Leave this running in a terminal. Press Ctrl+C to stop.
Logs go to logs/collect.log so you can audit every run.
"""

import logging
import sys
import time
from pathlib import Path

# Make sure collect.py is importable
sys.path.insert(0, str(Path(__file__).parent))
import collect

log = logging.getLogger(__name__)

INTERVAL_HOURS = 4
INTERVAL_SECONDS = INTERVAL_HOURS * 60 * 60


def main():
    print(f"Scheduler started. Collecting every {INTERVAL_HOURS} hours.")
    print("Press Ctrl+C to stop. Logs → logs/collect.log")
    print()

    # Run immediately on start so you don't wait 4 hours for first data
    collect.run()

    while True:
        next_run = time.time() + INTERVAL_SECONDS
        next_run_str = time.strftime("%H:%M:%S", time.localtime(next_run))
        print(f"Next collection at: {next_run_str}")

        try:
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
            break

        collect.run()


if __name__ == "__main__":
    main()
