import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def create_presentation_pdf(output_path="SmartClassVision_Presentation.pdf"):
    pdf_path = Path(output_path)
    # Landscape orientation: 11 x 8.5 inches (792 x 612 pt)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(letter),
        rightMargin=40,
        leftMargin=40,
        topMargin=35,
        bottomMargin=35
    )

    # Color Palette
    PRIMARY = colors.HexColor("#0F172A")    # Deep Navy Slate
    SECONDARY = colors.HexColor("#1E3A8A")  # Royal Blue
    ACCENT = colors.HexColor("#0D9488")     # Emerald Teal
    HIGHLIGHT = colors.HexColor("#D97706")  # Amber
    CARD_BG = colors.HexColor("#F8FAFC")    # Cool light slate
    CARD_BORDER = colors.HexColor("#CBD5E1")# Border grey
    TEXT_DARK = colors.HexColor("#1E293B")
    TEXT_MUTED = colors.HexColor("#64748B")

    styles = getSampleStyleSheet()

    slide_title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=SECONDARY,
        spaceAfter=4
    )

    slide_subtitle_style = ParagraphStyle(
        'SlideSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=TEXT_MUTED,
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        'SlideBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=16,
        textColor=TEXT_DARK
    )

    body_bold = ParagraphStyle(
        'SlideBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    bullet_style = ParagraphStyle(
        'SlideBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=6
    )

    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.white
    )

    story = []

    def make_header(title, subtitle):
        return [
            Paragraph(title, slide_title_style),
            Paragraph(subtitle, slide_subtitle_style),
            HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=14, spaceBefore=0)
        ]

    # ==========================================
    # SLIDE 1: TITLE SLIDE
    # ==========================================
    story.append(Spacer(1, 40))
    title_main = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=PRIMARY,
        alignment=TA_CENTER
    )
    subtitle_main = ParagraphStyle(
        'MainSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=15,
        leading=20,
        textColor=SECONDARY,
        alignment=TA_CENTER
    )
    author_style = ParagraphStyle(
        'AuthorStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER
    )

    story.append(Paragraph("SmartClass Vision", title_main))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Enterprise Automated Classroom Biometrics & Security Architecture", subtitle_main))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="60%", thickness=3, color=ACCENT, spaceAfter=20, spaceBefore=0))
    story.append(Paragraph("<b>Next-Gen Edge AI Attendance System</b><br/>Powered by OpenCV YuNet &bull; InsightFace ArcFace &bull; Cryptographic Auditing", author_style))
    story.append(Spacer(1, 30))
    
    meta_box = [
        [Paragraph("<b>Domain:</b> Computer Vision / Edge AI", body_style), Paragraph("<b>Key Models:</b> YuNet (5-Pt) + ArcFace (512-D)", body_style)],
        [Paragraph("<b>Accuracy:</b> > 99.8% LFW Benchmark", body_style), Paragraph("<b>Security:</b> Anti-Spoofing + HMAC-SHA256 Signatures", body_style)]
    ]
    t_meta = Table(meta_box, colWidths=[320, 320])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, CARD_BORDER),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ]))
    story.append(t_meta)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 2: PROBLEM STATEMENT & SOLUTION
    # ==========================================
    story.extend(make_header("1. Problem Statement & The Smart Solution", "Why Traditional Attendance Fails & How AI Reinvents It"))
    
    col1_content = [
        Paragraph("<b>Traditional Methods (The Flaws)</b>", body_bold),
        Spacer(1, 6),
        Paragraph("&bull; <b>Time Waste:</b> Manual roll call consumes 10-15 minutes of every lecture.", bullet_style),
        Paragraph("&bull; <b>Proxy Attendance:</b> Friends sign sheets or swipe RFID cards for absentees.", bullet_style),
        Paragraph("&bull; <b>Single-Photo Vulnerability:</b> Mobile scans easily tricked by printed photos.", bullet_style),
        Paragraph("&bull; <b>Unenforced Section Control:</b> Students attend wrong lecture sections undetected.", bullet_style)
    ]
    
    col2_content = [
        Paragraph("<b>SmartClass Vision (The AI Solution)</b>", body_bold),
        Spacer(1, 6),
        Paragraph("&bull; <b>Zero Instructional Delay:</b> Automated 10-shot batch scan takes seconds.", bullet_style),
        Paragraph("&bull; <b>Proxy-Proof AI Voting:</b> Multi-shot temporal voting requires 5/10 match consensus.", bullet_style),
        Paragraph("&bull; <b>Anti-Spoofing Defense:</b> Moiré & frequency analysis rejects phone/paper attacks.", bullet_style),
        Paragraph("&bull; <b>Strict Section Isolation:</b> Automatically rejects non-enrolled students.", bullet_style)
    ]

    t_problem = Table([[col1_content, col2_content]], colWidths=[350, 350])
    t_problem.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#FFF5F5")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#F0FDF4")),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#FEB2B2")),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor("#86EFAC")),
        ('PADDING', (0, 0), (-1, -1), 14),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t_problem)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 3: SYSTEM ARCHITECTURE & AI PIPELINE
    # ==========================================
    story.extend(make_header("2. End-to-End AI Pipeline Architecture", "From Raw Multi-Student Classroom Capture to Cryptographic Attendance Record"))

    pipe_data = [
        [
            Paragraph("<b>Stage 1: Ingestion</b>", th_style),
            Paragraph("<b>Stage 2: Detection</b>", th_style),
            Paragraph("<b>Stage 3: Quality Gate</b>", th_style),
            Paragraph("<b>Stage 4: ArcFace Match</b>", th_style),
            Paragraph("<b>Stage 5: Consensus</b>", th_style)
        ],
        [
            Paragraph("<b>10-Shot Burst</b><br/><br/>Synchronized live classroom camera feed captures 10 rapid frames with audio/visual feedback.", body_style),
            Paragraph("<b>OpenCV YuNet</b><br/><br/>Locates all faces + extracts 5 landmarks per face. Applies <b>affine rotation alignment</b>.", body_style),
            Paragraph("<b>Anti-Spoof Filter</b><br/><br/>Verifies Laplacian sharpness (&ge;40), pose yaw (&le;1.4), and frequency Moiré screen detection.", body_style),
            Paragraph("<b>512-D Embedding</b><br/><br/>Vectorized inference against enrolled roster with Cosine &ge; 0.65 and Margin &ge; 0.12.", body_style),
            Paragraph("<b>Voting & Export</b><br/><br/>Requires &ge;5/10 votes + section roster match. Exports HMAC-SHA256 signed CSV.", body_style)
        ]
    ]

    t_pipe = Table(pipe_data, colWidths=[142, 142, 142, 142, 144])
    t_pipe.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG]),
        ('BOX', (0, 0), (-1, -1), 1, CARD_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, CARD_BORDER),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t_pipe)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 4: WHY YUNET + ARCFACE? (THE SCIENCE)
    # ==========================================
    story.extend(make_header("3. Why These Specific Models? (Technical Justification)", "Deep Dive into Model Selection: OpenCV YuNet vs. ArcFace"))

    model_comp = [
        [
            Paragraph("<b>Component</b>", th_style),
            Paragraph("<b>Selected Model</b>", th_style),
            Paragraph("<b>Alternative Considered</b>", th_style),
            Paragraph("<b>Why Our Choice is Superior</b>", th_style)
        ],
        [
            Paragraph("<b>Face Detection &<br/>Landmark Regression</b>", body_style),
            Paragraph("<b>OpenCV YuNet</b><br/>(2023 ONNX)", body_style),
            Paragraph("YOLOv8-Face /<br/>Haar Cascades", body_style),
            Paragraph("Runs in native C++ DNN with sub-15ms latency on standard CPU. Directly regresses 5 key landmarks (eyes, nose, mouth corners) enabling exact <b>affine facial alignment</b>.", body_style)
        ],
        [
            Paragraph("<b>Biometric Feature<br/>Embedding</b>", body_style),
            Paragraph("<b>InsightFace ArcFace</b><br/>(ResNet-50 / 512-D)", body_style),
            Paragraph("FaceNet (Triplet Loss) /<br/>dlib (HOG/ResNet)", body_style),
            Paragraph("ArcFace introduces an <b>Additive Angular Margin</b> penalty on the hypersphere, forcing intra-class compact clusters and large inter-class margins. Outperforms Euclidean Triplet Loss with <b>>99.8% LFW accuracy</b>.", body_style)
        ]
    ]

    t_comp = Table(model_comp, colWidths=[130, 130, 130, 322])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, colors.white]),
        ('BOX', (0, 0), (-1, -1), 1, CARD_BORDER),
        ('GRID', (0, 0), (-1, -1), 0.5, CARD_BORDER),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t_comp)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 5: KEY THRESHOLDS & NUMBERS
    # ==========================================
    story.extend(make_header("4. Key Parameters & Thresholds (To Remember)", "Core Numeric Benchmarks Enforced During Execution"))

    params_data = [
        [Paragraph("<b>Metric / Parameter</b>", th_style), Paragraph("<b>Value</b>", th_style), Paragraph("<b>Engineering Rationale</b>", th_style)],
        [Paragraph("<b>ArcFace Cosine Similarity Threshold</b>", body_style), Paragraph("<b>&ge; 0.65</b>", body_bold), Paragraph("Ensures zero false positives across multi-student classroom environments.", body_style)],
        [Paragraph("<b>Top-1 vs. Top-2 Margin Gap</b>", body_style), Paragraph("<b>&ge; 0.12</b>", body_bold), Paragraph("Ambiguity rejection gate: Prevents confusing siblings or lookalikes.", body_style)],
        [Paragraph("<b>Multi-Shot Burst Size</b>", body_style), Paragraph("<b>10 Shots</b>", body_bold), Paragraph("Captures full classroom view with variable student head positions.", body_style)],
        [Paragraph("<b>Temporal Consensus Quorum</b>", body_style), Paragraph("<b>&ge; 5 / 10 Votes</b>", body_bold), Paragraph("Eliminates accidental passers-by outside doors or brief occlusions.", body_style)],
        [Paragraph("<b>Minimum Sharpness (Laplacian)</b>", body_style), Paragraph("<b>40.0</b>", body_bold), Paragraph("Filters out blurry, motion-corrupted face crops before inference.", body_style)],
        [Paragraph("<b>Biometric Enrollment Profile</b>", body_style), Paragraph("<b>5 Guided Angles</b>", body_bold), Paragraph("Captures Center, Left, Right, Up, and Down angles during registration.", body_style)]
    ]

    t_params = Table(params_data, colWidths=[230, 100, 382])
    t_params.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, colors.white]),
        ('BOX', (0, 0), (-1, -1), 1, CARD_BORDER),
        ('GRID', (0, 0), (-1, -1), 0.5, CARD_BORDER),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t_params)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 6: SECURITY & NEW UPDATES
    # ==========================================
    story.extend(make_header("5. Security Architecture & Recent Updates", "Multi-Tiered Security & Enterprise Features Implemented"))

    sec1 = [
        Paragraph("<b>1. Section-Specific Validation</b>", body_bold),
        Spacer(1, 4),
        Paragraph("&bull; Attendance is strictly bound to Degree, Year, Branch, and Section.", bullet_style),
        Paragraph("&bull; Non-enrolled students are tagged <b>REJECTED - WRONG CLASS</b>.", bullet_style),
        Spacer(1, 8),
        Paragraph("<b>2. Cryptographic HMAC-SHA256 Signatures</b>", body_bold),
        Spacer(1, 4),
        Paragraph("&bull; Every CSV export is sealed with HMAC-SHA256 using faculty credentials.", bullet_style),
        Paragraph("&bull; Any manual offline tampering permanently breaks verification.", bullet_style)
    ]

    sec2 = [
        Paragraph("<b>3. Automated Security Event Logging</b>", body_bold),
        Spacer(1, 4),
        Paragraph("&bull; All spoof attempts, quality rejections, and attendance events are committed to SQLite.", bullet_style),
        Paragraph("&bull; Full audit trail for administrators and faculty review.", bullet_style),
        Spacer(1, 8),
        Paragraph("<b>4. Complete Modernization</b>", body_bold),
        Spacer(1, 4),
        Paragraph("&bull; Deprecated FaceNet and YOLO; unified under ArcFace 512-D embeddings.", bullet_style),
        Paragraph("&bull; High-efficiency OpenCV streaming overlays with real-time feedback.", bullet_style)
    ]

    t_sec = Table([[sec1, sec2]], colWidths=[350, 350])
    t_sec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, CARD_BORDER),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t_sec)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 7: CONCLUSION & SUMMARY
    # ==========================================
    story.extend(make_header("6. Summary & Viva Takeaways", "Key Highlights to State During Your Presentation"))

    summary_items = [
        Paragraph("<b>1. Problem Solved:</b> Replaces 15-minute manual roll calls and proxy-vulnerable cards with automated, proxy-proof, 10-second batch biometric scans.", bullet_style),
        Paragraph("<b>2. Winning Model Pair:</b> <b>OpenCV YuNet</b> for 15ms 5-landmark face alignment + <b>InsightFace ArcFace</b> for 512-D angular margin biometric matching.", bullet_style),
        Paragraph("<b>3. Robust Defense:</b> Hardware-independent anti-spoofing (Moiré pattern rejection) + strict Section Validation + HMAC-SHA256 cryptographic signatures.", bullet_style),
        Paragraph("<b>4. Ready for Scale:</b> SQLite backend, vectorized multi-student matrix evaluation, and full audit logging.", bullet_style)
    ]

    t_sum = Table([[summary_items]], colWidths=[712])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#16A34A")),
        ('PADDING', (0, 0), (-1, -1), 16),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 30))

    thank_you_style = ParagraphStyle(
        'TY',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Thank You &bull; Questions & Discussion", thank_you_style))

    doc.build(story)
    print(f"Presentation PDF successfully created at: {pdf_path.resolve()}")

if __name__ == "__main__":
    create_presentation_pdf()
