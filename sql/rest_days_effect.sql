-- Flagship Query 3: Rest Days and Performance
-- Business question: How much does a player's scoring change when playing
-- on a back-to-back (zero days rest) versus with normal rest? This is one
-- of the most commonly used factors in real sportsbook line adjustments.

WITH games_with_rest AS (
    SELECT p.player_id,
           p.player_name,
           g.game_date,
           s.points,
           g.game_date - LAG(g.game_date) OVER (
               PARTITION BY s.player_id
               ORDER BY g.game_date
           ) AS days_since_last_game
    FROM player_game_stats s
    JOIN players p ON p.player_id = s.player_id
    JOIN games g ON g.game_id = s.game_id
)
SELECT player_name,
       COUNT(*) FILTER (WHERE days_since_last_game = 1) AS back_to_back_games,
       ROUND(AVG(points) FILTER (WHERE days_since_last_game = 1), 1) AS avg_points_back_to_back,
       ROUND(AVG(points) FILTER (WHERE days_since_last_game > 1), 1) AS avg_points_with_rest
FROM games_with_rest
GROUP BY player_name
HAVING COUNT(*) FILTER (WHERE days_since_last_game = 1) >= 10
ORDER BY (AVG(points) FILTER (WHERE days_since_last_game = 1) -
          AVG(points) FILTER (WHERE days_since_last_game > 1)) ASC
LIMIT 10;