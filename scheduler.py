from apscheduler.schedulers.background import BackgroundScheduler
from fpl_api import fetch_standings
import sqlite3

def check_gameweek_winner():
    data = fetch_standings()
    if not data:
        return
    results = data.get("standings", {}).get("results", [])
    if not results:
        return
    
    # Sort by gameweek points (event_total)
    sorted_by_gw = sorted(results, key=lambda x: x.get("event_total", 0), reverse=True)
    winner = sorted_by_gw[0]
    
    # Log winner to SQLite database...
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    # Insert logic here
    conn.commit()
    conn.close()

def setup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_gameweek_winner, 'cron', day_of_week='tue', hour=9)
    scheduler.start()