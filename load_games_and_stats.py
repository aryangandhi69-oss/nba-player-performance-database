import os
import time
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2

def convert_minutes(min_str):
    """Converts NBA API minute strings like '16:19' into decimal minutes like 16.32"""
    if min_str is None or min_str == "":
        return None
    if ":" not in str(min_str):
        return float(min_str)
    minutes, seconds = str(min_str).split(":")
    return round(int(minutes) + int(seconds) / 60, 2)

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

SEASON = "2023-24"

print("Pulling game list for the season...")
gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable=SEASON, league_id_nullable="00")
games_df = gamefinder.get_data_frames()[0]

unique_game_ids = games_df["GAME_ID"].unique()
print(f"Found {len(unique_game_ids)} unique games.")

insert_game = text("""
    INSERT INTO games (game_id, game_date, season, home_team_id, away_team_id, home_score, away_score)
    VALUES (:game_id, :game_date, :season, :home_team_id, :away_team_id, :home_score, :away_score)
    ON CONFLICT (game_id) DO NOTHING;
""")

insert_unknown_player = text("""
    INSERT INTO players (player_id, player_name, team_id, position, height, weight, birth_date)
    VALUES (:player_id, :player_name, :team_id, NULL, NULL, NULL, NULL)
    ON CONFLICT (player_id) DO NOTHING;
""")

insert_player_stat = text("""
    INSERT INTO player_game_stats (game_id, player_id, minutes_played, points, rebounds, assists, steals, blocks, turnovers, plus_minus)
    VALUES (:game_id, :player_id, :minutes_played, :points, :rebounds, :assists, :steals, :blocks, :turnovers, :plus_minus);
""")

insert_team_stat = text("""
    INSERT INTO team_game_stats (game_id, team_id, points, rebounds, assists, turnovers, field_goal_pct, three_point_pct)
    VALUES (:game_id, :team_id, :points, :rebounds, :assists, :turnovers, :field_goal_pct, :three_point_pct);
""")

games_loaded = 0
errors = 0

for game_id in unique_game_ids:
    # A fresh connection and transaction for every single game.
    # If this game fails, it cannot affect any other game.
    try:
        with engine.begin() as conn:
            game_rows = games_df[games_df["GAME_ID"] == game_id]
            if len(game_rows) != 2:
                continue

            home_row = game_rows[game_rows["MATCHUP"].str.contains("vs.")].iloc[0]
            away_row = game_rows[game_rows["MATCHUP"].str.contains("@")].iloc[0]

            conn.execute(insert_game, {
                "game_id": game_id,
                "game_date": home_row["GAME_DATE"],
                "season": SEASON,
                "home_team_id": int(home_row["TEAM_ID"]),
                "away_team_id": int(away_row["TEAM_ID"]),
                "home_score": int(home_row["PTS"]),
                "away_score": int(away_row["PTS"])
            })

            boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            player_stats_df = boxscore.get_data_frames()[0]
            team_stats_df = boxscore.get_data_frames()[1]

            for _, p in player_stats_df.iterrows():
                if pd.isna(p["MIN"]):
                    continue

                # Make sure this player exists before inserting their stat line.
                # This handles traded players, two-way players, anyone missing
                # from our original roster pull.
                conn.execute(insert_unknown_player, {
                    "player_id": int(p["PLAYER_ID"]),
                    "player_name": p["PLAYER_NAME"],
                    "team_id": int(p["TEAM_ID"])
                })

                conn.execute(insert_player_stat, {
                    "game_id": game_id,
                    "player_id": int(p["PLAYER_ID"]),
                    "minutes_played": convert_minutes(p["MIN"]),
                    "points": p["PTS"] if p["PTS"] is not None else 0,
                    "rebounds": p["REB"] if p["REB"] is not None else 0,
                    "assists": p["AST"] if p["AST"] is not None else 0,
                    "steals": p["STL"] if p["STL"] is not None else 0,
                    "blocks": p["BLK"] if p["BLK"] is not None else 0,
                    "turnovers": p["TO"] if p["TO"] is not None else 0,
                    "plus_minus": p["PLUS_MINUS"] if p["PLUS_MINUS"] is not None else 0
                })

            for _, t in team_stats_df.iterrows():
                conn.execute(insert_team_stat, {
                    "game_id": game_id,
                    "team_id": int(t["TEAM_ID"]),
                    "points": t["PTS"],
                    "rebounds": t["REB"],
                    "assists": t["AST"],
                    "turnovers": t["TO"],
                    "field_goal_pct": t["FG_PCT"],
                    "three_point_pct": t["FG3_PCT"]
                })
            # engine.begin() automatically commits here if no exception was raised

        games_loaded += 1
        if games_loaded % 25 == 0:
            print(f"Loaded {games_loaded} games so far...")

    except Exception as e:
        errors += 1
        print(f"Error on game {game_id}: {type(e).__name__}: {e}")
        # No manual rollback needed, engine.begin() already rolled back
        # this specific transaction, and it never touched any other game.
        continue

    time.sleep(0.6)

print(f"Finished. Loaded {games_loaded} games. Errors: {errors}")