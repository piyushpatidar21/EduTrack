from __future__ import annotations
import os
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import bcrypt
import database

MODEL_PATH = os.getenv("EDUTRACK_MODEL", "model.pkl")
_MODEL: Optional[RandomForestClassifier] = None
_CLASSES: Optional[List[str]] = None

def _generate_synthetic_dataset(n: int = 2000, seed: int = 42):
    """Generate synthetic training data for the ML model."""
    rng = np.random.default_rng(seed)
    attendance = rng.uniform(50, 100, size=n)
    marks = rng.uniform(30, 100, size=n)
    mst = rng.uniform(0, 40, size=n) / 40.0 * 100.0
    study_hours = rng.uniform(0, 40, size=n)
    assignments = rng.uniform(30, 100, size=n)
    extracurriculars = rng.integers(0, 11, size=n)
    projects = rng.integers(0, 6, size=n)
    certifications = rng.integers(0, 5, size=n)
    internships = rng.integers(0, 3, size=n)

    score = (
        marks * 0.30 +
        attendance * 0.15 +
        mst * 0.25 +
        (study_hours / 40.0) * 100.0 * 0.10 +
        (assignments / 100.0) * 100.0 * 0.05 +
        (extracurriculars / 10.0) * 100.0 * 0.05 +
        (projects / 5.0) * 100.0 * 0.05 +
        (certifications / 4.0) * 100.0 * 0.03 +
        (internships / 2.0) * 100.0 * 0.02
    )
    noise = rng.normal(0, 5, size=n)
    score = np.clip(score + noise, 0, 100)

    labels = np.empty(n, dtype=object)
    labels[score >= 85] = "A"
    labels[(score >= 70) & (score < 85)] = "B"
    labels[(score >= 55) & (score < 70)] = "C"
    labels[score < 55] = "D"

    X = np.column_stack([attendance, marks, mst, study_hours, assignments, 
                         extracurriculars, projects, certifications, internships])
    y = labels
    return X, y

def _ensure_model():
    """Load or train the ML model."""
    global _MODEL, _CLASSES
    if _MODEL is not None:
        return
    if os.path.exists(MODEL_PATH):
        _MODEL = joblib.load(MODEL_PATH)
        _CLASSES = list(_MODEL.classes_)
        return
    X, y = _generate_synthetic_dataset()
    model = RandomForestClassifier(n_estimators=200, random_state=0, class_weight="balanced_subsample")
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)
    _MODEL = model
    _CLASSES = list(model.classes_)

# ==================== AUTHENTICATION ====================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

def login_teacher(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Login a teacher. Returns (success, message, teacher_dict)."""
    teacher = database.get_teacher_by_email(email)
    if not teacher:
        return False, "Teacher not found.", None
    if verify_password(password, teacher["password_hash"]):
        return True, "Login successful.", teacher
    return False, "Incorrect password.", None

def register_teacher(name: str, email: str, password: str) -> Tuple[bool, str]:
    """Register a new teacher."""
    if not name or not email or not password:
        return False, "All fields required."
    existing = database.get_teacher_by_email(email)
    if existing:
        return False, "Email already registered."
    pw_hash = hash_password(password)
    teacher_id = database.add_teacher(name, email, pw_hash)
    if teacher_id == -1:
        return False, "Failed to register. Email may be taken."
    return True, "Teacher registered successfully."

# ==================== ML PREDICTIONS ====================

def predict_grade(
    attendance: float, marks: float, mst_marks: float,
    study_hours: float, assignments: float, extracurriculars: float,
    projects: int, certifications: int, internships: int
) -> Tuple[str, Dict[str, float]]:
    """
    Predict grade based on student metrics.
    Returns (predicted_grade, probabilities dict)
    """
    _ensure_model()
    assert _MODEL is not None and _CLASSES is not None
    
    mst_normalized = (mst_marks / 40.0) * 100.0
    X = np.array([[attendance, marks, mst_normalized, study_hours, assignments, 
                   extracurriculars, projects, certifications, internships]])
    probs = _MODEL.predict_proba(X)[0]
    pred_idx = int(np.argmax(probs))
    pred_label = _CLASSES[pred_idx]
    prob_map = {label: float(prob) for label, prob in zip(_CLASSES, probs)}
    return str(pred_label), prob_map

def calculate_risk(
    attendance: float, marks: float, mst_marks: float,
    study_hours: float, assignments: float, extracurriculars: float,
    projects: int, certifications: int, internships: int,
    prob_map: Optional[Dict[str, float]] = None
) -> Tuple[float, str, List[str]]:
    """Calculate risk score and mitigation tips."""
    risk = 0.0
    tips: List[str] = []
    
    if prob_map:
        risk += prob_map.get("D", 0.0) * 1.0
        risk += prob_map.get("C", 0.0) * 0.5

    if attendance < 75:
        risk += 0.20
        tips.append("Improve attendance to at least 85% for better outcomes.")
    if marks < 60:
        risk += 0.25
        tips.append("Focus on core subjects to raise marks above 70%.")
    if mst_marks < 16:
        risk += 0.20
        tips.append("MST performance is low. Schedule revision sessions weekly.")
    if study_hours < 8:
        risk += 0.10
        tips.append("Increase study hours to at least 12-15 hours per week.")
    if assignments < 60:
        risk += 0.15
        tips.append("Complete and revise assignments to boost score.")
    if extracurriculars < 2:
        risk += 0.05
        tips.append("Engage in extracurricular activities for balance.")
    
    if projects == 0:
        risk += 0.10
        tips.append("Complete project work to enhance practical skills.")
    if certifications == 0:
        risk += 0.08
        tips.append("Earn certifications to boost your profile.")
    if internships == 0:
        risk += 0.07
        tips.append("Consider internship opportunities for industry experience.")

    risk = min(max(risk, 0.0), 1.0)
    level = "Low" if risk < 0.4 else ("Medium" if risk < 0.7 else "High")

    if not tips:
        tips.append("Great job! Maintain consistency to keep your performance high.")
    
    return risk, level, tips

def generate_recommendation(
    attendance: float, marks: float, mst_marks: float,
    study_hours: float, assignments: float, extracurriculars: float,
    projects: int, certifications: int, internships: int
) -> str:
    """Generate a personalized recommendation string."""
    recs = []
    if attendance < 75:
        recs.append("Improve attendance")
    if marks < 70:
        recs.append("Focus on marks")
    if mst_marks < 16:
        recs.append("Boost MST prep")
    if study_hours < 10:
        recs.append("Increase study time")
    if assignments < 70:
        recs.append("Complete assignments")
    if extracurriculars < 2:
        recs.append("Join activities")
    if projects == 0:
        recs.append("Work on projects")
    if certifications == 0:
        recs.append("Earn certifications")
    if internships == 0:
        recs.append("Pursue internships")
    
    if not recs:
        return "Maintain current performance - you're excelling!"
    return " | ".join(recs)

# ==================== UI HELPERS ====================

def get_grade_color(grade: str) -> str:
    """Map grade to color for UI."""
    colors = {"A": "#10b981", "B": "#3b82f6", "C": "#f59e0b", "D": "#ef4444"}
    return colors.get(grade, "#6b7280")

def get_risk_color(level: str) -> str:
    """Map risk level to color for UI."""
    colors = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}
    return colors.get(level, "#6b7280")
