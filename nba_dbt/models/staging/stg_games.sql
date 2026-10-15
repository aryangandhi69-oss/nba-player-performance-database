select
    game_id,
    game_date,
    season,
    home_team_id,
    away_team_id,
    home_score,
    away_score
from {{ source('nba', 'games') }}