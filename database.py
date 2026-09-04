import sqlite3

def init_db():
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    # Tracks who won each gameweek and how big the pot was
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gameweek_winners (
            gameweek INTEGER PRIMARY KEY,
            manager_name TEXT,
            team_name TEXT,
            points INTEGER,
            pot_amount INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_gameweek_winner(gameweek, manager_name, team_name, points, pot_amount):
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO gameweek_winners (gameweek, manager_name, team_name, points, pot_amount)
        VALUES (?, ?, ?, ?, ?)
    ''', (gameweek, manager_name, team_name, points, pot_amount))
    conn.commit()
    conn.close()

def get_winner_counts():
    """Returns a list of tuples like (manager_name, total_wins) ordered by most wins."""
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT manager_name, COUNT(*) as wins 
        FROM gameweek_winners 
        GROUP BY manager_name 
        ORDER BY wins DESC
    ''')
    counts = cursor.fetchall()
    conn.close()
    return counts

def get_net_financial_standings(all_managers, entry_fee=50):
    """
    Calculates net balance for every manager across all recorded gameweeks.
    Each gameweek: Everyone pays `entry_fee`, and the winner takes the entire `pot_amount`.
    """
    conn = sqlite3.connect("fpl_bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT gameweek, manager_name, pot_amount FROM gameweek_winners')
    winners = cursor.fetchall()
    conn.close()

    # Initialize all managers with 0 balance
    ledger = {manager: 0 for manager in all_managers}

    for gw, winner_name, pot in winners:
        # Deduct entry fee from everyone who participated/is in the ledger
        for manager in ledger:
            ledger[manager] -= entry_fee
        
        # Add the full pot back to the gameweek winner
        if winner_name in ledger:
            ledger[winner_name] += pot
        else:
            # Handle edge case if winner name format differs slightly
            ledger[winner_name] = pot - entry_fee

    return ledger