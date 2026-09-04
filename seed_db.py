import sqlite3

def seed_custom_financials():
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gameweek_winners (
            gameweek INTEGER PRIMARY KEY,
            manager_name TEXT,
            team_name TEXT,
            points INTEGER,
            pot_amount INTEGER
        )
    ''')

    # GW1 pot was 200 Birr (4 players * 50). GW2 pot was 300 Birr (6 players * 50).
    winners = [
        (1, "Yoda Belay", "Yoda's Team", 0, 200),
        (2, "Ab Best", "Pending Moderation", 0, 300)
    ]

    for gw, manager, team, pts, pot in winners:
        cursor.execute('''
            INSERT OR REPLACE INTO gameweek_winners (gameweek, manager_name, team_name, points, pot_amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (gw, manager, team, pts, pot))

    conn.commit()
    conn.close()
    print("Database seeded successfully with GW1 and GW2 winners!")

if __name__ == "__main__":
    seed_custom_financials()