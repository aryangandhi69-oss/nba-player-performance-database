select
    player_id,
    player_name,
    team_id,
    position
from {{ source('nba', 'players') }}