# Unit and integration tests for the Robotic Arm Health Monitoring System

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.safety_interlock import SafetyInterlock
from src.predictive_wear import JointWearPredictor
from src.text_log_analyzer import MaintenanceLogAnalyzer
from src.spoof_detector import SpoofedSensorDetector
from src.health_monitor import RoboticArmHealthMonitor

class TestRoboticArmMonitoring(unittest.TestCase):

    def setUp(self):
        self.safety = SafetyInterlock()
        self.log_analyzer = MaintenanceLogAnalyzer()
        self.spoof_detector = SpoofedSensorDetector()
        self.monitor = RoboticArmHealthMonitor()

    # Requirement 1: Safety Interlock Tests
    def test_torque_safety_limit(self):
        """Shoulder torque over 140 Nm must trigger immediate EMERGENCY_STOP."""
        readings = {
            "shoulder": {"torque_nm": 145.0, "temperature_c": 50.0, "vibration_mms": 1.5},
            "elbow":    {"torque_nm": 40.0,  "temperature_c": 45.0, "vibration_mms": 1.0},
            "wrist":    {"torque_nm": 15.0,  "temperature_c": 40.0, "vibration_mms": 0.8}
        }
        tripped, reason, details = self.safety.evaluate_arm(readings)
        self.assertTrue(tripped)
        self.assertEqual(details["action"], "EMERGENCY_STOP")
        self.assertEqual(details["joint"], "shoulder")

    def test_temperature_safety_limit(self):
        """Joint temperature over 85 C must trigger immediate EMERGENCY_STOP."""
        readings = {
            "shoulder": {"torque_nm": 60.0, "temperature_c": 50.0, "vibration_mms": 1.5},
            "elbow":    {"torque_nm": 40.0, "temperature_c": 88.0, "vibration_mms": 1.0},
            "wrist":    {"torque_nm": 15.0, "temperature_c": 40.0, "vibration_mms": 0.8}
        }
        tripped, reason, details = self.safety.evaluate_arm(readings)
        self.assertTrue(tripped)
        self.assertEqual(details["action"], "EMERGENCY_STOP")
        self.assertEqual(details["joint"], "elbow")

    def test_vibration_safety_limit(self):
        """Vibration over 7.5 mm/s must trigger immediate stop."""
        readings = {
            "shoulder": {"torque_nm": 60.0, "temperature_c": 50.0, "vibration_mms": 1.5},
            "elbow":    {"torque_nm": 40.0, "temperature_c": 45.0, "vibration_mms": 1.0},
            "wrist":    {"torque_nm": 15.0, "temperature_c": 40.0, "vibration_mms": 8.0}
        }
        tripped, reason, details = self.safety.evaluate_arm(readings)
        self.assertTrue(tripped)
        self.assertEqual(details["action"], "EMERGENCY_STOP")
        self.assertEqual(details["joint"], "wrist")

    # Requirement 2: Predictive Wear Model Tests
    def test_wear_model_prediction(self):
        predictor = JointWearPredictor()
        # Normal reading should have lower wear score
        normal_res = predictor.predict_joint("shoulder", {
            "torque_nm": 60.0, "temperature_c": 45.0, "vibration_mms": 1.2,
            "operating_hours": 800, "load_kg": 2.5
        })
        self.assertIn(normal_res["predicted_state"], ["Normal", "Warning"])
        self.assertLess(normal_res["wear_score"], 0.7)

        # High wear reading should predict failure
        worn_res = predictor.predict_joint("shoulder", {
            "torque_nm": 125.0, "temperature_c": 82.0, "vibration_mms": 6.8,
            "operating_hours": 12000, "load_kg": 9.0
        })
        self.assertEqual(worn_res["predicted_state"], "Failure")
        self.assertGreater(worn_res["wear_score"], 0.8)

    # Requirement 3: Maintenance Notes Signal Tests
    def test_technician_notes_parsing(self):
        arm3 = self.log_analyzer.get_signal_for_arm("Arm-3")
        self.assertTrue(arm3["has_notes"])
        self.assertEqual(arm3["risk_level"], "CRITICAL")
        self.assertIn("grinding", arm3["matched_keywords"])

        arm2 = self.log_analyzer.get_signal_for_arm("Arm-2")
        self.assertTrue(arm2["has_notes"])
        self.assertEqual(arm2["risk_level"], "NORMAL")

    def test_irrelevant_notes_filtered(self):
        text = "Dave took a lunch break. Replaced paper towels in restroom."
        res = self.log_analyzer.parse_text(text)
        self.assertEqual(res["risk_level"], "NONE")
        self.assertTrue(res["is_irrelevant"])

    # Requirement 4: Spoofed Sensor Tests
    def test_physics_spoof_detection(self):
        """Attacker feeds fake low torque while bearing is overheating with high vibration."""
        res = self.spoof_detector.evaluate_reading("Arm-7", "shoulder", {
            "torque_nm": 15.0,       # Falsified low
            "temperature_c": 82.0,   # High heat
            "vibration_mms": 6.8,    # High vibration
            "load_kg": 6.0
        })
        self.assertTrue(res["is_spoofed"])
        self.assertEqual(res["attack_type"], "CROSS_CORRELATION_VIOLATION")

    def test_frozen_signal_detection(self):
        """Identical repeated readings should be detected as frozen."""
        detector = SpoofedSensorDetector()
        for _ in range(5):
            detector.update_history("Arm-X", "elbow", 40.0)
        is_frozen, msg = detector.check_frozen("Arm-X", "elbow")
        self.assertTrue(is_frozen)
        self.assertIn("FROZEN_SIGNAL", msg)

    # Requirement 5: All 4 Decisions Reachable
    def test_all_four_decisions_reachable(self):
        # 1. SAFE
        r_safe = self.monitor.evaluate_arm("Arm-2", {
            "shoulder": {"torque_nm": 62.0, "temperature_c": 46.0, "vibration_mms": 1.3, "operating_hours": 1000, "load_kg": 3.0},
            "elbow":    {"torque_nm": 41.0, "temperature_c": 42.0, "vibration_mms": 1.1, "operating_hours": 1000, "load_kg": 3.0},
            "wrist":    {"torque_nm": 17.0, "temperature_c": 38.0, "vibration_mms": 0.8, "operating_hours": 1000, "load_kg": 3.0}
        })
        self.assertEqual(r_safe["final_decision"], "SAFE")

        # 2. MONITOR
        r_mon = self.monitor.evaluate_arm("Arm-1", {
            "shoulder": {"torque_nm": 70.0, "temperature_c": 52.0, "vibration_mms": 1.6, "operating_hours": 4200, "load_kg": 4.5},
            "elbow":    {"torque_nm": 56.8, "temperature_c": 62.4, "vibration_mms": 3.1, "operating_hours": 4500, "load_kg": 4.5},
            "wrist":    {"torque_nm": 22.0, "temperature_c": 44.0, "vibration_mms": 1.3, "operating_hours": 4500, "load_kg": 4.5}
        })
        self.assertEqual(r_mon["final_decision"], "MONITOR")

        # 3. SCHEDULE_MAINTENANCE
        r_maint = self.monitor.evaluate_arm("Arm-3", {
            "shoulder": {"torque_nm": 72.0, "temperature_c": 51.0, "vibration_mms": 1.7, "operating_hours": 7500, "load_kg": 5.0},
            "elbow":    {"torque_nm": 48.0, "temperature_c": 49.0, "vibration_mms": 1.4, "operating_hours": 7500, "load_kg": 5.0},
            "wrist":    {"torque_nm": 33.2, "temperature_c": 76.0, "vibration_mms": 5.8, "operating_hours": 9200, "load_kg": 5.0}
        })
        self.assertEqual(r_maint["final_decision"], "SCHEDULE_MAINTENANCE")

        # 4. EMERGENCY_STOP
        r_stop = self.monitor.evaluate_arm("Arm-6", {
            "shoulder": {"torque_nm": 155.0, "temperature_c": 50.0, "vibration_mms": 1.5, "operating_hours": 2000, "load_kg": 5.0},
            "elbow":    {"torque_nm": 40.0,  "temperature_c": 45.0, "vibration_mms": 1.0, "operating_hours": 2000, "load_kg": 5.0},
            "wrist":    {"torque_nm": 18.0,  "temperature_c": 40.0, "vibration_mms": 0.9, "operating_hours": 2000, "load_kg": 5.0}
        })
        self.assertEqual(r_stop["final_decision"], "EMERGENCY_STOP")

if __name__ == "__main__":
    unittest.main()
