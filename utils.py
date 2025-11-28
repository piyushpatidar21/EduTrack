"""Utility functions for EduTrack."""
from typing import Dict, List, Any

def validate_email(email: str) -> bool:
    """Simple email validation."""
    return "@" in email and "." in email.split("@")[1]

def validate_roll_number(roll_number: str) -> bool:
    """Validate roll number (simple alphanumeric)."""
    return bool(roll_number) and len(roll_number) <= 20

def format_metrics_table(record: Dict[str, Any]) -> Dict[str, str]:
    """Format a record for display in tables."""
    return {
        "Subject": record.get("subject_name", "N/A"),
        "Attendance": f"{record.get('attendance', 0):.1f}%",
        "Marks": f"{record.get('marks', 0):.1f}%",
        "MST": f"{record.get('mst_marks', 0):.1f}",
        "Study Hrs": f"{record.get('study_hours', 0):.1f}",
        "Assignments": f"{record.get('assignments', 0):.1f}%",
        "Extras": f"{record.get('extracurriculars', 0):.0f}",
        "Grade": record.get("predicted_grade", "N/A"),
        "Risk": f"{record.get('risk_score', 0):.2f}",
    }

def get_grade_emoji(grade: str) -> str:
    """Return emoji for grade."""
    emojis = {"A": "🌟", "B": "✨", "C": "👍", "D": "⚠️"}
    return emojis.get(grade, "•")

def get_risk_emoji(level: str) -> str:
    """Return emoji for risk level."""
    emojis = {"Low": "✅", "Medium": "⚡", "High": "🔴"}
    return emojis.get(level, "•")
