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
    for _ in range(200):
        temperature = round(random.uniform(52, 99), 1)
        pressure = round(random.uniform(3, 6), 2)
        vibration = round(random.uniform(2, 12), 1)
        rpm = round(random.uniform(1000, 1600), 0)
        current = round(random.uniform(5, 13), 1)
        if temperature >= 90 or vibration >= 10 or current >= 12:
            state = "Failure"
        elif temperature >= 75 or pressure >= 5.5 or vibration >= 7 or current >= 8:
            state = "Warning"
        else:
            state = "Normal"
        writer.writerow([
            temperature, pressure, vibration,
            rpm, current, state
        ])

