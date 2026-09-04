import requests
from config import LEAGUE_ID

def get_league_entries():
    if not LEAGUE_ID:
        print("Error: LEAGUE_ID is missing in your config.py.")
        return

    url = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
    
    # FPL API requires a User-Agent header to prevent 403 blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch league. Status code: {response.status_code}")
        return

    data = response.json()
    league_name = data.get("league", {}).get("name", "League of Royalties")
    results = data.get("standings", {}).get("results", [])
    
    print(f"\n--- {league_name} ---")
    print(f"Total Managers: {len(results)}\n")
    print(f"{'ENTRY ID':<10} | {'MANAGER NAME':<20} | {'TEAM NAME'}")
    print("-" * 55)
    
    for manager in results:
        entry_id = manager.get("entry")
        player_name = manager.get("player_name")
        team_name = manager.get("entry_name")
        print(f"{entry_id:<10} | {player_name:<20} | {team_name}")
        
    print("-" * 55)
    print("\nCopy these Entry IDs into your MANAGER_HANDLES dictionary in config.py!\n")

if __name__ == "__main__":
    get_league_entries()