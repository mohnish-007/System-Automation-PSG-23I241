LIMITS = {
    "torque": {
        "shoulder": 140.0,
        "elbow": 95.0,
        "wrist": 45.0,
    },
    "temperature": 85.0,
    "vibration": 7.5
}

class SafetyInterlock:
    def __init__(self, limits=None):
        self.limits = limits or LIMITS

    def evaluate_joint(self, joint_name, reading):
        joint = joint_name.lower()
        torque = reading.get("torque_nm", 0.0)
        temp = reading.get("temperature_c", 0.0)
        vib = reading.get("vibration_mms", 0.0)

        max_torque = self.limits["torque"].get(joint, 100.0)
        if torque > max_torque:
            return True, f"CRITICAL: {joint.upper()} torque {torque:.1f} Nm exceeds safety limit of {max_torque:.1f} Nm", {
                "rule": "TORQUE_LIMIT_EXCEEDED",
                "joint": joint,
                "metric": "torque_nm",
                "value": torque,
                "limit": max_torque,
                "action": "EMERGENCY_STOP"
            }

        max_temp = self.limits["temperature"]
        if temp > max_temp:
            return True, f"CRITICAL: {joint.upper()} temperature {temp:.1f} C exceeds safety limit of {max_temp:.1f} C", {
                "rule": "TEMPERATURE_LIMIT_EXCEEDED",
                "joint": joint,
                "metric": "temperature_c",
                "value": temp,
                "limit": max_temp,
                "action": "EMERGENCY_STOP"
            }

        max_vib = self.limits["vibration"]
        if vib > max_vib:
            return True, f"CRITICAL: {joint.upper()} vibration {vib:.2f} mm/s exceeds structural limit of {max_vib:.2f} mm/s", {
                "rule": "VIBRATION_LIMIT_EXCEEDED",
                "joint": joint,
                "metric": "vibration_mms",
                "value": vib,
                "limit": max_vib,
                "action": "EMERGENCY_STOP"
            }

        return False, None, None

    def evaluate_arm(self, arm_readings):
        for joint, reading in arm_readings.items():
            tripped, reason, details = self.evaluate_joint(joint, reading)
            if tripped:
                return True, reason, details
        return False, None, None
