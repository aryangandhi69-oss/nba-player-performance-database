# NBA Player Performance Database & Analytics

I ahve made an SQL and Python pipeline that pulls real NBA game and player data from 2023-24 season, loads it into a relational Postgres database, and answers performance analytics questions relevant to sports operations and prop betting analytics, including hot/cold form detection, home/away splits, and rest/fatigue effects.

The main purpose fo this model was to build a self-directed project to help me develop a hands-on SQL model and work on my data pipeline skills.

## Why this project

I have a background in sports analytics but limited professional experience with SQL and Python, and database design. Rather than just take a course in isolation, I built this project to learn SQL directly against a real dataset, while producing something that reflects the kind of queries a team's analytics department or a sports betting company would actually run.

## Tech stack

- **Python** — data extraction via `nba_api`, pipeline orchestration
- **PostgreSQL (hosted on Supabase)** — relational data storage
- **SQLAlchemy** — database connection and query execution
- **SQL** — joins, aggregations, window functions, CTEs

## Data

Pulled directly from the NBA's official stats API (`nba_api`) for the 2023-24 season:
- 1,381 games (including preseason)
- 532 players
- 30,003 individual player game stat lines
- 2,762 team game stat lines

## Database schema

Six normalized tables:

- **teams** — team metadata
- **players** — player metadata, linked to current team
- **games** — game results, home/away teams, scores
- **player_game_stats** — box score stats per player per game
- **team_game_stats** — box score stats per team per game
- **player_season_averages** — reserved for aggregated season summaries

Foreign keys connect players and games to teams, and stats tables to both players and games, so queries can join across the full dataset.

## Pipeline

1. `create_tables.py` — creates the schema in Postgres
2. `load_teams.py` — loads all 30 NBA teams
3. `load_players.py` — loads team rosters for the season
4. `load_games_and_stats.py` — pulls every game and its full box score, loads games, player stats, and team stats. Handles missing/DNP players, minute-string conversion, and per-game transaction isolation so a single bad row can't fail the whole load.
5. `run_query.py` — a reusable runner that executes any saved `.sql` file against the database

## Flagship queries

Each query below answers a specific, real analytics question rather than being a generic demonstration of syntax.

### 1. Hot/Cold Player Detection (`sql/hot_cold_players.sql`)
**Question:** Which players are performing above or below their season norm right now?
Uses a window function to calculate each player's rolling 10-game scoring average, compared against their season average via a CTE. Useful for identifying players trending into or out of form, relevant to prop betting value and roster decisions.

### 2. Home/Away Performance Splits (`sql/home_away_splits.sql`)
**Question:** Do players score meaningfully more at home than on the road?
Uses conditional aggregation (`CASE` inside `AVG`) to split scoring averages by home and away games for each player.
**Known limitation:** this query joins on each player's *current* team, so results for players traded mid-season (e.g. players who changed teams during 2023-24) are less reliable, since some of their games are attributed to the wrong side of the split. This is called out rather than hidden, since it's a real constraint of the underlying data.

### 3. Rest Days and Fatigue Effect (`sql/rest_days_effect.sql`)
**Question:** How much does a player's scoring change on a back-to-back versus with normal rest?
Uses `LAG()` to calculate days of rest between consecutive games per player, then compares scoring averages on zero rest days versus one or more days of rest. This mirrors one of the most common factors real sportsbooks use to adjust player prop lines.

## Prediction model

A logistic regression classifier predicting whether a player will exceed their own rolling 10-game scoring average in their next game.

**Why this target instead of real sportsbook prop lines:** historical prop odds aren't freely available, so I used each player's own rolling average as a self-referenced baseline. This mirrors the actual logic behind how prop lines are set, recent player form, while being honest about the data actually available for this project.

**Features used:**
- Rolling 10-game scoring average (calculated using only prior games, no data leakage)
- Season average to date (also using only prior games)
- Home or away game
- Days of rest since last game
- Back-to-back indicator
- Difference between recent form and season average ("hot/cold" signal)

**Train/test split:** chronological, not random. Trained on the first 80% of the season by date, tested on the final 20%, so the model is only ever evaluated on games that happened after everything it was trained on. This avoids the model implicitly "seeing the future," a common mistake in sports prediction projects.

**Results:**
- Accuracy: 56.3%
- AUC: 0.559

**Honest interpretation:** this is a modest but real edge over random guessing (AUC 0.50). Predicting whether a player exceeds their own recent average is a genuinely difficult problem, since an average is by definition close to a 50/50 split point. Professional sports betting models achieve their edge using data this project doesn't have access to, injury reports, defensive matchup data, player tracking, lineup news. A single-digit AUC improvement using only box score history is a realistic, defensible result, not a shortcoming to hide.

One notable pattern: the model is more confident predicting "under" than "over" (59% precision on under vs. 50% on over), which lines up with the target distribution itself (54.7% of games are unders). The strongest feature, `hot_cold_diff`, has a negative coefficient, meaning that when a player is running hot relative to their season average, the model leans toward predicting a cooldown next game, a sensible regression-to-the-mean signal the model picked up without being told to look for it.

**Full results saved in `model_results.txt`.**

## What I'd build next

- Extend `player_season_averages` into a materialized rollup, refreshed after each data load
- Add opponent defensive rating as a feature to contextualize scoring output
- Build a simple classifier using the rolling average logic here as input features, predicting whether a player exceeds their own recent scoring average in their next game

## Notes on data limitations

- Player-to-team mapping reflects each player's roster status as of the data pull, not a full trade history, which affects the accuracy of home/away splits for traded players specifically.
- Game count (1,381) exceeds the standard 82-game schedule per team because `LeagueGameFinder` includes preseason games in this date range.