import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

st.set_page_config(page_title="NBA Player Performance Explorer", layout="centered")
st.title("NBA Player Performance Explorer")
st.caption("Live query against a PostgreSQL database of 2023-24 NBA season data")

# Get list of player names for the dropdown
@st.cache_data
def get_player_list():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT player_name FROM players ORDER BY player_name"))
        return [row[0] for row in result]

player_names = get_player_list()
selected_player = st.selectbox("Select a player", player_names, index=player_names.index("LeBron James") if "LeBron James" in player_names else 0)

if selected_player:
    query = text("""
        WITH player_games AS (
            SELECT p.player_name,
                   g.game_date,
                   s.points,
                   s.rebounds,
                   s.assists,
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
            WHERE p.player_name = :player_name
            ORDER BY g.game_date
        )
        SELECT * FROM player_games
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"player_name": selected_player})

    if df.empty:
        st.warning("No game data found for this player.")
    else:
        latest = df.iloc[-1]
        diff = latest["rolling_10_avg"] - latest["season_avg"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Season Avg PPG", f"{latest['season_avg']:.1f}")
        col2.metric("Last 10 Games Avg", f"{latest['rolling_10_avg']:.1f}", f"{diff:+.1f}")
        col3.metric("Games Played", len(df))

        if diff > 2:
            st.success(f"{selected_player} is running HOT, scoring {diff:.1f} points above their season average over the last 10 games.")
        elif diff < -2:
            st.error(f"{selected_player} is running COLD, scoring {abs(diff):.1f} points below their season average over the last 10 games.")
        else:
            st.info(f"{selected_player} is performing close to their season norm right now.")

        st.subheader("Points per game, full season")
        chart_df = df.set_index("game_date")[["points", "rolling_10_avg"]]
        chart_df.columns = ["Points", "10-Game Rolling Avg"]
        st.line_chart(chart_df)

        st.subheader("Game log")
        display_df = df[["game_date", "points", "rebounds", "assists"]].sort_values("game_date", ascending=False)
        display_df.columns = ["Date", "Points", "Rebounds", "Assists"]
        st.dataframe(display_df, hide_index=True, use_container_width=True)