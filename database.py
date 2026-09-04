import sqlite3

def init_db():
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    # Table to track every single gameweek's winner and the 50 Birr prize
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gameweek_history (
            gameweek INTEGER PRIMARY KEY,
            manager_name TEXT,
            team_name TEXT,
            points INTEGER,
            prize_amount INTEGER DEFAULT 50
        )
    ''')
    conn.commit()
    conn.close()

def get_wallet_standings():
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT manager_name, team_name, COUNT(gameweek) as wins, SUM(prize_amount) as total_cash 
        FROM gameweek_history 
        GROUP BY manager_name 
        ORDER BY total_cash DESC
    ''')
    data = cursor.fetchall()
    conn.close()
    return data