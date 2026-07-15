import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

create_teams = """
CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL,
    abbreviation TEXT,
    conference TEXT,
    division TEXT
);
"""

create_players = """
CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT NOT NULL,
    team_id INTEGER REFERENCES teams(team_id),
    position TEXT,
    height TEXT,
    weight INTEGER,
    birth_date DATE
);
"""

create_games = """
CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    game_date DATE NOT NULL,
    season TEXT,
    home_team_id INTEGER REFERENCES teams(team_id),
    away_team_id INTEGER REFERENCES teams(team_id),
    home_score INTEGER,
    away_score INTEGER
);
"""

create_player_game_stats = """
CREATE TABLE IF NOT EXISTS player_game_stats (
    stat_id SERIAL PRIMARY KEY,
    game_id TEXT REFERENCES games(game_id),
    player_id INTEGER REFERENCES players(player_id),
    minutes_played NUMERIC,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    plus_minus INTEGER
);
"""

create_team_game_stats = """
CREATE TABLE IF NOT EXISTS team_game_stats (
    stat_id SERIAL PRIMARY KEY,
    game_id TEXT REFERENCES games(game_id),
    team_id INTEGER REFERENCES teams(team_id),
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    turnovers INTEGER,
    field_goal_pct NUMERIC,
    three_point_pct NUMERIC
);
"""

create_player_season_averages = """
CREATE TABLE IF NOT EXISTS player_season_averages (
    season_id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season TEXT,
    games_played INTEGER,
    avg_points NUMERIC,
    avg_rebounds NUMERIC,
    avg_assists NUMERIC
);
"""

table_statements = [
    ("teams", create_teams),
    ("players", create_players),
    ("games", create_games),
    ("player_game_stats", create_player_game_stats),
    ("team_game_stats", create_team_game_stats),
    ("player_season_averages", create_player_season_averages),
]

with engine.connect() as conn:
    for table_name, statement in table_statements:
        conn.execute(text(statement))
        conn.commit()
        print(f"Created table: {table_name}")

print("All tables created successfully.")