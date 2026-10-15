import os
import random
import pandas as pd
import numpy as np

def generate_joint_history_dataset(n_samples=120, random_seed=42):
    random.seed(random_seed)
    np.random.seed(random_seed)

    joints = ["shoulder", "elbow", "wrist"]
    specs = {
        "shoulder": {"torque": (65.0, 8.0), "temp": (48.0, 4.0), "vib": (1.4, 0.3)},
        "elbow":    {"torque": (42.0, 6.0), "temp": (44.0, 3.5), "vib": (1.2, 0.25)},
        "wrist":    {"torque": (18.0, 3.0), "temp": (40.0, 3.0), "vib": (0.9, 0.2)},
    }

    records = []
    states = ["Normal"] * int(n_samples * 0.50) + \
             ["Warning"] * int(n_samples * 0.30) + \
             ["Failure"] * (n_samples - int(n_samples * 0.50) - int(n_samples * 0.30))
    random.shuffle(states)

    for i, state in enumerate(states):
        arm_id = f"Arm-{(i % 8) + 1}"
        joint = random.choice(joints)
        t_mean, t_std = specs[joint]["torque"]
        temp_mean, temp_std = specs[joint]["temp"]
        v_mean, v_std = specs[joint]["vib"]

        if state == "Normal":
            torque = np.random.normal(t_mean, t_std)
            temp = np.random.normal(temp_mean, temp_std)
            vib = np.random.normal(v_mean, v_std)
            hours = random.randint(100, 3500)
            load_kg = round(random.uniform(1.0, 7.0), 1)
        elif state == "Warning":
            torque = np.random.normal(t_mean * 1.35, t_std * 1.2)
            temp = np.random.normal(temp_mean + 18.0, temp_std * 1.3)
            vib = np.random.normal(v_mean * 2.6, v_std * 1.4)
            hours = random.randint(4000, 8500)
            load_kg = round(random.uniform(3.0, 8.5), 1)
        else:
            torque = np.random.normal(t_mean * 1.85, t_std * 1.5)
            temp = np.random.normal(temp_mean + 36.0, temp_std * 1.8)
            vib = np.random.normal(v_mean * 4.8, v_std * 1.6)
            hours = random.randint(8000, 15000)
            load_kg = round(random.uniform(4.0, 10.0), 1)

        cycles = hours * random.randint(45, 60)
        torque = max(5.0, round(float(torque), 2))
        temp = max(20.0, round(float(temp), 2))
        vib = max(0.2, round(float(vib), 2))

        records.append({
            "record_id": f"REC-{i+1:04d}",
            "arm_id": arm_id,
            "joint": joint,
            "torque_nm": torque,
            "temperature_c": temp,
            "vibration_mms": vib,
            "operating_hours": hours,
            "cycle_count": cycles,
            "load_kg": load_kg,
            "state": state
        })

    return pd.DataFrame(records)

generate_data = generate_joint_history_dataset

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "joint_wear_history.csv")
    df = generate_joint_history_dataset(120)
    df.to_csv(out_file, index=False)
    print(f"Generated {len(df)} records at {out_file}")
