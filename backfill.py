import time
import pytz
from datetime import date, timedelta
from app import fetch_games_for_date
from subscribe import save_game_scores

et = pytz.timezone("US/Eastern")

START = date(2026, 2, 6)   # Adjustable
END   = date(2026, 3, 6)    # Day before records was implemented

def backfill(start: date, end: date):
    current = start
    total_days = (end - start).days + 1
    day_num = 0

    while current <= end:
        day_num += 1
        date_str   = current.strftime("%Y%m%d")
        date_label = current.strftime("%Y-%m-%d")

        try:
            games = fetch_games_for_date(date_str, et)

            # Safeguard in case ESPN has games saved as pre-game or not completed
            completed = [g for g in games if "Final" in g.get("live_score", "")]

            if completed:
                saved = save_game_scores(completed, date_label)
                status = "OK" if saved else "FAIL"
            # Progress checking
                print(f"[{day_num}/{total_days}] {date_label}: {len(completed)} games saved ({status})")
            else:
                print(f"[{day_num}/{total_days}] {date_label}: no completed games, skipping")

        except Exception as e:
            print(f"[{day_num}/{total_days}] {date_label}: ERROR — {e}")

        current += timedelta(days=1)
        time.sleep(0.1)

if __name__ == "__main__":
    print(f"Backfilling {START} → {END}")
    backfill(START, END)
    print("\nDone.")