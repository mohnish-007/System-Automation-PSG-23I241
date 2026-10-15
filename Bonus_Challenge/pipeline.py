import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from model import predict_wear, train

def check_safety(joint, torque, temp, vib):
    limits = {"shoulder": 140.0, "elbow": 95.0, "wrist": 45.0}
    if torque > limits.get(joint, 100.0):
        return True, f"torque {torque} Nm exceeds limit {limits.get(joint, 100.0)} Nm"
    if temp > 85.0:
        return True, f"temperature {temp} C exceeds limit 85.0 C"
    if vib > 7.5:
        return True, f"vibration {vib} mm/s exceeds limit 7.5 mm/s"
    return False, None

def check_spoof(joint, torque, temp, vib):
    min_t = {"shoulder": 50.0, "elbow": 35.0, "wrist": 15.0}.get(joint, 30.0)
    if temp >= 65.0 and vib >= 4.5 and torque < min_t:
        return True, f"low torque ({torque} Nm) reported despite high temp ({temp} C) and vib ({vib} mm/s)"
    return False, None

def check_logs(arm_id):
    if not os.path.exists("Bonus_Challenge/logs.txt"):
        return "NONE", ""
    with open("Bonus_Challenge/logs.txt") as f:
        matches = [line.strip() for line in f if arm_id.lower() in line.lower()]
    if not matches:
        return "NONE", ""
    text = " ".join(matches).lower()
    if any(k in text for k in ["grinding", "leak", "grease", "backlash", "urgent"]):
        return "CRITICAL", matches[-1]
    if any(k in text for k in ["warm", "clicking", "whining", "chatter"]):
        return "WARNING", matches[-1]
    return "NORMAL", matches[-1]

def evaluate_arm(arm_id, joints_data):
    for joint, d in joints_data.items():
        tripped, reason = check_safety(joint, d["torque"], d["temperature"], d["vibration"])
        if tripped:
            return "EMERGENCY_STOP", f"Safety interlock tripped on {joint}: {reason}"

    for joint, d in joints_data.items():
        spoofed, reason = check_spoof(joint, d["torque"], d["temperature"], d["vibration"])
        if spoofed:
            if d["temperature"] > 80.0 or d["vibration"] > 7.0:
                return "EMERGENCY_STOP", f"Spoofed sensor masking severe danger on {joint}: {reason}"
            return "SCHEDULE_MAINTENANCE", f"Spoofed sensor detected on {joint}: {reason}"

    states = []
    for joint, d in joints_data.items():
        st = predict_wear(joint, d["torque"], d["temperature"], d["vibration"], d.get("hours", 1500))
        states.append(st)

    worst_model = "Normal"
    if "Failure" in states:
        worst_model = "Failure"
    elif "Warning" in states:
        worst_model = "Warning"

    log_level, note = check_logs(arm_id)

    if worst_model == "Failure" or log_level == "CRITICAL":
        return "SCHEDULE_MAINTENANCE", f"Model={worst_model}, Log={log_level}"
    if worst_model == "Warning" or log_level == "WARNING":
        return "MONITOR", f"Model={worst_model}, Log={log_level}"
    return "SAFE", f"Model={worst_model}, Log={log_level}"

def main():
    if not os.path.exists("Bonus_Challenge/model.pkl"):
        train()

    test_cases = [
        ("Arm-2", "Normal run", {
            "shoulder": {"torque": 62.0, "temperature": 46.0, "vibration": 1.3, "hours": 1000},
            "elbow":    {"torque": 41.0, "temperature": 42.0, "vibration": 1.1, "hours": 1000},
            "wrist":    {"torque": 17.0, "temperature": 38.0, "vibration": 0.8, "hours": 1000}
        }),
        ("Arm-1", "Warning signs", {
            "shoulder": {"torque": 68.0, "temperature": 50.0, "vibration": 1.5, "hours": 4200},
            "elbow":    {"torque": 56.0, "temperature": 62.0, "vibration": 3.1, "hours": 4500},
            "wrist":    {"torque": 21.0, "temperature": 43.0, "vibration": 1.2, "hours": 4500}
        }),
        ("Arm-3", "Severe wear", {
            "shoulder": {"torque": 72.0, "temperature": 51.0, "vibration": 1.7, "hours": 7500},
            "elbow":    {"torque": 48.0, "temperature": 49.0, "vibration": 1.4, "hours": 7500},
            "wrist":    {"torque": 33.0, "temperature": 75.0, "vibration": 5.8, "hours": 9200}
        }),
        ("Arm-6", "Collision / Jam", {
            "shoulder": {"torque": 158.0, "temperature": 52.0, "vibration": 2.0, "hours": 2000},
            "elbow":    {"torque": 42.0,  "temperature": 44.0, "vibration": 1.1, "hours": 2000},
            "wrist":    {"torque": 18.0,  "temperature": 39.0, "vibration": 0.9, "hours": 2000}
        }),
        ("Arm-7", "Spoofed torque attack", {
            "shoulder": {"torque": 18.0, "temperature": 82.0, "vibration": 7.2, "hours": 8500},
            "elbow":    {"torque": 42.0, "temperature": 43.0, "vibration": 1.1, "hours": 8500},
            "wrist":    {"torque": 19.0, "temperature": 39.0, "vibration": 0.9, "hours": 8500}
        })
    ]

    print("Running pipeline checks:")
    for arm_id, desc, data in test_cases:
        decision, reason = evaluate_arm(arm_id, data)
        print(f"[{arm_id}] ({desc}) -> Decision: {decision} | Reason: {reason}")

if __name__ == "__main__":
    main()
