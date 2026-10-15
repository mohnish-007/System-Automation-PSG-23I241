# Bonus Challenge — Robotic Arm Joint Health Monitoring System

**Course:** 23IF02 System Automation  
**Student:** Mohnish ([mohnish-007](https://github.com/mohnish-007))  

---

## Overview

This project implements an automated health monitoring system for 6-axis robotic arms on an assembly line. It monitors sensor readings (**joint torque**, **temperature**, and **vibration**) across the three primary joints (**shoulder**, **elbow**, and **wrist**), and also integrates unstructured technician inspection logs.

The pipeline performs five key tasks:
1. **Immediate Safety Stop**: A deterministic rule check that triggers an emergency stop immediately if any joint crosses a hard physical limit (runs with zero delay, no ML model required).
2. **Predictive Wear Detection**: A machine learning model (Random Forest) trained on historical failure data to detect joint degradation early.
3. **Maintenance Notes Signal**: An NLP text analyzer that scans technician notes, ignores irrelevant tasks (cleaning, lunch, etc.), and extracts wear warnings.
4. **Spoofed-Sensor Defense**: A physics and consistency check to catch fake or replayed torque readings.
5. **Final Decision Per Arm**: Combines all signals into one of four decisions: `SAFE`, `MONITOR`, `SCHEDULE_MAINTENANCE`, or `EMERGENCY_STOP`.

---

## Written Explanation

### 1. Why I Chose These Safety Thresholds for the Immediate Stop

For an articulated 6-axis industrial robot, the immediate safety stop needs to protect both the mechanical hardware and factory workers. It must be deterministic and run before any ML inference so that safety is guaranteed even if the model fails.

* **Torque Limits (Joint Specific):**
  * **Shoulder (> 140.0 Nm):** The shoulder supports the entire arm structure and payload, with normal operating torque around 50–80 Nm and continuous rated capacity around 120 Nm. A reading above 140 Nm indicates a collision, extreme binding, or an unmanageable payload.
  * **Elbow (> 95.0 Nm):** Normal elbow torque is 35–55 Nm, with an 80 Nm rating. Anything over 95 Nm points to gearbox jamming or mechanical seizure.
  * **Wrist (> 45.0 Nm):** The wrist contains much smaller and more delicate gears. Rated capacity is typically ~35 Nm. Spikes over 45 Nm can shear gear teeth or damage the end effector flange.
* **Temperature Limit (> 85.0 °C across all joints):** Normal running temperature is around 40–55 °C. Above 85 °C, synthetic bearing grease starts thinning and breaking down, leading to rapid friction increase and possible motor burnout.
* **Vibration Limit (> 7.5 mm/s RMS):** Following the ISO 10816-3 industrial vibration standard (Zone D — dangerous vibration), vibration over 7.5 mm/s indicates severe mechanical issues like loose mounting bolts, bearing cage fracture, or severe rotor imbalance.

---

### 2. How the ML Prediction and Maintenance Log Combine into a Final Decision

The system uses a priority-based decision flow:

1. **Safety Interlock First (Priority 0):** If any sensor reading crosses the hard safety limits above, the system immediately outputs `EMERGENCY_STOP`. The ML model and log notes are bypassed.
2. **Spoofed-Sensor Defense (Priority 1):** If spoofing is detected while temperature or vibration are at dangerous levels, it immediately triggers `EMERGENCY_STOP`. If spoofing is detected under non-critical conditions, it outputs `SCHEDULE_MAINTENANCE` so technicians can inspect the sensor.
3. **Signal Combination Matrix (Priority 2):**
   * If the **ML model predicts `Failure`** OR technician notes have a **`CRITICAL` observation** (e.g., loud grinding noise, grease leak, backlash):  
     $$\rightarrow$$ **`SCHEDULE_MAINTENANCE`**
   * If the **ML model predicts `Warning`** OR technician notes mention a **`WARNING` issue** (e.g., joint feels warm, minor clicking sound, whining noise):  
     $$\rightarrow$$ **`MONITOR`**
   * If **sensors are within normal ranges**, the **ML model predicts `Normal`**, and **technician notes are clean**:  
     $$\rightarrow$$ **`SAFE`**

---

### 3. How the Spoofed-Sensor Defense Works

The defense module (`src/spoof_detector.py`) protects the system from situations where someone feeds fake or replayed torque readings to hide a failing joint.

#### How it works:
1. **Electro-Mechanical Physics Check:** In a mechanical joint, friction and mechanical strain naturally generate heat and vibration. If a joint reports high vibration ($\ge 4.5\text{ mm/s}$) and elevated temperature ($\ge 65\text{ }^\circ\text{C}$), the torque cannot physically be near zero or nominal. If the sensor reports a low torque (e.g., 18 Nm on a shoulder) during active thermal/vibrational distress, it flags a cross-correlation violation.
2. **Payload Consistency Check:** When the arm holds a heavy payload (e.g., 6–8 kg), static physics requires minimum holding torque on the shoulder. If the torque is reported near zero under load, it flags a payload mismatch.
3. **Frozen Reading / Replay Check:** Real sensors always have slight analog noise. If the exact same float value is sent repeatedly across consecutive samples (variance $< 0.005$), the system flags a frozen or replayed sensor attack.

#### What attacks it catches:
* **Faked Low-Torque Attacks:** When an attacker injects a normal-looking torque reading to prevent wear or collision alarms while the joint is overheating or vibrating.
* **Frozen / Replay Attacks:** Streaming static pre-recorded sensor data.
* **Payload Under-Reporting:** Suppressing load readings to bypass weight safety checks.

#### What it wouldn't catch:
* **Full Multi-Sensor Spoofing:** If an attacker compromises all sensors (torque, temperature, and vibration simultaneously) and calculates fake values that perfectly match the robot's physical model.
* **Tiny Biases / Drifts:** Very small offsets (within normal sensor noise margins) that don't violate physics bounds.

---

## Project Structure

```
Bonus-Challenge/
├── README.md                  # This report & documentation
├── generate_synthetic_data.py # Script to generate the historical sensor dataset
├── run_pipeline.py            # End-to-end pipeline showing all 4 outcomes + spoof attack
├── test_system.py             # 9 unit & integration tests
├── data/
│   ├── joint_wear_history.csv # 120 labeled historical joint records (Normal, Warning, Failure)
│   └── maintenance_notes.txt  # 9 realistic technician log entries (mix of relevant & irrelevant)
├── models/
│   └── joint_wear_model.pkl   # Trained Random Forest model
└── src/
    ├── __init__.py
    ├── safety_interlock.py    # Requirement 1: Immediate safety stop logic
    ├── predictive_wear.py     # Requirement 2: ML model training & wear prediction
    ├── text_log_analyzer.py   # Requirement 3: Plain text maintenance log parser
    ├── spoof_detector.py      # Requirement 4: Spoofed sensor defense engine
    └── health_monitor.py      # Requirement 5: Final decision fusion engine
```

---

## How to Run

### 1. Run Unit Tests
```bash
python test_system.py
```
Expected output:
```text
Ran 9 tests in 0.44s
OK
```

### 2. Run the Full Pipeline Demo
```bash
python run_pipeline.py
```
This runs 5 test scenarios demonstrating all 4 reachable decisions plus the spoofed-sensor defense:
* **Arm-2:** Normal operation $\rightarrow$ **`SAFE`**
* **Arm-1:** Warm elbow + clicking noise noted $\rightarrow$ **`MONITOR`**
* **Arm-3:** Wrist vibration + grinding noise logged $\rightarrow$ **`SCHEDULE_MAINTENANCE`**
* **Arm-6:** Torque spike to 162.4 Nm $\rightarrow$ **`EMERGENCY_STOP`**
* **Arm-7:** Spoofed torque (18 Nm) masking 82.5 °C heat $\rightarrow$ **`EMERGENCY_STOP`** (Spoof Defended)
