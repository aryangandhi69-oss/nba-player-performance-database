select
    stat_id,
    game_id,
    player_id,
    minutes_played,
    points,
    rebounds,
    assists,
    steals,
    blocks,
    turnovers,
    plus_minus
from {{ source('nba', 'player_game_stats') }}