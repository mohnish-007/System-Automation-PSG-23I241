import os
import re

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_notes.txt")

CRITICAL_WORDS = [
    "urgent", "grinding", "leakage", "leaking", "grease", "backlash",
    "seizure", "hot", "smoke", "failure", "broken", "asap"
]

WARNING_WORDS = [
    "warm", "clicking", "whining", "chatter", "slight", "monitor",
    "elevated", "intermittent", "noise", "play"
]

NORMAL_WORDS = [
    "routine", "smooth", "clean", "normal", "within spec", "fine", "inspected"
]

IRRELEVANT_TOPICS = [
    "lunch", "safety tape", "warning signs", "cleaning", "conveyor",
    "hex keys", "toolbox", "dust filters", "cabinet"
]

class MaintenanceLogAnalyzer:
    def __init__(self, log_path=None):
        self.log_path = log_path or LOG_PATH
        self.entries = []
        if self.log_path and os.path.exists(self.log_path):
            self.load_entries()

    def load_entries(self):
        with open(self.log_path, "r", encoding="utf-8") as f:
            content = f.read()

        raw_blocks = re.split(r"(?=\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", content)
        self.entries = []

        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue

            lines = block.split("\n", 1)
            header = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""

            ts_match = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", header)
            timestamp = ts_match.group(1) if ts_match else "UNKNOWN"

            parsed = self.parse_text(body or header)
            self.entries.append({
                "timestamp": timestamp,
                "header": header,
                "text": body or header,
                **parsed
            })

    def parse_text(self, text):
        text_lower = text.lower()

        arms_found = re.findall(r"\barm[\s\-]?(\d+)\b", text_lower)
        arm_ids = [f"Arm-{num}" for num in arms_found]
        joints_found = [j for j in ["shoulder", "elbow", "wrist"] if j in text_lower]

        cleaned_text = re.sub(r"\bno\s+[\w\s]{0,15}(leak|leakage|noise|vibration|grease|heat)", "", text_lower)

        matched_crit = [w for w in CRITICAL_WORDS if w in cleaned_text]
        matched_warn = [w for w in WARNING_WORDS if w in cleaned_text]
        matched_norm = [w for w in NORMAL_WORDS if w in text_lower]

        is_irrelevant = any(irr in text_lower for irr in IRRELEVANT_TOPICS) and not arms_found

        if matched_crit:
            level = "CRITICAL"
            score = 0.9
        elif matched_warn:
            level = "WARNING"
            score = 0.5
        elif matched_norm and not matched_warn and not matched_crit:
            level = "NORMAL"
            score = 0.1
        elif is_irrelevant or not arms_found:
            level = "NONE"
            score = 0.0
        else:
            level = "LOW"
            score = 0.2

        return {
            "arm_ids": arm_ids,
            "joints": joints_found,
            "risk_level": level,
            "risk_score": score,
            "matched_keywords": matched_crit + matched_warn + matched_norm,
            "is_irrelevant": is_irrelevant
        }

    def get_signal_for_arm(self, arm_id):
        matched = [e for e in self.entries if arm_id.lower() in [a.lower() for a in e["arm_ids"]]]

        if not matched:
            return {
                "arm_id": arm_id,
                "has_notes": False,
                "risk_level": "NONE",
                "risk_score": 0.0,
                "summary": "No technician notes logged for this arm.",
                "matched_keywords": []
            }

        severity = {"CRITICAL": 3, "WARNING": 2, "LOW": 1, "NORMAL": 0, "NONE": 0}
        top_entry = max(matched, key=lambda e: severity.get(e["risk_level"], 0))

        return {
            "arm_id": arm_id,
            "has_notes": True,
            "risk_level": top_entry["risk_level"],
            "risk_score": top_entry["risk_score"],
            "summary": top_entry["text"],
            "timestamp": top_entry["timestamp"],
            "matched_keywords": top_entry["matched_keywords"]
        }

if __name__ == "__main__":
    analyzer = MaintenanceLogAnalyzer()
    print(f"Loaded {len(analyzer.entries)} entries.")
    for arm in ["Arm-1", "Arm-2", "Arm-3", "Arm-4", "Arm-5"]:
        res = analyzer.get_signal_for_arm(arm)
        print(f"[{arm}] Level: {res['risk_level']} | Summary: {res['summary']}")
