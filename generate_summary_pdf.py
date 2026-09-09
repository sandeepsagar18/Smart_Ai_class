import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_quick_summary_pdf(output_path="SmartClassVision_Quick_Summary.pdf"):
    pdf_path = Path(output_path)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor("#1A365D")    # Deep Navy
    SECONDARY = colors.HexColor("#2B6CB0")  # Slate Blue
    ACCENT = colors.HexColor("#319795")     # Teal
    DARK_TEXT = colors.HexColor("#2D3748")  # Charcoal
    LIGHT_BG = colors.HexColor("#F7FAFC")   # Soft Off-white
    BORDER = colors.HexColor("#CBD5E0")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=SECONDARY,
        alignment=TA_CENTER
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=PRIMARY,
        spaceBefore=6,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=DARK_TEXT
    )

    header_cell_style = ParagraphStyle(
        'HCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.white
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("SmartClass Vision — Quick Reference Summary", title_style))
    story.append(Paragraph("Enterprise AI Biometric Attendance & Security Architecture | High-Yield Cheat Sheet", subtitle_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=6, spaceBefore=0))

    # Section 1: Core AI Models & Purpose
    story.append(Paragraph("1. Core AI Models & Why We Use Them", h2_style))
    
    model_data = [
        [
            Paragraph("<b>Model</b>", header_cell_style),
            Paragraph("<b>Role in System</b>", header_cell_style),
            Paragraph("<b>Key Benefit & Why Selected</b>", header_cell_style)
        ],
        [
            Paragraph("<b>OpenCV YuNet</b><br/><i>(2023 ONNX)</i>", body_style),
            Paragraph("Face Detection &<br/>5-Point Landmarks", body_style),
            Paragraph("Ultra-fast C++ DNN (~15ms CPU). Detects micro-faces & extracts 5 key landmarks (eyes, nose, mouth) for <b>affine alignment</b>.", body_style)
        ],
        [
            Paragraph("<b>InsightFace ArcFace</b><br/><i>(ResNet-50 / 512-D)</i>", body_style),
            Paragraph("Biometric Face<br/>Recognition", body_style),
            Paragraph("Additive Angular Margin Loss maximizes inter-class distance. Outperforms FaceNet/dlib with <b>99.8% accuracy</b> on normalized 512-D vectors.", body_style)
        ],
        [
            Paragraph("<b>Liveness & Quality Engine</b>", body_style),
            Paragraph("Anti-Spoofing &<br/>Quality Filter", body_style),
            Paragraph("Rejects motion blur, extreme head turns (yaw &gt; 1.4), dark shots, and screen photo attacks using Moiré & frequency analysis.", body_style)
        ]
    ]

    t_model = Table(model_data, colWidths=[110, 110, 320])
    t_model.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(t_model)
    story.append(Spacer(1, 6))

    # Section 2: Key Numbers to Remember
    story.append(Paragraph("2. Key Thresholds & Numbers to Remember (Quick Cheat Sheet)", h2_style))
    
    thresh_data = [
        [
            Paragraph("<b>Metric</b>", header_cell_style),
            Paragraph("<b>Value</b>", header_cell_style),
            Paragraph("<b>Purpose & Practical Meaning</b>", header_cell_style)
        ],
        [
            Paragraph("<b>Cosine Similarity</b>", body_style),
            Paragraph("<b>&ge; 0.65</b>", body_style),
            Paragraph("ArcFace confidence threshold required to confirm match.", body_style)
        ],
        [
            Paragraph("<b>Top-1 vs Top-2 Margin</b>", body_style),
            Paragraph("<b>&ge; 0.12</b>", body_style),
            Paragraph("Ambiguity rejection gate. Prevents misidentifying lookalikes/twins.", body_style)
        ],
        [
            Paragraph("<b>Burst Capture Size</b>", body_style),
            Paragraph("<b>10 Shots</b>", body_style),
            Paragraph("Synchronized multi-shot capture sequence across the classroom.", body_style)
        ],
        [
            Paragraph("<b>Consensus Requirement</b>", body_style),
            Paragraph("<b>&ge; 5 of 10</b>", body_style),
            Paragraph("Student must appear in &ge; 5 shots to eliminate accidental passers-by.", body_style)
        ],
        [
            Paragraph("<b>Min Sharpness (Laplacian)</b>", body_style),
            Paragraph("<b>40.0</b>", body_style),
            Paragraph("Discards blurry frames or moving faces.", body_style)
        ],
        [
            Paragraph("<b>Registration Poses</b>", body_style),
            Paragraph("<b>5 Angles</b>", body_style),
            Paragraph("Center, Left, Right, Up, Down for complete facial profile.", body_style)
        ]
    ]

    t_thresh = Table(thresh_data, colWidths=[130, 75, 335])
    t_thresh.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(t_thresh)
    story.append(Spacer(1, 6))

    # Section 3: Recent New Updates
    story.append(Paragraph("3. Summary of Recent Major Updates", h2_style))
    story.append(Paragraph("&bull; <b>Complete ArcFace + YuNet Migration:</b> Removed legacy FaceNet & YOLO models; standardized on 512-D L2 embeddings.", bullet_style))
    story.append(Paragraph("&bull; <b>Strict Section & Roster Validation:</b> Students are validated against enrolled section. Cross-class students are flagged <i>REJECTED - WRONG CLASS</i>.", bullet_style))
    story.append(Paragraph("&bull; <b>Cryptographic HMAC-SHA256 Signatures:</b> Every attendance CSV is signed with file hash + faculty ID to prevent manual Excel edits.", bullet_style))
    story.append(Paragraph("&bull; <b>Automated Audit Logs:</b> Rejections, spoof attempts, and mismatch reasons are automatically logged to SQLite database.", bullet_style))
    story.append(Paragraph("&bull; <b>Optimized Video Streaming:</b> Real-time live HUD overlay with instant countdowns, enrolled candidate counts, and green capture feedback.", bullet_style))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceAfter=4, spaceBefore=0))
    
    footer_text = Paragraph(
        "<i>SmartClass Vision &bull; Designed for high-speed, secure, multi-student biometric classroom attendance.</i>",
        ParagraphStyle('Footer', parent=body_style, alignment=TA_CENTER, textColor=colors.gray, fontSize=7.5)
    )
    story.append(footer_text)

    doc.build(story)
    print(f"PDF generated successfully at: {pdf_path.resolve()}")

if __name__ == "__main__":
    generate_quick_summary_pdf()
