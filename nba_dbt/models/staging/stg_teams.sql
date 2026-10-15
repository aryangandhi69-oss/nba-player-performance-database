select
    team_id,
    team_name,
    abbreviation
from {{ source('nba', 'teams') }}