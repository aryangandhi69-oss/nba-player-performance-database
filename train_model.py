import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score, confusion_matrix, classification_report

df = pd.read_csv("model_ready_data.csv")
df["game_date"] = pd.to_datetime(df["game_date"])

# Split by date, not randomly. Train on the first 80% of the season chronologically,
# test on the final 20%. This mimics how the model would actually be used,
# predicting future games using only past data.
cutoff_date = df["game_date"].quantile(0.8)
train_df = df[df["game_date"] <= cutoff_date]
test_df = df[df["game_date"] > cutoff_date]

print(f"Train set: {len(train_df)} rows, up to {cutoff_date.date()}")
print(f"Test set: {len(test_df)} rows, after {cutoff_date.date()}")

features = ["rolling_10_avg", "season_avg_so_far", "is_home", "days_rest", "is_back_to_back", "hot_cold_diff"]

X_train = train_df[features]
y_train = train_df["target_over"]
X_test = test_df[features]
y_test = test_df["target_over"]

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

print("\n--- Results ---")
print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
print(f"AUC: {roc_auc_score(y_test, y_pred_proba):.3f}")
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nFeature importance (coefficients):")
for feat, coef in zip(features, model.coef_[0]):
    print(f"  {feat}: {coef:.4f}")

with open("model_results.txt", "w") as f:
    f.write(f"Train set: {len(train_df)} rows, up to {cutoff_date.date()}\n")
    f.write(f"Test set: {len(test_df)} rows, after {cutoff_date.date()}\n\n")
    f.write(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}\n")
    f.write(f"AUC: {roc_auc_score(y_test, y_pred_proba):.3f}\n\n")
    f.write("Classification Report:\n")
    f.write(classification_report(y_test, y_pred))
    f.write("\nFeature importance (coefficients):\n")
    for feat, coef in zip(features, model.coef_[0]):
        f.write(f"  {feat}: {coef:.4f}\n")

print("\nSaved results to model_results.txt")

import joblib

joblib.dump(model, "trained_model.pkl")
print("Saved trained model to trained_model.pkl")