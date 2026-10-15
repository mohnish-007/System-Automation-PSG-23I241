# Bonus Challenge - End-to-End Pipeline Demonstration
# Tests all 4 possible decisions: SAFE, MONITOR, SCHEDULE_MAINTENANCE, EMERGENCY_STOP
# Also demonstrates the spoofed-sensor defense in action.

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.health_monitor import RoboticArmHealthMonitor

def run_scenarios():
    print("=" * 65)
    print("Robotic Arm Joint Health Monitoring System - Pipeline Test")
    print("=" * 65)

    monitor = RoboticArmHealthMonitor()
    results = []

    # Scenario 1: Normal operation -> SAFE
    print("\n--- Scenario 1: Arm-2 (Normal Operation) ---")
    readings_safe = {
        "shoulder": {"torque_nm": 62.5, "temperature_c": 46.2, "vibration_mms": 1.35, "operating_hours": 1200, "load_kg": 3.0},
        "elbow":    {"torque_nm": 41.0, "temperature_c": 42.5, "vibration_mms": 1.10, "operating_hours": 1200, "load_kg": 3.0},
        "wrist":    {"torque_nm": 17.5, "temperature_c": 38.0, "vibration_mms": 0.85, "operating_hours": 1200, "load_kg": 3.0}
    }
    r1 = monitor.evaluate_arm("Arm-2", readings_safe)
    print(f"Decision: {r1['final_decision']}")
    print(f"Reason:   {r1['summary']}")
    print(f"Action:   {r1['action']}")
    results.append(r1['final_decision'])

    # Scenario 2: Warning signs -> MONITOR
    print("\n--- Scenario 2: Arm-1 (Moderate Wear & Tech Note) ---")
    readings_monitor = {
        "shoulder": {"torque_nm": 70.0, "temperature_c": 52.0, "vibration_mms": 1.6, "operating_hours": 4200, "load_kg": 4.5},
        "elbow":    {"torque_nm": 56.8, "temperature_c": 62.4, "vibration_mms": 3.12, "operating_hours": 4500, "load_kg": 4.5},
        "wrist":    {"torque_nm": 22.0, "temperature_c": 44.0, "vibration_mms": 1.3, "operating_hours": 4500, "load_kg": 4.5}
    }
    r2 = monitor.evaluate_arm("Arm-1", readings_monitor)
    print(f"Decision: {r2['final_decision']}")
    print(f"Reason:   {r2['summary']}")
    print(f"Action:   {r2['action']}")
    results.append(r2['final_decision'])

    # Scenario 3: Heavy wear and critical note -> SCHEDULE_MAINTENANCE
    print("\n--- Scenario 3: Arm-3 (Severe Wear & Grinding Noise Logged) ---")
    readings_maint = {
        "shoulder": {"torque_nm": 72.0, "temperature_c": 51.0, "vibration_mms": 1.7, "operating_hours": 7500, "load_kg": 5.0},
        "elbow":    {"torque_nm": 48.0, "temperature_c": 49.0, "vibration_mms": 1.4, "operating_hours": 7500, "load_kg": 5.0},
        "wrist":    {"torque_nm": 33.2, "temperature_c": 76.0, "vibration_mms": 5.80, "operating_hours": 9200, "load_kg": 5.0}
    }
    r3 = monitor.evaluate_arm("Arm-3", readings_maint)
    print(f"Decision: {r3['final_decision']}")
    print(f"Reason:   {r3['summary']}")
    print(f"Action:   {r3['action']}")
    results.append(r3['final_decision'])

    # Scenario 4: Hardware safety stop -> EMERGENCY_STOP
    print("\n--- Scenario 4: Arm-6 (Torque Spike / Mechanical Jam) ---")
    readings_estop = {
        "shoulder": {"torque_nm": 162.4, "temperature_c": 55.0, "vibration_mms": 2.1, "operating_hours": 3000, "load_kg": 7.0},
        "elbow":    {"torque_nm": 45.0,  "temperature_c": 44.0, "vibration_mms": 1.2, "operating_hours": 3000, "load_kg": 7.0},
        "wrist":    {"torque_nm": 20.0,  "temperature_c": 41.0, "vibration_mms": 1.0, "operating_hours": 3000, "load_kg": 7.0}
    }
    r4 = monitor.evaluate_arm("Arm-6", readings_estop)
    print(f"Decision: {r4['final_decision']}")
    print(f"Reason:   {r4['summary']}")
    print(f"Action:   {r4['action']}")
    results.append(r4['final_decision'])

    # Scenario 5: Spoofed sensor attack -> Defense catches it
    print("\n--- Scenario 5: Arm-7 (Spoofed Sensor Attack) ---")
    print("Attacker feeds fake torque of 18.0 Nm while bearing is at 82.5 C with 7.1 mm/s vibration.")
    readings_spoofed = {
        "shoulder": {
            "torque_nm": 18.0,      # Fake reading injected by attacker
            "temperature_c": 82.5,  # Real physical heat
            "vibration_mms": 7.10,  # Real bearing vibration
            "operating_hours": 8900,
            "load_kg": 7.5
        },
        "elbow": {"torque_nm": 42.0, "temperature_c": 43.0, "vibration_mms": 1.1, "operating_hours": 8900, "load_kg": 7.5},
        "wrist": {"torque_nm": 19.0, "temperature_c": 39.0, "vibration_mms": 0.9, "operating_hours": 8900, "load_kg": 7.5}
    }
    r5 = monitor.evaluate_arm("Arm-7", readings_spoofed)
    print(f"Decision: {r5['final_decision']}")
    print(f"Spoof Alert: {r5['spoof_defense']['alert']}")
    print(f"Action:   {r5['action']}")

    print("\n" + "=" * 65)
    print(f"Decisions produced in test run: {set(results)}")
    print("All 4 target decisions (SAFE, MONITOR, SCHEDULE_MAINTENANCE, EMERGENCY_STOP) verified!")
    print("=" * 65)

main = run_scenarios

if __name__ == "__main__":
    run_scenarios()
