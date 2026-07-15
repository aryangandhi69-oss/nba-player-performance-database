import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    result = conn.execute(text("""
        WITH rolling_stats AS (
            SELECT p.player_id,
                   p.player_name,
                   g.game_date,
                   s.points,
                   AVG(s.points) OVER (
                       PARTITION BY s.player_id
                       ORDER BY g.game_date
                       ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                   ) AS rolling_10_avg,
                   AVG(s.points) OVER (
                       PARTITION BY s.player_id
                   ) AS season_avg
            FROM player_game_stats s
            JOIN players p ON p.player_id = s.player_id
            JOIN games g ON g.game_id = s.game_id
        )
        SELECT player_name,
               game_date,
               points,
               ROUND(rolling_10_avg, 1) AS rolling_10_avg,
               ROUND(season_avg, 1) AS season_avg,
               ROUND(rolling_10_avg - season_avg, 1) AS diff_from_season_avg
        FROM rolling_stats
        WHERE game_date = (SELECT MAX(game_date) FROM rolling_stats)
        ORDER BY diff_from_season_avg DESC
        LIMIT 10
    """))
    for row in result:
        print(row)