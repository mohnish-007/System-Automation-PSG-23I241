import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report

data = pd.read_csv("Day-02/data/sensor_history.csv")

features = [
    "temperature", "pressure", "vibration",
    "rpm", "current"
]

X = data[features]
y = data["state"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = DecisionTreeClassifier(random_state=42)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("Model accuracy:", accuracy_score(y_test, predictions) * 100, "%")
print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))

Path("Day-02").mkdir(exist_ok=True)
joblib.dump(model, "Day-02/machine_model.pkl")

print("\nTrained model saved successfully!")
