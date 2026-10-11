
import csv
import random
from pathlib import Path

Path("Day-02/data").mkdir(parents=True, exist_ok=True)

with open("Day-02/data/sensor_history.csv", "w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        "temperature", "pressure", "vibration",
        "rpm", "current", "state"
    ])

    for _ in range(1000):
        temperature = random.randint(50, 95)
        pressure = random.randint(20, 100)
        vibration = round(random.uniform(0.1, 5.0), 2)
        rpm = random.randint(1180, 1600)
        current = round(random.uniform(5, 20), 2)

        if temperature > 90 or current > 18:
            state = "Failure"
        elif (
            temperature > 80
            or pressure > 35
            or pressure < 25
            or vibration > 4.0
        ):
            state = "Warning"
        else:
            state = "Normal"

        writer.writerow([
            temperature, pressure, vibration,
            rpm, current, state
        ])

print("1000 training records generated successfully!")
