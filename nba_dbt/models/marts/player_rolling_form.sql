with player_games as (
    select
        s.player_id,
        p.player_name,
        g.game_id,
        g.game_date,
        s.points
    from {{ ref('stg_player_game_stats') }} s
    join {{ ref('stg_players') }} p on p.player_id = s.player_id
    join {{ ref('stg_games') }} g on g.game_id = s.game_id
)

select
    player_id,
    player_name,
    game_id,
    game_date,
    points,
    round(avg(points) over (
        partition by player_id
        order by game_date
        rows between 9 preceding and current row
    ), 1) as rolling_10_avg,
    round(avg(points) over (
        partition by player_id
    ), 1) as season_avg
from player_games