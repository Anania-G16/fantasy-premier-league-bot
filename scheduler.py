from apscheduler.schedulers.background import BackgroundScheduler
import requests
import sqlite3
import config
from handlers import generate_current_gameweek_table, generate_winning_counts_table

TELEGRAM_TOKEN = getattr(config, 'TELEGRAM_TOKEN', None)
TEST_GROUP_ID = getattr(config, 'TEST_GROUP_ID', None)
LEAGUE_ID = getattr(config, 'LEAGUE_ID', None)

def test_send_updates():
    if not TEST_GROUP_ID:
        print("❌ TEST_GROUP_ID not set in config.py")
        return

    # Combine live table and wins table for a thorough test payload
    message_text = "🧪 *Automated 2-Minute Test Update* 🧪\n\n"
    message_text += generate_current_gameweek_table() + "\n\n"
    message_text += generate_winning_counts_table()

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TEST_GROUP_ID,
        "text": message_text
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ 2-minute test message sent successfully to the group!")
        else:
            print(f"❌ Failed to send message: {response.text}")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")

def setup_scheduler():
    scheduler = BackgroundScheduler()
    # Runs the test update every 2 minutes
    scheduler.add_job(test_send_updates, 'interval', minutes=2)
    scheduler.start()
    print("⏳ Scheduler started: testing updates every 2 minutes.")