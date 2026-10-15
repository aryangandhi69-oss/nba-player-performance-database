with games_with_rest as (
    select
        s.player_id,
        p.player_name,
        g.game_date,
        s.points,
        g.game_date - lag(g.game_date) over (
            partition by s.player_id
            order by g.game_date
        ) as days_since_last_game
    from {{ ref('stg_player_game_stats') }} s
    join {{ ref('stg_players') }} p on p.player_id = s.player_id
    join {{ ref('stg_games') }} g on g.game_id = s.game_id
)

select
    player_id,
    player_name,
    count(*) filter (where days_since_last_game = 1) as back_to_back_games,
    round(avg(points) filter (where days_since_last_game = 1), 1) as avg_points_back_to_back,
    round(avg(points) filter (where days_since_last_game > 1), 1) as avg_points_with_rest
from games_with_rest
group by player_id, player_name
having count(*) filter (where days_since_last_game = 1) >= 10