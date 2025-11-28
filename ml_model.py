"""ML model utilities for EduTrack."""
import numpy as np
import backend

def get_grade_color(grade: str) -> str:
    """Map grade to color for UI."""
    colors = {"A": "#10b981", "B": "#3b82f6", "C": "#f59e0b", "D": "#ef4444"}
    return colors.get(grade, "#6b7280")

def get_risk_color(level: str) -> str:
    """Map risk level to color for UI."""
    colors = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}
    return colors.get(level, "#6b7280")

def format_metrics(attendance, marks, mst, study_hours, assignments, extras) -> Dict:
    """Format metrics for display."""
    return {
        "Attendance": f"{attendance:.1f}%",
        "Marks": f"{marks:.1f}%",
        "MST (out of 40)": f"{mst:.1f}",
        "Study Hours/Week": f"{study_hours:.1f}",
        "Assignments": f"{assignments:.1f}%",
        "Extracurriculars": f"{extras:.0f}/10",
    }

from typing import Dict
