# System-Automation-PSG-23I241

Coursework submissions for 23IF02 System Automation.

## Repository Contents

- **`Day-01/`**: Rule engine implementation with priority-based decision logic.
- **`Day-02/`**: Synthetic sensor data generation and machine learning model for predictive maintenance.
- **`Bonus-Challenge/`**: Robotic Arm Joint Health Monitoring System
  - Monitors joint torque, temperature, and vibration across shoulder, elbow, and wrist joints.
  - Implements deterministic immediate safety stop (Requirement 1).
  - Trains ML wear prediction model on historical joint failure data (Requirement 2).
  - Parses unstructured technician logs into arm risk signals (Requirement 3).
  - Defends against spoofed torque readings using physical cross-checks (Requirement 4).
  - Fuses signals into one final decision per arm: `SAFE`, `MONITOR`, `SCHEDULE_MAINTENANCE`, `EMERGENCY_STOP` (Requirement 5).
  - Documentation and written report in [`Bonus-Challenge/README.md`](Bonus-Challenge/README.md).