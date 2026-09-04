from telegram import Update
from telegram.ext import ContextTypes
from fpl_api import fetch_standings

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Sir Royale is online, inspecting the realm, and tracking the League of Royalties! ⚽")

async def standings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = fetch_standings()
    if not data:
        await update.message.reply_text("❌ Failed to fetch data from the FPL API. Check your League ID!")
        return

    league_name = data.get("league", {}).get("name", "League of Royalties")
    results = data.get("standings", {}).get("results", [])

    if not results:
        await update.message.reply_text("No managers found in this league yet.")
        return

    msg = f"👑 *{league_name} Standings* 👑\n\n"
    for idx, manager in enumerate(results[:10], start=1):
        name = manager.get("player_name")
        team = manager.get("entry_name")
        total = manager.get("total")
        msg += f"{idx}. *{team}* ({name}) — {total} pts\n"

    await update.message.reply_markdown(msg)