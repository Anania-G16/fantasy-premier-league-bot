from telegram import Update
from telegram.ext import ContextTypes
import sqlite3
import requests
from config import LEAGUE_ID, MANAGER_HANDLES

def get_fpl_bootstrap():
    """Helper to fetch bootstrap-static data for the current active gameweek."""
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        for event in res.json().get("events", []):
            if event.get("is_current"):
                return event.get("id")
    return None

def get_identity(entry_id, player_name):
    """Formats manager identity as 'Name (handle)' or just 'Name' if no handle exists."""
    handle = MANAGER_HANDLES.get(entry_id)
    if handle:
        return f"{player_name} ({handle})"
    return player_name

def generate_current_gameweek_table():
    current_gw = get_fpl_bootstrap()
    if not current_gw:
        return "❌ Could not determine the current active gameweek."

    standings_url = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
    res = requests.get(standings_url, headers={"User-Agent": "Mozilla/5.0"})
    if res.status_code != 200:
        return "❌ Failed to fetch league standings."

    results = res.json().get("standings", {}).get("results", [])
    if not results:
        return "No managers found."

    gw_scores = []
    for manager in results:
        entry_id = manager.get("entry")
        player_name = manager.get("player_name")
        gw_points = manager.get("event_total", 0)

        gw_scores.append({
            "entry_id": entry_id,
            "player_name": player_name,
            "points": gw_points
        })

    gw_scores.sort(key=lambda x: x["points"], reverse=True)

    msg = f"🟢 Gameweek {current_gw} Live Table 🟢\n\n"
    for idx, m in enumerate(gw_scores, start=1):
        identity = get_identity(m["entry_id"], m["player_name"])
        msg += f"{idx}. {identity} — {m['points']} pts\n"

    return msg

def generate_total_points_table():
    standings_url = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
    res = requests.get(standings_url, headers={"User-Agent": "Mozilla/5.0"})
    if res.status_code != 200:
        return "❌ Failed to fetch total standings."

    data = res.json()
    league_name = data.get("league", {}).get("name", "League of Royalties")
    league_name = league_name.replace("_", " ")
    
    results = data.get("standings", {}).get("results", [])

    if not results:
        return "No managers found."

    msg = f"👑 {league_name} — Total Standings 👑\n\n"
    for idx, manager in enumerate(results, start=1):
        entry_id = manager.get("entry")
        player_name = manager.get("player_name")
        total = manager.get("total")
        
        identity = get_identity(entry_id, player_name)
        identity = identity.replace("_", " ")

        msg += f"{idx}. {identity} — {total} pts\n"

    return msg

def generate_net_gain_table():
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT gameweek, manager_name, pot_amount FROM gameweek_winners')
    winners_data = cursor.fetchall()
    conn.close()

    all_managers = [
        "Ab Best",
        "Yoda Belay",
        "Antiko Kasahun",
        "Kaleab Great",
        "Anex GB",
        "Vladmir MCI"
    ]

    gw_participants = {
        1: ["Ab Best", "Yoda Belay", "Anex GB", "Vladmir MCI"],
        2: ["Ab Best", "Yoda Belay", "Anex GB", "Vladmir MCI", "Antiko Kasahun", "Kaleab Great"]
    }

    winner_dict = {gw: (winner, pot) for gw, winner, pot in winners_data}

    ledger = {name: 0 for name in all_managers}

    for gw, participants in gw_participants.items():
        if gw not in winner_dict:
            continue
        winner_name, pot = winner_dict[gw]
        for manager in participants:
            if manager == winner_name:
                ledger[manager] += (pot - 50)
            else:
                ledger[manager] -= 50

    sorted_ledger = sorted(ledger.items(), key=lambda x: x[1], reverse=True)

    msg = f"💸 League Financial Ledger (Net Gain/Loss) 💸\n\n"
    if not winners_data:
        msg += "No financial data recorded yet. Run sync for completed gameweeks!"
        return msg

    for idx, (manager_name, net_amount) in enumerate(sorted_ledger, start=1):
        sign = "+" if net_amount > 0 else ""
        msg += f"{idx}. {manager_name} — {sign}{net_amount} Birr\n"

    return msg


# --- Telegram Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👑 Welcome to Sir Royale Bot! 👑\n\n"
        "Your official 24/7 FPL manager and financial ledger for the League of Royalties.\n\n"
        "Use these commands to check the action:\n"
        "/live - View current gameweek live standings\n"
        "/total - View overall FPL league standings\n"
        "/final [gw] - View final standings with medals (defaults to latest finished gameweek)\n"
        "/net - View the financial ledger (Net Gain/Loss)\n"
        "/wins - View total gameweek win counts for each manager\n"
    )
    await update.message.reply_text(welcome_text)
async def live_standings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching live gameweek standings...")
    table_text = generate_current_gameweek_table()
    await update.message.reply_text(table_text)

async def total_standings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching total league standings...")
    table_text = generate_total_points_table()
    await update.message.reply_text(table_text)

async def final_standings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⏳ Figuring out latest gameweek & fetching standings...")

    target_gw = None
    
    # Check if a gameweek argument was passed (e.g. /final 2)
    if context.args and context.args[0].isdigit():
        target_gw = int(context.args[0])
    else:
        # Auto-detect latest finished gameweek from bootstrap-static
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if res.status_code == 200:
                events = res.json().get("events", [])
                finished_gws = [e.get("id") for e in events if e.get("finished") == True]
                if finished_gws:
                    target_gw = max(finished_gws)
                else:
                    current_gw = get_fpl_bootstrap()
                    if current_gw and current_gw > 1:
                        target_gw = current_gw - 1
                    else:
                        target_gw = 1
        except Exception:
            target_gw = None

    if not target_gw:
        await status_msg.edit_text("❌ Could not determine the gameweek automatically. Try typing it explicitly, e.g., `/final 2`")
        return

    await status_msg.edit_text(f"Fetching final standings for Gameweek {target_gw}...")

    standings_url = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
    res = requests.get(standings_url, headers={"User-Agent": "Mozilla/5.0"})
    if res.status_code != 200:
        await status_msg.edit_text("❌ Failed to fetch league standings.")
        return

    results = res.json().get("standings", {}).get("results", [])
    if not results:
        await status_msg.edit_text("No managers found.")
        return

    gw_scores = []
    
    for manager in results:
        entry_id = manager.get("entry")
        player_name = manager.get("player_name")
        
        history_url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/history/"
        h_res = requests.get(history_url, headers={"User-Agent": "Mozilla/5.0"})
        
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

    msg = f"🏆 Gameweek {target_gw} Final Standings 🏆\n\n"
    for idx, m in enumerate(gw_scores, start=1):
        identity = get_identity(m["entry_id"], m["player_name"]).replace("_", " ")
        rank_display = medals.get(idx, f"{idx}.")
        msg += f"{rank_display} {identity} — {m['points']} pts\n"

    await status_msg.edit_text(msg)

async def net_ledger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    table_text = generate_net_gain_table()
    await update.message.reply_text(table_text)
from collections import defaultdict
import sqlite3

def generate_winning_counts_table():
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT manager_name, gameweek 
        FROM gameweek_winners 
        ORDER BY manager_name, gameweek ASC
    ''')
    data = cursor.fetchall()
    conn.close()

    # Group gameweeks by manager name
    manager_wins = defaultdict(list)
    for manager_name, gw in data:
        manager_wins[manager_name].append(str(gw))

    # Sort managers by total wins descending
    sorted_managers = sorted(manager_wins.items(), key=lambda x: len(x[1]), reverse=True)

    msg = "🏆 Gameweek Winner Counts & History 🏆\n\n"
    if not sorted_managers:
        msg += "No gameweek winners recorded yet!"
        return msg

    for idx, (manager_name, gws) in enumerate(sorted_managers, start=1):
        count = len(gws)
        gw_list = ", ".join(gws)
        msg += f"{idx}. {manager_name} — {count} — GW({gw_list})\n"

    return msg
async def wins_standings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    table_text = generate_winning_counts_table()
    await update.message.reply_text(table_text)