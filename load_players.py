import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.static import teams

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

nba_teams = teams.get_teams()

insert_statement = text("""
    INSERT INTO players (player_id, player_name, team_id, position, height, weight, birth_date)
    VALUES (:player_id, :player_name, :team_id, :position, :height, :weight, :birth_date)
    ON CONFLICT (player_id) DO NOTHING;
""")

total_loaded = 0

with engine.connect() as conn:
    for team in nba_teams:
        print(f"Pulling roster for {team['full_name']}...")
        roster = commonteamroster.CommonTeamRoster(team_id=team["id"], season="2023-24")
        df = roster.get_data_frames()[0]

        for _, row in df.iterrows():
            conn.execute(insert_statement, {
                "player_id": row["PLAYER_ID"],
                "player_name": row["PLAYER"],
                "team_id": team["id"],
                "position": row["POSITION"],
                "height": row["HEIGHT"],
                "weight": row["WEIGHT"],
                "birth_date": row["BIRTH_DATE"] if row["BIRTH_DATE"] else None
            })
            total_loaded += 1

        conn.commit()
        time.sleep(0.6)  # be polite to the API, avoid rate limiting

print(f"Loaded {total_loaded} players into the database.")