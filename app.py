import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime
import io

import database
import backend
import pdf_report

st.set_page_config(
    page_title="EduTrack",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    [data-testid="stToolbar"] { display: none; }
    .main > div { padding-top: 0 !important; }
    .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.student_class_id = None

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.student_class_id = None

# ==================== LOGIN / REGISTER ====================

def page_auth():
    """Authentication page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>📊 EduTrack</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Track, Analyze & Predict Student Performance</p>", unsafe_allow_html=True)
        
        role_selection = st.radio("Login as:", ["Teacher", "Student"], horizontal=True)
        st.divider()
        
        if role_selection == "Teacher":
            auth_tab, register_tab = st.tabs(["Login", "Register"])
            
            with auth_tab:
                st.markdown("### Teacher Login")
                email_login = st.text_input("Email", key="login_email", placeholder="teacher@example.com")
                password_login = st.text_input("Password", type="password", key="login_password")
                
                if st.button("Login", use_container_width=True, type="primary"):
                    if email_login and password_login:
                        ok, msg, teacher = backend.login_teacher(email_login, password_login)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.user_id = teacher["id"]
                            st.session_state.username = teacher["name"]
                            st.session_state.role = "Teacher"
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter email and password.")
            
            with register_tab:
                st.markdown("### Teacher Registration")
                name_register = st.text_input("Full Name", key="register_name", placeholder="John Doe")
                email_register = st.text_input("Email", key="register_email", placeholder="john@example.com")
                password_register = st.text_input("Password", type="password", key="register_password")
                
                if st.button("Register", use_container_width=True):
                    if name_register and email_register and password_register:
                        ok, msg = backend.register_teacher(name_register, email_register, password_register)
                        if ok:
                            st.success(msg + " You can now login.")
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please fill all fields.")
        
        else:
            st.markdown("### Student Login")
            st.info("Select your class and enter your roll number to view your performance.")
            
            all_classes = database.get_all_classes()
            
            if not all_classes:
                st.warning("No classes available yet. Contact your teacher.")
            else:
                class_names = [c["class_name"] for c in all_classes]
                selected_class_name = st.selectbox("Select Your Class", class_names)
                selected_class = next((c for c in all_classes if c["class_name"] == selected_class_name), None)
                
                student_roll = st.text_input("Enter Your Roll Number", placeholder="e.g., 101")
                
                if st.button("Login", use_container_width=True, type="primary"):
                    if selected_class and student_roll:
                        students = database.get_class_students(selected_class["id"])
                        student = next((s for s in students if s["roll_number"] == student_roll), None)
                        
                        if student:
                            st.session_state.logged_in = True
                            st.session_state.user_id = student["id"]
                            st.session_state.username = student["student_name"]
                            st.session_state.role = "Student"
                            st.session_state.student_class_id = selected_class["id"]
                            st.success(f"Welcome, {student['student_name']}!")
                            st.rerun()
                        else:
                            st.error("Student not found. Check your class and roll number.")
                    else:
                        st.warning("Please select a class and enter your roll number.")

# ==================== STUDENT DASHBOARD ====================

def page_student_dashboard():
    """Student dashboard - matching your design concept."""
    with st.sidebar:
        st.markdown("### 📊 EduTrack")
        st.write(f"Signed in as: **{st.session_state.username}** (Student)")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    
    st.title("Student Dashboard")
    
    student_id = st.session_state.user_id
    records = database.get_student_records(student_id)
    
    if not records:
        st.info("No performance records yet. Check back after your teacher adds your data.")
    else:
        latest_record = records[-1]
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    padding: 30px; border-radius: 12px; color: white; text-align: center; margin-bottom: 30px;">
            <h2 style="margin: 0; font-size: 18px; opacity: 0.9;">Predicted Grade</h2>
            <h1 style="margin: 10px 0 0 0; font-size: 56px;">{latest_record['predicted_grade']}</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Grade Probability")
        
        # Calculate probabilities from prediction
        predicted_grade = latest_record['predicted_grade']
        prob_base = 0.60 if predicted_grade == 'B' else (0.25 if predicted_grade == 'A' else (0.10 if predicted_grade == 'C' else 0.05))
        grade_probs = {
            'A': 0.15 if predicted_grade != 'A' else prob_base,
            'B': 0.60 if predicted_grade == 'B' else 0.25,
            'C': 0.20 if predicted_grade == 'C' else 0.10,
            'D': 0.05 if predicted_grade != 'D' else 0.30
        }
        
        prob_df = pd.DataFrame([
            {"Grade": g, "Probability": p} for g, p in grade_probs.items()
        ])
        
        color_map = {'A': '#3b82f6', 'B': '#f59e0b', 'C': '#ef4444', 'D': '#6b7280'}
        
        chart = alt.Chart(prob_df).mark_bar().encode(
            y=alt.Y('Grade:N', title='Grade', sort=['A', 'B', 'C', 'D']),
            x=alt.X('Probability:Q', title='Probability', axis=alt.Axis(format='%')),
            color=alt.Color('Grade:N', scale=alt.Color(domain=['A','B','C','D'], 
                           range=['#3b82f6','#f59e0b','#ef4444','#6b7280']), legend=None),
            tooltip=['Grade', alt.Tooltip('Probability:Q', format='.0%')]
        ).properties(height=200)
        
        st.altair_chart(chart, use_container_width=True)
        
        st.divider()
        
        st.subheader("Risk Assessment")
        
        risk_score = latest_record['risk_score']
        risk_level = latest_record['risk_level']
        
        risk_colors = {'Low': '#3b82f6', 'Medium': '#f59e0b', 'High': '#ef4444'}
        risk_color = risk_colors.get(risk_level, '#6b7280')
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Risk Level**")
            st.markdown(f"<h2 style='color: {risk_color}; margin: 0;'>{risk_level}</h2>", unsafe_allow_html=True)
            st.progress(risk_score)
        
        with col2:
            st.write("")
            st.metric("Risk Score", f"{risk_score:.0%}")
        
        st.divider()
        
        st.subheader("How to Reduce Risk")
        
        tips = []
        if latest_record['attendance'] < 75:
            tips.append("• Maintain attendance above 75%")
        if latest_record['marks'] < 60:
            tips.append("• Focus on stronger study habits to improve marks")
        if latest_record['mst_marks'] < 16:
            tips.append("• Schedule regular MST revision sessions")
        if latest_record['study_hours'] < 8:
            tips.append("• Increase study hours to at least 8-12 per week")
        if latest_record['assignments'] < 60:
            tips.append("• Complete all assignments on time")
        if latest_record['extracurriculars'] < 2:
            tips.append("• Participate in extracurricular activities")
        if latest_record['projects'] == 0:
            tips.append("• Work on at least one project")
        if latest_record['certifications'] == 0:
            tips.append("• Pursue certifications in your field")
        if latest_record['internships'] == 0:
            tips.append("• Look for internship opportunities")
        
        if not tips:
            tips.append("✅ Maintain current habits and review weekly to keep risk low")
        
        for tip in tips[:5]:
            st.write(tip)
        
        st.divider()
        
        st.subheader("Recommendations")
        st.write(f"• {latest_record.get('recommendation', 'Keep up the excellent work!')}")
        
        st.divider()
        
        st.subheader("Download Your Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = pd.DataFrame(records).to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Report (CSV)",
                data=csv_data,
                file_name=f"{st.session_state.username}_performance.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            if st.button("📥 Download Report (PDF)", use_container_width=True):
                pdf_bytes = pdf_report.generate_student_report(
                    student_name=st.session_state.username,
                    records=records
                )
                st.download_button(
                    label="PDF Ready",
                    data=pdf_bytes,
                    file_name=f"{st.session_state.username}_performance.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="pdf_btn"
                )
        
        st.divider()
        
        st.subheader("View My Recent Submissions")
        
        with st.expander("📊 Click to expand", expanded=False):
            if records:
                df_display = pd.DataFrame([
                    {
                        "ID": r['id'],
                        "Subject": r.get('subject_name', 'N/A'),
                        "Attendance": f"{r['attendance']:.0f}%",
                        "Marks": f"{r['marks']:.0f}%",
                        "MST": f"{r['mst_marks']:.0f}/40",
                        "Assignments": f"{r['assignments']:.0f}%",
                        "Study Hours": f"{r['study_hours']:.1f}",
                        "Extracurriculars": int(r['extracurriculars']),
                        "Projects": int(r['projects']),
                        "Certifications": int(r['certifications']),
                        "Internships": int(r['internships']),
                        "Grade": r['predicted_grade'],
                        "Risk": r['risk_level']
                    }
                    for r in records
                ])
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)

# ==================== TEACHER DASHBOARD ====================

def page_teacher_dashboard():
    """Teacher dashboard with full control."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title(f"👋 Welcome, {st.session_state.username}!")
    
    with col2:
        if st.button("Logout"):
            logout()
            st.rerun()
    
    st.divider()
    
    classes = database.get_teacher_classes(st.session_state.user_id)
    
    if not classes:
        st.info("No classes yet. Create one to get started.")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Overview", "Manage Classes", "Manage Students", "Manage Subjects",
        "Add Academic Details", "At-Risk Students", "Analytics"
    ])
    
    with tab1:
        st.header("Overview")
        
        total_students = sum(len(database.get_class_students(c["id"])) for c in classes)
        total_subjects = sum(len(database.get_class_subjects(c["id"])) for c in classes)
        total_records = sum(len(database.get_class_records(c["id"])) for c in classes)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Classes", len(classes))
        with col2:
            st.metric("Students", total_students)
        with col3:
            st.metric("Subjects", total_subjects)
        with col4:
            st.metric("Records", total_records)
    
    with tab2:
        st.header("Manage Classes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Create New Class")
            with st.form("create_class"):
                class_name = st.text_input("Class Name", placeholder="e.g., Class 10-A")
                if st.form_submit_button("Create", use_container_width=True):
                    if class_name:
                        database.add_class(st.session_state.user_id, class_name)
                        st.success(f"Class '{class_name}' created!")
                        st.rerun()
                    else:
                        st.warning("Enter class name")
        
        with col2:
            st.subheader("Manage Existing Classes")
            if classes:
                for cls in classes:
                    with st.expander(f"📚 {cls['class_name']}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            new_name = st.text_input("New Name", value=cls['class_name'], key=f"name_{cls['id']}")
                            if st.button("Update", key=f"upd_{cls['id']}", use_container_width=True):
                                database.update_class(cls['id'], new_name)
                                st.success("Updated!")
                                st.rerun()
                        with col_b:
                            if st.button("Delete", key=f"del_{cls['id']}", use_container_width=True):
                                database.delete_class(cls['id'])
                                st.success("Deleted!")
                                st.rerun()
            else:
                st.info("No classes to manage")
    
    with tab3:
        st.header("Manage Students")
        
        if not classes:
            st.warning("Create a class first")
        else:
            selected_cls_name = st.selectbox("Select Class", [c['class_name'] for c in classes], key="st_cls")
            cls = next((c for c in classes if c['class_name'] == selected_cls_name), None)
            
            if cls:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Add Student")
                    with st.form("add_student"):
                        st_name = st.text_input("Student Name")
                        roll_num = st.text_input("Roll Number")
                        if st.form_submit_button("Add", use_container_width=True):
                            if st_name and roll_num:
                                sid = database.add_student(cls['id'], st_name, roll_num)
                                if sid != -1:
                                    st.success(f"Added {st_name}!")
                                    st.rerun()
                                else:
                                    st.error("Duplicate roll number")
                            else:
                                st.warning("Fill all fields")
                
                with col2:
                    st.subheader("Class Students")
                    students = database.get_class_students(cls['id'])
                    if students:
                        for student in students:
                            col_name, col_delete = st.columns([3, 1])
                            with col_name:
                                st.write(f"📝 {student['student_name']} (Roll: {student['roll_number']})")
                            with col_delete:
                                if st.button("Delete", key=f"del_st_{student['id']}", use_container_width=True):
                                    database.delete_student(student['id'])
                                    st.success(f"Deleted {student['student_name']}!")
                                    st.rerun()
                    else:
                        st.info("No students")
    
    with tab4:
        st.header("Manage Subjects")
        st.write("Add subjects for each class. Students' records will be tracked per subject.")
        
        if not classes:
            st.warning("Create a class first")
        else:
            selected_cls_name = st.selectbox("Select Class", [c['class_name'] for c in classes], key="subj_cls")
            cls = next((c for c in classes if c['class_name'] == selected_cls_name), None)
            
            if cls:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Add Subject")
                    with st.form("add_subject"):
                        subject_name = st.text_input("Subject Name", placeholder="e.g., Mathematics, English, Science")
                        if st.form_submit_button("Add", use_container_width=True):
                            if subject_name:
                                subject_id = database.add_subject(cls['id'], subject_name)
                                if subject_id != -1:
                                    st.success(f"Added '{subject_name}' to {cls['class_name']}!")
                                    st.rerun()
                                else:
                                    st.error("Failed to add subject")
                            else:
                                st.warning("Enter subject name")
                
                with col2:
                    st.subheader("Class Subjects")
                    subjects = database.get_class_subjects(cls['id'])
                    if subjects:
                        for subj in subjects:
                            col_x, col_y = st.columns([3, 1])
                            with col_x:
                                st.write(f"📖 {subj['subject_name']}")
                            with col_y:
                                if st.button("Delete", key=f"del_subj_{subj['id']}", use_container_width=True):
                                    database.delete_subject(subj['id'])
                                    st.success("Deleted!")
                                    st.rerun()
                    else:
                        st.info("No subjects yet. Add one above!")
    
    with tab5:
        st.header("Add Academic Details")
        st.write("Enter comprehensive student performance data using all 9 metrics for ML-based grade prediction.")
        
        if not classes:
            st.warning("⚠️ Create a class first")
        else:
            selected_cls_name = st.selectbox("Select Class", [c['class_name'] for c in classes], key="rec_cls")
            cls = next((c for c in classes if c['class_name'] == selected_cls_name), None)
            
            if cls:
                students = database.get_class_students(cls['id'])
                subjects = database.get_class_subjects(cls['id'])
                
                if not students:
                    st.error("❌ No students in this class. Go to 'Manage Students' tab and add students first.")
                elif not subjects:
                    st.error("❌ No subjects in this class. Go to 'Manage Subjects' tab and add subjects first.")
                else:
                    st.write("---")
                    
                    with st.form("add_academic_details", border=True):
                        st.markdown("### 👤 Student & Subject Selection")
                        col_st, col_sub = st.columns(2)
                        
                        with col_st:
                            student_name = st.selectbox("Student", [s['student_name'] for s in students])
                            student = next((s for s in students if s['student_name'] == student_name), None)
                        
                        with col_sub:
                            subject_name = st.selectbox("Subject", [s['subject_name'] for s in subjects])
                            subject = next((s for s in subjects if s['subject_name'] == subject_name), None)
                        
                        st.divider()
                        
                        st.markdown("### 📊 Performance Metrics (All 9 Fields)")
                        
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        
                        with metric_col1:
                            st.write("**Core Academics**")
                            attendance = st.slider("Attendance (%)", 0, 100, 85, key="att_slider")
                            marks = st.slider("Marks (%)", 0, 100, 75, key="marks_slider")
                            mst_marks = st.slider("MST Marks (0-40)", 0.0, 40.0, 20.0, 0.5, key="mst_slider")
                        
                        with metric_col2:
                            st.write("**Assignment & Study**")
                            assignments = st.slider("Assignments (%)", 0, 100, 80, key="asgn_slider")
                            study_hours = st.number_input("Study Hours/Week", 0.0, 50.0, 10.0, 0.5, key="study_input")
                            extracurriculars = st.slider("Extracurriculars (0-10)", 0, 10, 3, key="extra_slider")
                        
                        with metric_col3:
                            st.write("**Achievements**")
                            projects = st.number_input("Projects Completed", 0, 20, 0, key="proj_input")
                            certifications = st.number_input("Certifications Earned", 0, 20, 0, key="cert_input")
                            internships = st.number_input("Internships Done", 0, 10, 0, key="intern_input")
                        
                        st.divider()
                        
                        submitted = st.form_submit_button("🚀 Save & Predict Grade", use_container_width=True, type="primary")
                    
                    if submitted and student and subject:
                        with st.spinner("Predicting grade and calculating risk..."):
                            predicted_grade, prob_map = backend.predict_grade(
                                attendance, marks, mst_marks, study_hours, assignments,
                                extracurriculars, projects, certifications, internships
                            )
                            
                            risk_score, risk_level, tips = backend.calculate_risk(
                                attendance, marks, mst_marks, study_hours, assignments,
                                extracurriculars, projects, certifications, internships, prob_map
                            )
                            
                            recommendation = backend.generate_recommendation(
                                attendance, marks, mst_marks, study_hours, assignments,
                                extracurriculars, projects, certifications, internships
                            )
                            
                            database.add_record(
                                student['id'], subject['id'],
                                attendance, marks, mst_marks, study_hours, assignments,
                                extracurriculars, projects, certifications, internships,
                                predicted_grade, risk_score, risk_level, recommendation
                            )
                        
                        st.success("✅ Record Saved Successfully!")
                        
                        col_res1, col_res2, col_res3 = st.columns(3)
                        
                        with col_res1:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                                <h3 style="margin: 0; font-size: 14px; opacity: 0.9;">Predicted Grade</h3>
                                <h1 style="margin: 10px 0 0 0; font-size: 48px;">{predicted_grade}</h1>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_res2:
                            risk_color = {'Low': '#3b82f6', 'Medium': '#f59e0b', 'High': '#ef4444'}.get(risk_level, '#6b7280')
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, {risk_color} 0%, {risk_color}dd 100%); 
                                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                                <h3 style="margin: 0; font-size: 14px; opacity: 0.9;">Risk Level</h3>
                                <h1 style="margin: 10px 0 0 0; font-size: 48px;">{risk_level}</h1>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_res3:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); 
                                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                                <h3 style="margin: 0; font-size: 14px; opacity: 0.9;">Risk Score</h3>
                                <h1 style="margin: 10px 0 0 0; font-size: 48px;">{risk_score:.0%}</h1>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.divider()
                        
                        st.markdown("**📋 Recommendation:**")
                        st.info(recommendation)
    
    with tab6:
        st.header("At-Risk Students")
        
        if not classes:
            st.warning("Create a class first")
        else:
            selected_cls_name = st.selectbox("Select Class", [c['class_name'] for c in classes], key="risk_cls")
            cls = next((c for c in classes if c['class_name'] == selected_cls_name), None)
            
            if cls:
                at_risk = database.get_at_risk_students(cls['id'])
                
                if not at_risk:
                    st.success("✅ No high-risk students in this class!")
                else:
                    st.warning(f"⚠️ {len(at_risk)} high-risk student(s)")
                    
                    for record in at_risk:
                        with st.expander(f"🚨 {record['student_name']} - {record['subject_name']}", expanded=True):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Risk Score", f"{record['risk_score']:.0%}")
                                st.metric("Grade", record['predicted_grade'])
                            with col2:
                                st.metric("Attendance", f"{record['attendance']:.0f}%")
                                st.metric("Marks", f"{record['marks']:.0f}%")
                            with col3:
                                st.metric("Study Hours", f"{record['study_hours']:.1f}")
                                st.metric("MST", f"{record['mst_marks']:.0f}/40")
                            
                            st.write(f"**Recommendation:** {record['recommendation']}")
    
    with tab7:
        st.header("Class Analytics & Overview")
        
        if not classes:
            st.warning("Create a class first")
        else:
            selected_cls_name = st.selectbox("Select Class", [c['class_name'] for c in classes], key="analytics_cls")
            cls = next((c for c in classes if c['class_name'] == selected_cls_name), None)
            
            if cls:
                records = database.get_class_records(cls['id'])
                
                if not records:
                    st.info("No records yet")
                else:
                    df = pd.DataFrame(records)
                    
                    st.subheader("Key Metrics")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Avg Attendance", f"{df['attendance'].mean():.1f}%")
                    with col2:
                        st.metric("Avg Marks", f"{df['marks'].mean():.1f}%")
                    with col3:
                        at_risk_count = len(df[df['risk_score'] >= 0.7])
                        st.metric("High Risk", at_risk_count)
                    with col4:
                        st.metric("Total Projects", int(df['projects'].sum()))
                    with col5:
                        st.metric("Total Certifications", int(df['certifications'].sum()))
                    
                    st.divider()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Grade Distribution")
                        grade_counts = df['predicted_grade'].value_counts().sort_index()
                        chart = alt.Chart(grade_counts.reset_index()).mark_bar().encode(
                            x=alt.X('predicted_grade:N', title='Grade'),
                            y=alt.Y('count():Q', title='Count'),
                            color=alt.Color('predicted_grade:N', scale=alt.Scale(scheme='set2'), legend=None)
                        ).properties(height=250)
                        st.altair_chart(chart, use_container_width=True)
                    
                    with col2:
                        st.subheader("Risk Distribution")
                        risk_data = pd.DataFrame({
                            "Risk": ["Low", "Medium", "High"],
                            "Count": [
                                len(df[df['risk_score'] < 0.4]),
                                len(df[(df['risk_score'] >= 0.4) & (df['risk_score'] < 0.7)]),
                                len(df[df['risk_score'] >= 0.7])
                            ]
                        })
                        chart = alt.Chart(risk_data).mark_bar().encode(
                            x=alt.X('Risk:N', title='Risk Level'),
                            y=alt.Y('Count:Q', title='Students'),
                            color=alt.Color('Risk:N', scale=alt.Scale(domain=['Low','Medium','High'],
                                          range=['#10b981','#f59e0b','#ef4444']), legend=None)
                        ).properties(height=250)
                        st.altair_chart(chart, use_container_width=True)
                    
                    st.subheader("Attendance vs Marks")
                    scatter = alt.Chart(df).mark_circle(size=100, opacity=0.6).encode(
                        x=alt.X('attendance:Q', title='Attendance (%)'),
                        y=alt.Y('marks:Q', title='Marks (%)'),
                        color=alt.Color('predicted_grade:N', scale=alt.Scale(scheme='set2')),
                        tooltip=['student_name', 'subject_name', 'attendance', 'marks', 'predicted_grade']
                    ).properties(height=300)
                    st.altair_chart(scatter, use_container_width=True)
                    
                    st.subheader("Student Achievements")
                    achievement_data = pd.DataFrame({
                        "Metric": ["Projects", "Certifications", "Internships"],
                        "Total": [int(df['projects'].sum()), int(df['certifications'].sum()), int(df['internships'].sum())]
                    })
                    
                    chart = alt.Chart(achievement_data).mark_bar().encode(
                        x=alt.X('Metric:N', title='Achievement Type'),
                        y=alt.Y('Total:Q', title='Total Count'),
                        color=alt.Color('Metric:N', scale=alt.Scale(scheme='set1'), legend=None)
                    ).properties(height=250)
                    st.altair_chart(chart, use_container_width=True)
                    
                    st.divider()
                    
                    st.subheader("Download Class Report")
                    if st.button("Generate PDF Report", use_container_width=True):
                        pdf_bytes = pdf_report.generate_class_report(
                            class_name=cls['class_name'],
                            records=records
                        )
                        st.download_button(
                            label="📥 Download Class Report (PDF)",
                            data=pdf_bytes,
                            file_name=f"{cls['class_name']}_report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="class_pdf_btn"
                        )

def main():
    if not st.session_state.logged_in:
        page_auth()
    else:
        if st.session_state.role == "Teacher":
            page_teacher_dashboard()
        elif st.session_state.role == "Student":
            page_student_dashboard()

if __name__ == "__main__":
    main()
