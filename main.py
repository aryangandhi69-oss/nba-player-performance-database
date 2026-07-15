import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print("Connected to:", result.fetchone())

player_dict = players.find_players_by_full_name("LeBron James")
player_id = player_dict[0]['id']
print("Found player ID:", player_id)

gamelog = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24")
df = gamelog.get_data_frames()[0]
print(df[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST']].head())