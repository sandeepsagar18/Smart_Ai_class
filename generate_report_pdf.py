import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def build_comprehensive_report_pdf(output_path="SmartClassVision_Project_Report.pdf"):
    pdf_path = Path(output_path)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    PRIMARY = colors.HexColor("#0F172A")    # Deep Slate / Navy
    SECONDARY = colors.HexColor("#1E3A8A")  # Royal Blue
    ACCENT = colors.HexColor("#0D9488")     # Teal Accent
    DARK_TEXT = colors.HexColor("#1E293B")  # Charcoal Text
    LIGHT_BG = colors.HexColor("#F8FAFC")   # Light background
    BORDER = colors.HexColor("#CBD5E1")     # Border grey
    ALERT_BG = colors.HexColor("#FEF3C7")   # Soft amber
    ALERT_BORDER = colors.HexColor("#F59E0B")

    styles = getSampleStyleSheet()

    doc_title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        alignment=TA_CENTER
    )

    doc_sub_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=SECONDARY,
        alignment=TA_CENTER
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=SECONDARY,
        spaceBefore=12,
        spaceAfter=5
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=7,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=DARK_TEXT,
        alignment=TA_LEFT
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    story = []

    # ==================== HEADER ====================
    story.append(Paragraph("SmartClass Vision — Complete Technical Report", doc_title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("System Implementation, Model Justification & Architecture Summary", doc_sub_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.8, color=ACCENT, spaceAfter=10, spaceBefore=0))

    # ==================== SECTION 1 ====================
    story.append(Paragraph("1. Executive Overview & What Was Implemented", h1_style))
    story.append(Paragraph(
        "<b>SmartClass Vision</b> is an automated classroom attendance and security intelligence system designed "
        "to eliminate attendance fraud, proxy check-ins, and manual roll-call delays. The system captures synchronized "
        "burst frames of the classroom, detects and aligns all faces simultaneously, validates biometric quality and liveness, "
        "matches identities using high-dimensional angular embeddings, and cryptographically signs audit logs.",
        body_style
    ))
    story.append(Spacer(1, 4))

    impl_data = [
        [
            Paragraph("<b>Implemented Feature</b>", th_style),
            Paragraph("<b>Technical Functionality & Engineering Implementation</b>", th_style)
        ],
        [
            Paragraph("<b>OpenCV YuNet Detection & Landmark Alignment</b>", body_style),
            Paragraph("Replaced generic detectors with YuNet C++ ONNX model. Detects faces at micro-scales and extracts 5 landmarks (eyes, nose, mouth) to mathematically rotate faces via <b>Affine Transformations</b> before recognition.", body_style)
        ],
        [
            Paragraph("<b>InsightFace ArcFace 512-D Recognition</b>", body_style),
            Paragraph("Upgraded legacy FaceNet (128-D) to ArcFace (512-D). Employs <b>Additive Angular Margin Loss</b> to maximize inter-person separation. Feature vectors are L2-normalized and matched via vectorized cosine distance.", body_style)
        ],
        [
            Paragraph("<b>Multi-Shot Temporal Voting Consensus</b>", body_style),
            Paragraph("Captures a 10-shot burst across the classroom. Enforces a <b>minimum 5-shot quorum</b> and average cosine score &ge; 0.65 to prevent false triggers from passers-by outside doors.", body_style)
        ],
        [
            Paragraph("<b>Strict Section & Class Isolation</b>", body_style),
            Paragraph("Validates candidates against target Degree, Year, Branch, and Section. Students enrolled in another class are explicitly flagged <b>REJECTED - WRONG CLASS</b>, logged as incidents, and denied attendance.", body_style)
        ],
        [
            Paragraph("<b>Hardware-Independent Anti-Spoofing</b>", body_style),
            Paragraph("Multi-stage quality firewall checks Laplacian sharpness (&ge;40.0), pose yaw ratio (&le;1.4), and high-frequency Moiré patterns to reject smartphone screen and printed photo presentation attacks.", body_style)
        ],
        [
            Paragraph("<b>Cryptographic Signatures (HMAC-SHA256)</b>", body_style),
            Paragraph("Every generated attendance CSV is hashed and cryptographically signed with the teacher's credentials using HMAC-SHA256, permanently preventing manual offline alterations in Excel.", body_style)
        ],
        [
            Paragraph("<b>5-Pose Guided Student Registration HUD</b>", body_style),
            Paragraph("Interactive registration camera interface requiring 5 distinct angles (Center, Left, Right, Up, Down) with live quality meters (sharpness, light) and instant Spacebar capture lock.", body_style)
        ]
    ]

    t_impl = Table(impl_data, colWidths=[170, 362])
    t_impl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t_impl)
    story.append(Spacer(1, 8))

    # ==================== SECTION 2 ====================
    story.append(Paragraph("2. Which Models Are Being Used & Why", h1_style))
    story.append(Paragraph(
        "The project strictly runs two modern, state-of-the-art computer vision models. All obsolete legacy models "
        "(such as YOLOv8-Face, FaceNet 128-D, and dlib) were completely removed:",
        body_style
    ))
    story.append(Spacer(1, 4))

    model_cards = [
        [
            Paragraph("<b>MODEL 1: OpenCV YuNet (Face Detection & Alignment)</b>", th_style),
            Paragraph("<b>MODEL 2: InsightFace ArcFace (Face Recognition)</b>", th_style)
        ],
        [
            Paragraph(
                "&bull; <b>Model File:</b> <code>face_detection_yunet_2023mar.onnx</code><br/>"
                "&bull; <b>Execution Engine:</b> Native OpenCV C++ DNN module.<br/>"
                "&bull; <b>Input/Output:</b> Full frame &rarr; BBoxes + 5-point facial landmarks.<br/>"
                "&bull; <b>Why YuNet?</b><br/>"
                "1. <b>Extremely Fast:</b> Runs in ~15ms on standard CPU hardware without GPU requirements.<br/>"
                "2. <b>Micro-Face Detection:</b> Accurately detects distant students in large lecture halls.<br/>"
                "3. <b>Built-in Landmark Regression:</b> Provides coordinates for both eyes, nose, and mouth corners, enabling precise <b>Affine transformation alignment</b> so faces are upright and standardized before recognition.",
                body_style
            ),
            Paragraph(
                "&bull; <b>Model File:</b> <code>w600k_r50.onnx</code> (ResNet-50 backbone).<br/>"
                "&bull; <b>Execution Engine:</b> ONNX Runtime / Vectorized NumPy.<br/>"
                "&bull; <b>Embedding Size:</b> 512-Dimensional L2-Normalized Vector.<br/>"
                "&bull; <b>Why ArcFace over FaceNet / dlib?</b><br/>"
                "1. <b>Additive Angular Margin:</b> ArcFace optimizes geodesic distance on a hypersphere. Unlike FaceNet's Euclidean triplet loss, ArcFace produces compact intra-class clusters and huge inter-class margins.<br/>"
                "2. <b>Extreme Accuracy:</b> Achieves <b>>99.8% on LFW benchmark</b>.<br/>"
                "3. <b>Zero Ambiguity:</b> Enforces dual thresholds (Cosine &ge; 0.65 and Top-1 vs Top-2 Margin &ge; 0.12).",
                body_style
            )
        ]
    ]

    t_models = Table(model_cards, colWidths=[266, 266])
    t_models.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), SECONDARY),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#065F46")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG]),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t_models)
    story.append(Spacer(1, 8))

    # ==================== SECTION 3 ====================
    story.append(Paragraph("3. Core Numerical Parameters & Thresholds (To Remember)", h1_style))
    
    thresh_table = [
        [
            Paragraph("<b>Parameter</b>", th_style),
            Paragraph("<b>Threshold</b>", th_style),
            Paragraph("<b>Operational Meaning & Engineering Defense</b>", th_style)
        ],
        [
            Paragraph("<b>ArcFace Cosine Similarity</b>", body_style),
            Paragraph("<b>&ge; 0.65</b>", body_style),
            Paragraph("Confidence requirement for biometric identity confirmation.", body_style)
        ],
        [
            Paragraph("<b>Top-1 vs Top-2 Margin</b>", body_style),
            Paragraph("<b>&ge; 0.12</b>", body_style),
            Paragraph("Ambiguity gate. Discards matches if the top two candidates are too close.", body_style)
        ],
        [
            Paragraph("<b>Burst Capture Shots</b>", body_style),
            Paragraph("<b>10 Frames</b>", body_style),
            Paragraph("Synchronized high-resolution bursts across the classroom.", body_style)
        ],
        [
            Paragraph("<b>Temporal Quorum Votes</b>", body_style),
            Paragraph("<b>&ge; 5 of 10</b>", body_style),
            Paragraph("Candidate must be detected and verified across at least 5 frames.", body_style)
        ],
        [
            Paragraph("<b>Min Sharpness (Laplacian)</b>", body_style),
            Paragraph("<b>40.0</b>", body_style),
            Paragraph("Rejects motion-blurred or poorly focused face crops.", body_style)
        ],
        [
            Paragraph("<b>Max Pose Yaw Ratio</b>", body_style),
            Paragraph("<b>&le; 1.40</b>", body_style),
            Paragraph("Rejects extreme profile/side-facing head angles.", body_style)
        ],
        [
            Paragraph("<b>Registration Poses</b>", body_style),
            Paragraph("<b>5 Angles</b>", body_style),
            Paragraph("Center, Left, Right, Up, Down for complete facial feature enrollment.", body_style)
        ]
    ]

    t_th = Table(thresh_table, colWidths=[150, 75, 307])
    t_th.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t_th)
    story.append(Spacer(1, 8))

    # ==================== FOOTER ====================
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=5, spaceBefore=4))
    story.append(Paragraph(
        "<b>Summary for Viva / Presentation:</b> <i>SmartClass Vision pairs <b>OpenCV YuNet</b> (for 15ms 5-landmark affine face alignment) "
        "with <b>InsightFace ArcFace</b> (for 512-D angular margin biometrics). Attendance is proxy-proof via 10-shot temporal consensus, "
        "strict Section isolation, liveness anti-spoofing, and tamper-evident HMAC-SHA256 signatures.</i>",
        ParagraphStyle('FooterSummary', parent=body_style, fontSize=8, leading=11, textColor=DARK_TEXT)
    ))

    doc.build(story)
    print(f"Report PDF generated at: {pdf_path.resolve()}")

if __name__ == "__main__":
    build_comprehensive_report_pdf()
