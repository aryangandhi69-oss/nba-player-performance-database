-- Flagship Query 2: Home vs Away Performance Splits
-- Business question: Do players perform meaningfully better at home versus
-- on the road? Useful for adjusting prop lines and evaluating travel fatigue
-- effects on individual players.

SELECT p.player_name,
       COUNT(*) AS total_games,
       ROUND(AVG(CASE WHEN g.home_team_id = p.team_id THEN s.points END), 1) AS avg_points_home,
       ROUND(AVG(CASE WHEN g.away_team_id = p.team_id THEN s.points END), 1) AS avg_points_away,
       COUNT(*) FILTER (WHERE g.home_team_id = p.team_id) AS home_games,
       COUNT(*) FILTER (WHERE g.away_team_id = p.team_id) AS away_games
FROM player_game_stats s
JOIN players p ON p.player_id = s.player_id
JOIN games g ON g.game_id = s.game_id
GROUP BY p.player_name
HAVING COUNT(*) >= 50
ORDER BY (AVG(CASE WHEN g.home_team_id = p.team_id THEN s.points END) -
          AVG(CASE WHEN g.away_team_id = p.team_id THEN s.points END)) DESC
LIMIT 10;