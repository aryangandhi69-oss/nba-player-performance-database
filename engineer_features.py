import pandas as pd

df = pd.read_csv("raw_player_games.csv")
df["game_date"] = pd.to_datetime(df["game_date"])

# Sort properly, this is critical for rolling calculations to be correct
df = df.sort_values(["player_id", "game_date"]).reset_index(drop=True)

# Feature 1: Rolling 10-game average points, BEFORE the current game.
# We use shift(1) so the current game's own points never leak into its own feature,
# otherwise we'd be using the answer to predict itself.
df["rolling_10_avg"] = (
    df.groupby("player_id")["points"]
    .transform(lambda x: x.shift(1).rolling(window=10, min_periods=3).mean())
)

# Feature 2: Season average so far, also shifted to avoid leakage
df["season_avg_so_far"] = (
    df.groupby("player_id")["points"]
    .transform(lambda x: x.shift(1).expanding(min_periods=3).mean())
)

# Feature 3: Home or away for this game
df["is_home"] = (df["home_team_id"] == df["team_id"]).astype(int)

# Feature 4: Days of rest before this game
df["days_rest"] = df.groupby("player_id")["game_date"].diff().dt.days
df["is_back_to_back"] = (df["days_rest"] == 1).astype(int)

# Feature 5: Trend, is recent form above or below season norm
df["hot_cold_diff"] = df["rolling_10_avg"] - df["season_avg_so_far"]

# LABEL: did the player exceed their OWN rolling average in this game?
# This is what we're predicting: 1 if they went over their recent form, 0 if under.
df["target_over"] = (df["points"] > df["rolling_10_avg"]).astype(int)

# Drop rows where we don't have enough history yet to calculate rolling features
model_df = df.dropna(subset=["rolling_10_avg", "season_avg_so_far", "days_rest"]).copy()

print(f"Total rows before dropping incomplete history: {len(df)}")
print(f"Rows with enough history to use: {len(model_df)}")
print(f"Target distribution:\n{model_df['target_over'].value_counts(normalize=True)}")

model_df.to_csv("model_ready_data.csv", index=False)
print("Saved to model_ready_data.csv")