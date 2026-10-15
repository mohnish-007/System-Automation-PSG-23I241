# Requirement 4: Spoofed Sensor Defense
# Defends against spoofed torque readings that try to hide physical joint issues

import numpy as np

class SpoofedSensorDetector:
    def __init__(self, variance_threshold=0.005):
        self.variance_threshold = variance_threshold
        # Keep track of recent torque readings to detect frozen signals
        self.history = {}

    def _get_key(self, arm_id, joint):
        return f"{arm_id.lower()}_{joint.lower()}"

    def update_history(self, arm_id, joint, torque):
        key = self._get_key(arm_id, joint)
        if key not in self.history:
            self.history[key] = []
        self.history[key].append(torque)
        if len(self.history[key]) > 5:
            self.history[key].pop(0)

    def check_frozen(self, arm_id, joint):
        """Check if sensor readings are completely frozen (zero variance)."""
        key = self._get_key(arm_id, joint)
        readings = self.history.get(key, [])
        if len(readings) >= 4:
            var = float(np.var(readings))
            if var < self.variance_threshold:
                return True, f"FROZEN_SIGNAL: {joint.upper()} torque reading is identical across multiple samples (var={var:.5f}). Likely replay or frozen sensor."
        return False, None

    def check_physics_correlation(self, joint, torque, temp, vib):
        """
        Check if reported torque is consistent with temperature and vibration.
        If joint is overheating or vibrating heavily from friction, torque cannot be unrealistically low.
        """
        joint_key = joint.lower()
        min_expected_torque = {
            "shoulder": 50.0,
            "elbow": 35.0,
            "wrist": 15.0
        }.get(joint_key, 30.0)

        # High vibration and high temperature, but torque reported as very low
        if vib >= 4.5 and temp >= 65.0 and torque < min_expected_torque:
            return True, (
                f"SPOOF_DETECTED: {joint.upper()} has high vibration ({vib:.2f} mm/s) "
                f"and elevated temp ({temp:.1f} C), but reported torque is only {torque:.1f} Nm. "
                f"Fake low torque reading detected."
            )

        # Extreme temperature with almost zero torque
        if temp >= 75.0 and torque < (min_expected_torque * 0.75):
            return True, (
                f"SPOOF_DETECTED: {joint.upper()} temperature is high ({temp:.1f} C) "
                f"with unrealistically low torque ({torque:.1f} Nm)."
            )

        return False, None

    def check_payload_logic(self, joint, torque, load_kg):
        """Check if shoulder torque is reasonable for the given payload."""
        if joint.lower() == "shoulder" and load_kg >= 6.0 and torque < 25.0:
            return True, f"PAYLOAD_MISMATCH: Shoulder torque ({torque:.1f} Nm) is too low for a {load_kg:.1f} kg payload."
        return False, None

    def evaluate_reading(self, arm_id, joint, reading):
        torque = float(reading.get("torque_nm", 0.0))
        temp = float(reading.get("temperature_c", 25.0))
        vib = float(reading.get("vibration_mms", 1.0))
        load_kg = float(reading.get("load_kg", 0.0))

        self.update_history(arm_id, joint, torque)

        # 1. Physics correlation check
        is_spoofed, msg = self.check_physics_correlation(joint, torque, temp, vib)
        if is_spoofed:
            return {
                "is_spoofed": True,
                "attack_type": "CROSS_CORRELATION_VIOLATION",
                "message": msg,
                "unmasked_danger": temp > 80.0 or vib > 7.0
            }

        # 2. Payload check
        is_load_spoofed, load_msg = self.check_payload_logic(joint, torque, load_kg)
        if is_load_spoofed:
            return {
                "is_spoofed": True,
                "attack_type": "PAYLOAD_MISMATCH",
                "message": load_msg,
                "unmasked_danger": False
            }

        # 3. Frozen reading check
        is_frozen, frozen_msg = self.check_frozen(arm_id, joint)
        if is_frozen:
            return {
                "is_spoofed": True,
                "attack_type": "FROZEN_SIGNAL",
                "message": frozen_msg,
                "unmasked_danger": False
            }

        return {
            "is_spoofed": False,
            "attack_type": "NONE",
            "message": "Readings look normal and consistent.",
            "unmasked_danger": False
        }

    def evaluate_arm(self, arm_id, arm_readings):
        """Check all joints for signs of sensor spoofing."""
        spoofed_joints = []
        alert_msg = None
        has_danger = False

        for joint, reading in arm_readings.items():
            res = self.evaluate_reading(arm_id, joint, reading)
            if res["is_spoofed"]:
                spoofed_joints.append(joint)
                alert_msg = res["message"]
                if res.get("unmasked_danger"):
                    has_danger = True

        return {
            "is_spoofed": len(spoofed_joints) > 0,
            "spoofed_joints": spoofed_joints,
            "alert": alert_msg or "No spoofing detected.",
            "unmasked_danger": has_danger
        }
