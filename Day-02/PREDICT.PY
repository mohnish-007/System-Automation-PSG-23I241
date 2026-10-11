
import joblib
import pandas as pd

model = joblib.load("Day-02/machine_model.pkl")

print("Enter the machine sensor readings:")

temperature = float(input("Temperature: "))
pressure = float(input("Pressure: "))
vibration = float(input("Vibration: "))
rpm = float(input("RPM: "))
current = float(input("Current: "))

sensor_reading = pd.DataFrame([{
    "temperature": temperature,
    "pressure": pressure,
    "vibration": vibration,
    "rpm": rpm,
    "current": current
}])

prediction = model.predict(sensor_reading)[0]

print("\nPredicted Machine State:", prediction)

if prediction == "Failure":
    print("Recommended Action: STOP MACHINE")
elif prediction == "Warning":
    print("Recommended Action: CHECK MACHINE")
else:
    print("Recommended Action: CONTINUE NORMAL OPERATION")
