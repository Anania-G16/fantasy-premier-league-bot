from apscheduler.schedulers.background import BackgroundScheduler
import requests
import config
from handlers import (
    generate_current_gameweek_table,
    generate_total_points_table,
    generate_net_gain_table,
    generate_winning_counts_table,
    get_fpl_bootstrap,
    get_identity,
    LEAGUE_ID
)

TELEGRAM_TOKEN = getattr(config, 'TELEGRAM_TOKEN', None)
TEST_GROUP_ID = getattr(config, 'TEST_GROUP_ID', None)

_last_live_posted_gw = None

def send_telegram_message(text):
    """Helper to dispatch messages safely to the Telegram group."""
    if not TEST_GROUP_ID or not TELEGRAM_TOKEN:
        return
    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TEST_GROUP_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(send_url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Error sending message to Telegram: {e}")

def post_periodic_live_updates():
    """Job 1: Periodically post live gameweek standings and overall standings while a gameweek is active."""
    global _last_live_posted_gw
    if not TEST_GROUP_ID:
        return

    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return
        
        data = response.json()
        current_gw = next((gw for gw in data.get("events", []) if gw.get("is_current") == True), None)
        
        if not current_gw:
            return

        gw_id = current_gw.get("id")
        is_finished = current_gw.get("finished", False)

        # Only post if the gameweek is actively running
        if not is_finished:
            print(f"📊 Posting periodic live update for Gameweek {gw_id}...")
            
            message_text = f"📊 *Gameweek {gw_id} Periodic Live Update* 📊\n\n"
            message_text += generate_current_gameweek_table() + "\n\n"
            message_text += generate_total_points_table()

            send_telegram_message(message_text)
            _last_live_posted_gw = gw_id
        else:
            if _last_live_posted_gw == gw_id:
                _last_live_posted_gw = None
            
    except Exception as e:
        print(f"❌ Error in periodic live update scheduler: {e}")

def check_gameweek_status_and_notify():
    """Job 2: Monitor for gameweek completion to push final standings, win counts, overall standings, and financial ledger."""
    if not TEST_GROUP_ID:
        return

    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return
        
        data = response.json()
        current_gw = next((gw for gw in data.get("events", []) if gw.get("is_current") == True), None)
        
        if not current_gw:
            return

        gw_id = current_gw.get("id")
        is_finished = current_gw.get("finished", False)
        data_checked = current_gw.get("data_checked", False)

        # Trigger when the gameweek is officially closed and data is verified
        if is_finished and data_checked:
            print(f"🏁 Gameweek {gw_id} finalized! Broadcasting full final summary...")
            
            target_gw = gw_id

            standings_url = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
            s_res = requests.get(standings_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            
            final_gw_block = ""
            if s_res.status_code == 200:
                results = s_res.json().get("standings", {}).get("results", [])
                gw_scores = []
                for manager in results:
                    entry_id = manager.get("entry")
                    player_name = manager.get("player_name")
                    
                    history_url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/history/"
                    h_res = requests.get(history_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    
                    points = 0
                    if h_res.status_code == 200:
                        history_data = h_res.json().get("current", [])
                        for event in history_data:
                            if event.get("event") == target_gw:
                                points = event.get("points", 0)
                                break

                    gw_scores.append({
                        "entry_id": entry_id,
                        "player_name": player_name,
                        "points": points
                    })

                gw_scores.sort(key=lambda x: x["points"], reverse=True)
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}

                final_gw_block = f"🏆 Gameweek {target_gw} Final Standings 🏆\n"
                for idx, m in enumerate(gw_scores, start=1):
                    identity = get_identity(m["entry_id"], m["player_name"]).replace("_", " ")
                    rank_display = medals.get(idx, f"{idx}.")
                    final_gw_block += f"{rank_display} {identity} — {m['points']} pts\n"

            message_text = f"🚨 *Official Gameweek {target_gw} Final Wrap-up* 🚨\n\n"
            if final_gw_block:
                message_text += final_gw_block + "\n\n"
            else:
                message_text += generate_current_gameweek_table() + "\n\n"
            
            message_text += generate_winning_counts_table() + "\n\n"
            message_text += generate_total_points_table() + "\n\n"
            message_text += generate_net_gain_table()

            send_telegram_message(message_text)
            
    except Exception as e:
        print(f"❌ Error checking FPL API status for final notification: {e}")

def setup_scheduler():
    scheduler = BackgroundScheduler()
    
    # 🧪 TEST MODE: Set to seconds for rapid local testing
    # Remember to change back to hours=6 and minutes=30 before deploying to production!
    scheduler.add_job(post_periodic_live_updates, 'interval', seconds=15)
    scheduler.add_job(check_gameweek_status_and_notify, 'interval', seconds=30)
    
    scheduler.start()
    print("⏳ TEST Schedulers active: Live feed (every 15s) + Final closing check (every 30s).")































# from apscheduler.schedulers.background import BackgroundScheduler
# import requests
# import config
# from handlers import (
#     generate_current_gameweek_table,
#     generate_total_points_table,
#     generate_net_gain_table,
#     generate_winning_counts_table,
#     get_fpl_bootstrap,
#     get_identity,
#     LEAGUE_ID
# )

# TELEGRAM_TOKEN = getattr(config, 'TELEGRAM_TOKEN', None)
# TEST_GROUP_ID = getattr(config, 'TEST_GROUP_ID', None)

# _last_live_posted_gw = None

# def send_telegram_message(text):
#     """Helper to dispatch messages safely to the Telegram group."""
#     if not TEST_GROUP_ID or not TELEGRAM_TOKEN:
#         return
#     send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
#     payload = {
#         "chat_id": TEST_GROUP_ID,
#         "text": text,
#         "parse_mode": "Markdown"
#     }
#     try:
#         requests.post(send_url, json=payload, timeout=10)
#     except Exception as e:
#         print(f"❌ Error sending message to Telegram: {e}")

# def post_periodic_live_updates():
#     """Job 1: Periodically post live gameweek standings and overall standings while a gameweek is active."""
#     global _last_live_posted_gw
#     if not TEST_GROUP_ID:
#         return

#     url = "https://fantasy.premierleague.com/api/bootstrap-static/"
#     try:
#         response = requests.get(url, timeout=10)
#         if response.status_code != 200:
#             return
        
#         data = response.json()
#         current_gw = next((gw for gw in data.get("events", []) if gw.get("is_current") == True), None)
        
#         if not current_gw:
#             return

#         gw_id = current_gw.get("id")
#         is_finished = current_gw.get("finished", False)

#         # Only post if the gameweek is actively running
#         if not is_finished:
#             print(f"📊 Posting periodic live update for Gameweek {gw_id}...")
            
#             message_text = f"📊 *Gameweek {gw_id} Periodic Live Update* 📊\n\n"
#             message_text += generate_current_gameweek_table() + "\n\n"
#             message_text += generate_total_points_table()

#             send_telegram_message(message_text)
#             _last_live_posted_gw = gw_id
#         else:
#             if _last_live_posted_gw == gw_id:
#                 _last_live_posted_gw = None
            
#     except Exception as e:
#         print(f"❌ Error in periodic live update scheduler: {e}")

# def check_gameweek_status_and_notify():
#     """Job 2: Monitor for gameweek completion to push final standings, win counts, overall standings, and financial ledger."""
#     if not TEST_GROUP_ID:
#         return

#     url = "https://fantasy.premierleague.com/api/bootstrap-static/"
#     try:
#         response = requests.get(url, timeout=10)
#         if response.status_code != 200:
#             return
        
#         data = response.json()
#         current_gw = next((gw for gw in data.get("events", []) if gw.get("is_current") == True), None)
        
#         if not current_gw:
#             return

#         gw_id = current_gw.get("id")
#         is_finished = current_gw.get("finished", False)
#         data_checked = current_gw.get("data_checked", False)

#         # Trigger when the gameweek is officially closed and data is verified
#         if is_finished and data_checked:
#             print(f"🏁 Gameweek {gw_id} finalized! Broadcasting full final summary...")
            
#             # Determine target finished gameweek safely
#             target_gw = gw_id

#             # Fetch standings and evaluate individual scores for the final summary table with medals
#             standings_url = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
#             s_res = requests.get(standings_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            
#             final_gw_block = ""
#             if s_res.status_code == 200:
#                 results = s_res.json().get("standings", {}).get("results", [])
#                 gw_scores = []
#                 for manager in results:
#                     entry_id = manager.get("entry")
#                     player_name = manager.get("player_name")
                    
#                     history_url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/history/"
#                     h_res = requests.get(history_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    
#                     points = 0
#                     if h_res.status_code == 200:
#                         history_data = h_res.json().get("current", [])
#                         for event in history_data:
#                             if event.get("event") == target_gw:
#                                 points = event.get("points", 0)
#                                 break

#                     gw_scores.append({
#                         "entry_id": entry_id,
#                         "player_name": player_name,
#                         "points": points
#                     })

#                 gw_scores.sort(key=lambda x: x["points"], reverse=True)
#                 medals = {1: "🥇", 2: "🥈", 3: "🥉"}

#                 final_gw_block = f"🏆 Gameweek {target_gw} Final Standings 🏆\n"
#                 for idx, m in enumerate(gw_scores, start=1):
#                     identity = get_identity(m["entry_id"], m["player_name"]).replace("_", " ")
#                     rank_display = medals.get(idx, f"{idx}.")
#                     final_gw_block += f"{rank_display} {identity} — {m['points']} pts\n"

#             # Combine all core functionalities into the automated background broadcast
#             message_text = f"🚨 *Official Gameweek {target_gw} Final Wrap-up* 🚨\n\n"
#             if final_gw_block:
#                 message_text += final_gw_block + "\n\n"
#             else:
#                 message_text += generate_current_gameweek_table() + "\n\n"
            
#             message_text += generate_winning_counts_table() + "\n\n"
#             message_text += generate_total_points_table() + "\n\n"
#             message_text += generate_net_gain_table()

#             send_telegram_message(message_text)
            
#     except Exception as e:
#         print(f"❌ Error checking FPL API status for final notification: {e}")

# def setup_scheduler():
#     scheduler = BackgroundScheduler()
    
#     # Job 1: Post live table and total points update every 6 hours while active
#     scheduler.add_job(post_periodic_live_updates, 'interval', hours=6)
    
#     # Job 2: Check FPL API every 30 minutes to capture final gameweek wrap-ups and trigger the full suite
#     scheduler.add_job(check_gameweek_status_and_notify, 'interval', minutes=30)
    
#     scheduler.start()
#     print("⏳ Dual Schedulers active: Live feed (every 6h) + Final closing check (every 30m).")
