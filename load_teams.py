import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from nba_api.stats.static import teams

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

nba_teams = teams.get_teams()

insert_statement = text("""
    INSERT INTO teams (team_id, team_name, abbreviation, conference, division)
    VALUES (:team_id, :team_name, :abbreviation, :conference, :division)
    ON CONFLICT (team_id) DO NOTHING;
""")

with engine.connect() as conn:
    for team in nba_teams:
        conn.execute(insert_statement, {
            "team_id": team["id"],
            "team_name": team["full_name"],
            "abbreviation": team["abbreviation"],
            "conference": None,
            "division": None
        })
    conn.commit()

print(f"Loaded {len(nba_teams)} teams into the database.")