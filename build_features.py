import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

query = """
    SELECT p.player_id,
           p.player_name,
           g.game_id,
           g.game_date,
           g.home_team_id,
           g.away_team_id,
           p.team_id,
           s.points,
           s.minutes_played
    FROM player_game_stats s
    JOIN players p ON p.player_id = s.player_id
    JOIN games g ON g.game_id = s.game_id
    ORDER BY p.player_id, g.game_date
"""

with engine.connect() as conn:
    df = pd.read_sql(text(query), conn)

print(f"Pulled {len(df)} player-game rows.")
print(df.head())

df.to_csv("raw_player_games.csv", index=False)
print("Saved to raw_player_games.csv")