from telegram.ext import ApplicationBuilder, CommandHandler
from config import TELEGRAM_TOKEN
from database import init_db
from handlers import start, live_standings, total_standings, final_standings, net_ledger, wins_standings
from scheduler import setup_scheduler

def main():
    init_db()
    setup_scheduler()
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live_standings))
    app.add_handler(CommandHandler("total", total_standings))
    app.add_handler(CommandHandler("final", final_standings))
    app.add_handler(CommandHandler("net", net_ledger))
    app.add_handler(CommandHandler("wins", wins_standings))

    print("Sir Royale is polling and ready for duty...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

