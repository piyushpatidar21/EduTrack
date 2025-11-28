import sqlite3
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import os

DB_PATH = os.getenv("EDUTRACK_DB", "edutrack.db")

@contextmanager
def get_conn():
    """SQLite connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def create_tables() -> None:
    """Create all EduTrack tables."""
    with get_conn() as conn:
        cur = conn.cursor()
        
        # Teachers table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Classes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            )
        """)
        
        # Subjects table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE
            )
        """)
        
        # Students table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                student_name TEXT NOT NULL,
                roll_number TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(class_id, roll_number),
                FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE
            )
        """)
        
        # Student records table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                attendance REAL DEFAULT 0,
                marks REAL DEFAULT 0,
                mst_marks REAL DEFAULT 0,
                study_hours REAL DEFAULT 0,
                assignments REAL DEFAULT 0,
                extracurriculars REAL DEFAULT 0,
                projects INTEGER DEFAULT 0,
                certifications INTEGER DEFAULT 0,
                internships INTEGER DEFAULT 0,
                predicted_grade TEXT DEFAULT 'C',
                risk_score REAL DEFAULT 0.5,
                risk_level TEXT DEFAULT 'Medium',
                recommendation TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )
        """)
        
        # Add missing columns if they don't exist (for schema migration)
        cur.execute("PRAGMA table_info(student_records)")
        columns = {col[1] for col in cur.fetchall()}
        
        for col_name, col_def in [
            ("projects", "INTEGER DEFAULT 0"),
            ("certifications", "INTEGER DEFAULT 0"),
            ("internships", "INTEGER DEFAULT 0"),
            ("mst_marks", "REAL DEFAULT 0")
        ]:
            if col_name not in columns:
                try:
                    cur.execute(f"ALTER TABLE student_records ADD COLUMN {col_name} {col_def}")
                except Exception:
                    pass
        
        conn.commit()

# ==================== TEACHER OPERATIONS ====================

def add_teacher(name: str, email: str, password_hash: str) -> int:
    """Add a new teacher."""
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO teachers (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return -1

def get_teacher_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get teacher by email."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM teachers WHERE email = ?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_teacher(teacher_id: int) -> Optional[Dict[str, Any]]:
    """Get teacher by ID."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,))
        row = cur.fetchone()
        return dict(row) if row else None

# ==================== CLASS OPERATIONS ====================

def add_class(teacher_id: int, class_name: str) -> int:
    """Add a new class."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO classes (teacher_id, class_name) VALUES (?, ?)",
            (teacher_id, class_name)
        )
        conn.commit()
        return cur.lastrowid

def get_teacher_classes(teacher_id: int) -> List[Dict[str, Any]]:
    """Get all classes for a teacher."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM classes WHERE teacher_id = ? ORDER BY id DESC", (teacher_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def get_class(class_id: int) -> Optional[Dict[str, Any]]:
    """Get class by ID."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def update_class(class_id: int, class_name: str) -> bool:
    """Update class name."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE classes SET class_name = ? WHERE id = ?", (class_name, class_id))
        conn.commit()
        return cur.rowcount > 0

def delete_class(class_id: int) -> bool:
    """Delete a class."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        conn.commit()
        return cur.rowcount > 0

def get_all_classes() -> List[Dict[str, Any]]:
    """Get all classes across all teachers."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM classes ORDER BY class_name")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

# ==================== SUBJECT OPERATIONS ====================

def add_subject(class_id: int, subject_name: str) -> int:
    """Add a subject to a class."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO subjects (class_id, subject_name) VALUES (?, ?)",
            (class_id, subject_name)
        )
        conn.commit()
        return cur.lastrowid

def get_class_subjects(class_id: int) -> List[Dict[str, Any]]:
    """Get all subjects for a class."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM subjects WHERE class_id = ? ORDER BY id", (class_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def get_subject(subject_id: int) -> Optional[Dict[str, Any]]:
    """Get subject by ID."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def update_subject(subject_id: int, subject_name: str) -> bool:
    """Update subject name."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE subjects SET subject_name = ? WHERE id = ?", (subject_name, subject_id))
        conn.commit()
        return cur.rowcount > 0

def delete_subject(subject_id: int) -> bool:
    """Delete a subject."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
        return cur.rowcount > 0

# ==================== STUDENT OPERATIONS ====================

def add_student(class_id: int, student_name: str, roll_number: str) -> int:
    """Add a student to a class."""
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO students (class_id, student_name, roll_number) VALUES (?, ?, ?)",
                (class_id, student_name, roll_number)
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return -1

def get_class_students(class_id: int) -> List[Dict[str, Any]]:
    """Get all students in a class."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE class_id = ? ORDER BY roll_number", (class_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def get_student(student_id: int) -> Optional[Dict[str, Any]]:
    """Get student by ID."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def update_student(student_id: int, student_name: str, roll_number: str) -> bool:
    """Update student info."""
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE students SET student_name = ?, roll_number = ? WHERE id = ?",
                (student_name, roll_number, student_id)
            )
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.IntegrityError:
            return False

def delete_student(student_id: int) -> bool:
    """Delete a student."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        return cur.rowcount > 0

# ==================== STUDENT RECORD OPERATIONS ====================

def add_record(
    student_id: int, subject_id: int, attendance: float, marks: float,
    mst_marks: float, study_hours: float, assignments: float,
    extracurriculars: float, projects: int, certifications: int, internships: int,
    predicted_grade: str, risk_score: float, risk_level: str, recommendation: str
) -> int:
    """Add or update a student record."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM student_records WHERE student_id = ? AND subject_id = ?",
            (student_id, subject_id)
        )
        existing = cur.fetchone()
        
        if existing:
            cur.execute(
                """UPDATE student_records 
                   SET attendance=?, marks=?, mst_marks=?, study_hours=?, assignments=?,
                       extracurriculars=?, projects=?, certifications=?, internships=?,
                       predicted_grade=?, risk_score=?, risk_level=?, recommendation=?,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE student_id=? AND subject_id=?""",
                (attendance, marks, mst_marks, study_hours, assignments,
                 extracurriculars, projects, certifications, internships,
                 predicted_grade, risk_score, risk_level, recommendation,
                 student_id, subject_id)
            )
        else:
            cur.execute(
                """INSERT INTO student_records
                   (student_id, subject_id, attendance, marks, mst_marks, study_hours,
                    assignments, extracurriculars, projects, certifications, internships,
                    predicted_grade, risk_score, risk_level, recommendation)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (student_id, subject_id, attendance, marks, mst_marks, study_hours,
                 assignments, extracurriculars, projects, certifications, internships,
                 predicted_grade, risk_score, risk_level, recommendation)
            )
        conn.commit()
        return existing[0] if existing else cur.lastrowid

def get_student_records(student_id: int) -> List[Dict[str, Any]]:
    """Get all records for a student."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT sr.*, s.subject_name FROM student_records sr
            JOIN subjects s ON sr.subject_id = s.id
            WHERE sr.student_id = ?
            ORDER BY sr.created_at DESC
        """, (student_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def get_class_records(class_id: int) -> List[Dict[str, Any]]:
    """Get all records for students in a class."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT sr.*, st.student_name, s.subject_name FROM student_records sr
            JOIN students st ON sr.student_id = st.id
            JOIN subjects s ON sr.subject_id = s.id
            WHERE st.class_id = ?
            ORDER BY sr.created_at DESC
        """, (class_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def get_record(record_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific record."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM student_records WHERE id = ?", (record_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def delete_record(record_id: int) -> bool:
    """Delete a record."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM student_records WHERE id = ?", (record_id,))
        conn.commit()
        return cur.rowcount > 0

def get_at_risk_students(class_id: int) -> List[Dict[str, Any]]:
    """Get all high-risk students in a class."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT sr.*, st.student_name, s.subject_name FROM student_records sr
            JOIN students st ON sr.student_id = st.id
            JOIN subjects s ON sr.subject_id = s.id
            WHERE st.class_id = ? AND sr.risk_score >= 0.7
            ORDER BY sr.risk_score DESC
        """, (class_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

# Initialize on import
create_tables()

