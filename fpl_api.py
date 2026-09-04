import requests
from config import LEAGUE_ID

def fetch_standings():
    if not LEAGUE_ID:
        return None
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None