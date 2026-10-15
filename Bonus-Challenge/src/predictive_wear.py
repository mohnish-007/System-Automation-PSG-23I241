import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

MODEL_FILE = os.path.join(os.path.dirname(__file__), "..", "models", "joint_wear_model.pkl")
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "joint_wear_history.csv")

FEATURE_COLS = [
    "joint_shoulder", "joint_elbow", "joint_wrist",
    "torque_nm", "temperature_c", "vibration_mms",
    "operating_hours", "load_kg"
]

def prepare_features(df):
    feats = pd.DataFrame(index=df.index)
    joint_lower = df["joint"].str.lower()
    feats["joint_shoulder"] = (joint_lower == "shoulder").astype(int)
    feats["joint_elbow"] = (joint_lower == "elbow").astype(int)
    feats["joint_wrist"] = (joint_lower == "wrist").astype(int)

    for col in ["torque_nm", "temperature_c", "vibration_mms", "operating_hours", "load_kg"]:
        feats[col] = df[col].astype(float)

    return feats[FEATURE_COLS]

def train_model(data_path=DATA_FILE, model_path=MODEL_FILE):
    data = pd.read_csv(data_path)
    X = prepare_features(data)
    y = data["state"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump({"model": clf, "features": FEATURE_COLS}, model_path)

    print(f"Model trained. Accuracy: {acc * 100:.2f}%")
    return clf

class JointWearPredictor:
    def __init__(self, model_path=None):
        self.model_path = model_path or MODEL_FILE
        if not os.path.exists(self.model_path):
            self.model = train_model(model_path=self.model_path)
        else:
            artifact = joblib.load(self.model_path)
            self.model = artifact["model"]

    def predict_joint(self, joint_name, reading):
        row = {
            "joint": joint_name.lower(),
            "torque_nm": reading.get("torque_nm", 50.0),
            "temperature_c": reading.get("temperature_c", 45.0),
            "vibration_mms": reading.get("vibration_mms", 1.2),
            "operating_hours": reading.get("operating_hours", 2000),
            "load_kg": reading.get("load_kg", 3.0),
        }
        df_row = pd.DataFrame([row])
        X = prepare_features(df_row)

        pred_state = self.model.predict(X)[0]
        probs = self.model.predict_proba(X)[0]
        classes = list(self.model.classes_)
        prob_dict = dict(zip(classes, [float(p) for p in probs]))

        p_warn = prob_dict.get("Warning", 0.0)
        p_fail = prob_dict.get("Failure", 0.0)
        wear_score = round(p_warn * 0.5 + p_fail * 1.0, 3)

        return {
            "joint": joint_name.lower(),
            "predicted_state": pred_state,
            "confidence": round(float(np.max(probs)), 3),
            "probabilities": prob_dict,
            "wear_score": wear_score
        }

    def predict_arm(self, arm_readings):
        results = {}
        worst_score = 0.0
        worst_state = "Normal"
        rank = {"Normal": 0, "Warning": 1, "Failure": 2}

        for joint_name, reading in arm_readings.items():
            res = self.predict_joint(joint_name, reading)
            results[joint_name] = res
            if rank.get(res["predicted_state"], 0) > rank.get(worst_state, 0):
                worst_state = res["predicted_state"]
            if res["wear_score"] > worst_score:
                worst_score = res["wear_score"]

        return {
            "aggregate_state": worst_state,
            "max_wear_score": worst_score,
            "joint_details": results
        }

if __name__ == "__main__":
    train_model()
