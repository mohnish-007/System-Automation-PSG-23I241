from src.safety_interlock import SafetyInterlock
from src.predictive_wear import JointWearPredictor
from src.text_log_analyzer import MaintenanceLogAnalyzer
from src.spoof_detector import SpoofedSensorDetector

class RoboticArmHealthMonitor:
    def __init__(self, limits=None, model_path=None, log_path=None):
        self.safety = SafetyInterlock(limits)
        self.wear_model = JointWearPredictor(model_path) if model_path else JointWearPredictor()
        self.log_analyzer = MaintenanceLogAnalyzer(log_path)
        self.spoof_detector = SpoofedSensorDetector()

    def evaluate_arm(self, arm_id, arm_readings):
        tripped, trip_reason, trip_details = self.safety.evaluate_arm(arm_readings)
        if tripped:
            return {
                "arm_id": arm_id,
                "final_decision": "EMERGENCY_STOP",
                "trigger": "SAFETY_LIMIT_TRIPPED",
                "summary": trip_reason,
                "safety_interlock": {"tripped": True, "details": trip_details},
                "spoof_defense": None,
                "predictive_ml": None,
                "maintenance_log": None,
                "action": "Trigger emergency stop. Inspect machine immediately."
            }

        spoof = self.spoof_detector.evaluate_arm(arm_id, arm_readings)
        if spoof["is_spoofed"]:
            if spoof.get("unmasked_danger"):
                return {
                    "arm_id": arm_id,
                    "final_decision": "EMERGENCY_STOP",
                    "trigger": "CRITICAL_SPOOF_ATTACK",
                    "summary": f"Emergency stop: Spoofed sensor masking critical danger! {spoof['alert']}",
                    "safety_interlock": {"tripped": False},
                    "spoof_defense": spoof,
                    "predictive_ml": None,
                    "maintenance_log": None,
                    "action": "Immediate stop. Sensor tampered and physical hardware in danger."
                }
            else:
                return {
                    "arm_id": arm_id,
                    "final_decision": "SCHEDULE_MAINTENANCE",
                    "trigger": "SPOOF_DETECTED",
                    "summary": f"Sensor anomaly detected: {spoof['alert']}",
                    "safety_interlock": {"tripped": False},
                    "spoof_defense": spoof,
                    "predictive_ml": None,
                    "maintenance_log": None,
                    "action": "Schedule technician to inspect sensor wiring and calibration."
                }

        ml_res = self.wear_model.predict_arm(arm_readings)
        log_res = self.log_analyzer.get_signal_for_arm(arm_id)

        ml_state = ml_res["aggregate_state"]
        log_level = log_res["risk_level"]

        if ml_state == "Failure" or log_level == "CRITICAL":
            decision = "SCHEDULE_MAINTENANCE"
            reasons = []
            if ml_state == "Failure":
                reasons.append(f"ML wear model predicted failure risk (score: {ml_res['max_wear_score']:.2f})")
            if log_level == "CRITICAL":
                reasons.append(f"Technician log noted critical issue: '{log_res['summary']}'")
            summary = " | ".join(reasons)
            action = "Schedule maintenance to repair or replace worn joint components."

        elif ml_state == "Warning" or log_level == "WARNING":
            decision = "MONITOR"
            reasons = []
            if ml_state == "Warning":
                reasons.append(f"ML wear model indicates moderate wear (score: {ml_res['max_wear_score']:.2f})")
            if log_level == "WARNING":
                reasons.append(f"Technician logged warning note: '{log_res['summary']}'")
            summary = " | ".join(reasons)
            action = "Monitor joint performance closely during upcoming shifts."

        else:
            decision = "SAFE"
            summary = "Sensors within normal ranges, ML model predicts healthy, and no technician issues logged."
            action = "Continue normal operations."

        return {
            "arm_id": arm_id,
            "final_decision": decision,
            "trigger": f"FUSION [ML={ml_state}, Log={log_level}]",
            "summary": summary,
            "safety_interlock": {"tripped": False},
            "spoof_defense": spoof,
            "predictive_ml": ml_res,
            "maintenance_log": log_res,
            "action": action
        }
