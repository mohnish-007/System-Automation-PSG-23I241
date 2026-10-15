import random
import pandas as pd
import numpy as np

def generate():
    random.seed(42)
    np.random.seed(42)
    joints = ["shoulder", "elbow", "wrist"]
    base = {
        "shoulder": (65.0, 48.0, 1.4),
        "elbow": (42.0, 44.0, 1.2),
        "wrist": (18.0, 40.0, 0.9)
    }
    states = ["Normal"] * 45 + ["Warning"] * 25 + ["Failure"] * 20
    random.shuffle(states)

    rows = []
    for i, state in enumerate(states):
        j = random.choice(joints)
        t, temp, vib = base[j]
        if state == "Normal":
            row = [j, round(np.random.normal(t, 5), 2), round(np.random.normal(temp, 3), 2), round(np.random.normal(vib, 0.2), 2), random.randint(100, 3000), state]
        elif state == "Warning":
            row = [j, round(np.random.normal(t * 1.3, 6), 2), round(np.random.normal(temp + 15, 4), 2), round(np.random.normal(vib * 2.5, 0.4), 2), random.randint(3500, 7000), state]
        else:
            row = [j, round(np.random.normal(t * 1.8, 8), 2), round(np.random.normal(temp + 35, 5), 2), round(np.random.normal(vib * 4.5, 0.6), 2), random.randint(7500, 12000), state]
        rows.append(row)

    df = pd.DataFrame(rows, columns=["joint", "torque", "temperature", "vibration", "hours", "state"])
    df.to_csv("Bonus_Challenge/data.csv", index=False)
    print(f"Generated {len(df)} records in Bonus_Challenge/data.csv")

if __name__ == "__main__":
    generate()
