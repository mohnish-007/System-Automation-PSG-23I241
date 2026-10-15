import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

def train():
    df = pd.read_csv("Bonus_Challenge/data.csv")
    df = pd.get_dummies(df, columns=["joint"])
    for col in ["joint_shoulder", "joint_elbow", "joint_wrist"]:
        if col not in df.columns:
            df[col] = 0
    X = df[["torque", "temperature", "vibration", "hours", "joint_shoulder", "joint_elbow", "joint_wrist"]]
    y = df["state"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = DecisionTreeClassifier(max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    acc = accuracy_score(y_test, model.predict(X_test))
    joblib.dump({"model": model, "cols": X.columns.tolist()}, "Bonus_Challenge/model.pkl")
    print(f"Model trained. Accuracy: {acc * 100:.1f}%")
    return model

def predict_wear(joint, torque, temp, vib, hours):
    saved = joblib.load("Bonus_Challenge/model.pkl")
    m, cols = saved["model"], saved["cols"]
    df = pd.DataFrame([{
        "torque": torque, "temperature": temp, "vibration": vib, "hours": hours,
        "joint_shoulder": int(joint == "shoulder"),
        "joint_elbow": int(joint == "elbow"),
        "joint_wrist": int(joint == "wrist")
    }])[cols]
    return m.predict(df)[0]

if __name__ == "__main__":
    train()
