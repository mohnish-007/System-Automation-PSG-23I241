# Requirement 1: Immediate Safety Stop
# Deterministic rule check for hard physical safety limits (no ML involved)

# Threshold limits based on joint specs and safety standards
DEFAULT_LIMITS = {
    "torque": {
        "shoulder": 140.0,  # Nm (rated ~120 Nm; >140 indicates collision or severe jam)
        "elbow": 95.0,      # Nm (rated ~80 Nm; >95 indicates mechanical binding)
        "wrist": 45.0,      # Nm (rated ~35 Nm; >45 indicates gear shear / crash)
    },
    "temperature": 85.0,    # deg C (grease degradation and motor overheat limit)
    "vibration": 7.5        # mm/s (ISO 10816-3 Zone D dangerous vibration)
}

class SafetyInterlock:
    def __init__(self, limits=None):
        self.limits = limits or DEFAULT_LIMITS

    def evaluate_joint(self, joint_name, reading):
        """Check a single joint's sensor readings against hard safety limits."""
        joint = joint_name.lower()
        torque = reading.get("torque_nm", 0.0)
        temp = reading.get("temperature_c", 0.0)
        vib = reading.get("vibration_mms", 0.0)

        # 1. Torque check
        max_torque = self.limits["torque"].get(joint, 100.0)
        if torque > max_torque:
            reason = f"CRITICAL: {joint.upper()} torque {torque:.1f} Nm exceeds safety limit of {max_torque:.1f} Nm"
            details = {
                "rule": "TORQUE_LIMIT_EXCEEDED",
                "joint": joint,
                "metric": "torque_nm",
                "value": torque,
                "limit": max_torque,
                "action": "EMERGENCY_STOP"
            }
            return True, reason, details

        # 2. Temperature check
        max_temp = self.limits["temperature"]
        if temp > max_temp:
            reason = f"CRITICAL: {joint.upper()} temperature {temp:.1f} C exceeds safety limit of {max_temp:.1f} C"
            details = {
                "rule": "TEMPERATURE_LIMIT_EXCEEDED",
                "joint": joint,
                "metric": "temperature_c",
                "value": temp,
                "limit": max_temp,
                "action": "EMERGENCY_STOP"
            }
            return True, reason, details

        # 3. Vibration check
        max_vib = self.limits["vibration"]
        if vib > max_vib:
            reason = f"CRITICAL: {joint.upper()} vibration {vib:.2f} mm/s exceeds structural limit of {max_vib:.2f} mm/s"
            details = {
                "rule": "VIBRATION_LIMIT_EXCEEDED",
                "joint": joint,
                "metric": "vibration_mms",
                "value": vib,
                "limit": max_vib,
                "action": "EMERGENCY_STOP"
            }
            return True, reason, details

        return False, None, None

    def evaluate_arm(self, arm_readings):
        """Check all joints for an arm. If any joint violates a limit, trigger EMERGENCY_STOP."""
        for joint, reading in arm_readings.items():
            tripped, reason, details = self.evaluate_joint(joint, reading)
            if tripped:
                return True, reason, details
        return False, None, None
