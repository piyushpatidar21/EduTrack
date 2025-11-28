"""PDF report generation for EduTrack."""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
from typing import Dict, Any
import statistics

def generate_student_report(
    student_name: str,
    class_name: str,
    records: list,
    teacher_name: str = "Teacher"
) -> bytes:
    """
    Generate a PDF report for a student.
    records: List of dict with keys: subject_name, attendance, marks, mst_marks,
             study_hours, assignments, extracurriculars, predicted_grade, risk_score, recommendation
    Returns PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph("EduTrack Performance Report", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Student Info
    info_data = [
        ["Student Name", student_name],
        ["Class", class_name],
        ["Teacher", teacher_name],
        ["Report Date", datetime.now().strftime("%Y-%m-%d %H:%M")],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Subject Records Table
    if records:
        elements.append(Paragraph("Subject Performance", styles['Heading2']))
        elements.append(Spacer(1, 0.15*inch))
        
        table_data = [["Subject", "Attendance", "Marks", "MST", "Study Hrs", "Assignments", "Grade", "Risk"]]
        for rec in records:
            table_data.append([
                rec.get("subject_name", "N/A"),
                f"{rec.get('attendance', 0):.1f}%",
                f"{rec.get('marks', 0):.1f}%",
                f"{rec.get('mst_marks', 0):.1f}",
                f"{rec.get('study_hours', 0):.1f}",
                f"{rec.get('assignments', 0):.1f}%",
                rec.get("predicted_grade", "N/A"),
                f"{rec.get('risk_score', 0):.2f}",
            ])
        
        table = Table(table_data, colWidths=[1.2*inch, 0.9*inch, 0.8*inch, 0.7*inch, 0.85*inch, 0.95*inch, 0.6*inch, 0.6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
        ]))
        elements.append(table)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Recommendations
    if records and records[0].get("recommendation"):
        elements.append(Paragraph("Recommendations", styles['Heading2']))
        for rec in records:
            if rec.get("recommendation"):
                elements.append(Paragraph(f"• {rec['recommendation']}", styles['Normal']))
    
    doc.build(elements)
    return buffer.getvalue()

def generate_class_report(class_name: str, records: list) -> bytes:
    """
    Generate a PDF report for a class showing all student performance.
    records: List of dict with keys: student_name, subject_name, attendance, marks, mst_marks,
             study_hours, assignments, predicted_grade, risk_score
    Returns PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph("EduTrack Class Performance Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Class Info
    info_data = [
        ["Class Name", class_name],
        ["Report Date", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Total Records", str(len(records))],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Class Records Table
    if records:
        elements.append(Paragraph("All Student Records", styles['Heading2']))
        elements.append(Spacer(1, 0.15*inch))
        
        table_data = [["Student", "Subject", "Attendance", "Marks", "MST", "Study Hrs", "Grade", "Risk"]]
        for rec in records:
            table_data.append([
                rec.get("student_name", "N/A"),
                rec.get("subject_name", "N/A"),
                f"{rec.get('attendance', 0):.1f}%",
                f"{rec.get('marks', 0):.1f}%",
                f"{rec.get('mst_marks', 0):.1f}",
                f"{rec.get('study_hours', 0):.1f}",
                rec.get("predicted_grade", "N/A"),
                f"{rec.get('risk_score', 0):.0%}",
            ])
        
        table = Table(table_data, colWidths=[1.2*inch, 1.2*inch, 0.9*inch, 0.8*inch, 0.7*inch, 0.85*inch, 0.6*inch, 0.6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
        ]))
        elements.append(table)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary Statistics
    if records:
        elements.append(Paragraph("Summary Statistics", styles['Heading2']))
        
        attendances = [r.get('attendance', 0) for r in records]
        marks_list = [r.get('marks', 0) for r in records]
        
        summary_text = f"""
        <b>Class Average Attendance:</b> {statistics.mean(attendances):.1f}%<br/>
        <b>Class Average Marks:</b> {statistics.mean(marks_list):.1f}%<br/>
        <b>High-Risk Students:</b> {len([r for r in records if r.get('risk_score', 0) >= 0.7])}<br/>
        """
        
        elements.append(Paragraph(summary_text, styles['Normal']))
    
    doc.build(elements)
    return buffer.getvalue()
