import cv2
import numpy as np


class LivenessDetector:
    """
    Biometric Anti-Spoofing & Liveness Detection Engine
    Defends against:
      1. Printed 2D paper photographs
      2. Digital smartphone / tablet / laptop display screens (moiré & pixel grids)
      3. Flat static cutouts
    """

    def __init__(self, texture_threshold=35.0, liveness_threshold=0.55):
        self.texture_threshold = texture_threshold
        self.liveness_threshold = liveness_threshold

    def evaluate_texture(self, face_crop):
        """
        Analyzes micro-texture and frequency characteristics using the Laplacian operator.
        Screens and printed papers exhibit either low variance (blur) or spiky high frequencies.
        """
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        # Healthy live human face typically has variance in [40, 1500] depending on lighting
        if variance < self.texture_threshold:
            return False, variance, "Insufficient texture depth (Flat / Blurry image)"
        elif variance > 3000.0:
            # Extremely sharp high-frequency noise is typical of digital screen pixel grid / moire
            return False, variance, "Unnatural high-frequency noise (Possible Screen Moiré)"
        return True, variance, "Natural facial skin texture"

    def evaluate_color_chroma(self, face_crop):
        """
        Analyzes human skin tone characteristics in YCrCb and HSV color spaces.
        Digital phone screens alter skin chroma and exhibit specular glass reflections.
        """
        ycrcb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2YCrCb)
        _, cr, cb = cv2.split(ycrcb)

        # Standard human skin locus in YCrCb: Cr in [130, 175], Cb in [75, 130]
        skin_mask = (cr >= 125) & (cr <= 180) & (cb >= 70) & (cb <= 135)
        skin_ratio = np.sum(skin_mask) / float(face_crop.shape[0] * face_crop.shape[1])

        # HSV saturation analysis (screens often over-saturate color balance)
        hsv = cv2.cvtColor(face_crop, cv2.COLOR_BGR2HSV)
        _, s, v = cv2.split(hsv)
        mean_saturation = np.mean(s)

        # Check for harsh specular glass glare (pure white blown-out clusters common on phone screens)
        glare_mask = (v > 250) & (s < 20)
        glare_ratio = np.sum(glare_mask) / float(face_crop.shape[0] * face_crop.shape[1])

        if glare_ratio > 0.12:
            return False, 0.25, "Severe glass reflection / screen glare detected"

        if skin_ratio < 0.20:
            return False, 0.35, "Abnormal chromatic distribution for biological skin"

        return True, float(skin_ratio), "Normal biological skin chromaticity"

    def evaluate_gradient_depth(self, face_crop):
        """
        Evaluates 3D facial depth gradients around facial features (nose bridge, cheekbones).
        Flat 2D surfaces lack natural biological gradient transitions.
        """
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(gx ** 2 + gy ** 2)
        mean_grad = np.mean(mag)

        if mean_grad < 5.0:
            return False, float(mean_grad), "Low geometric gradient depth"
        return True, float(mean_grad), "Healthy geometric depth"

    def check_liveness(self, face_crop):
        """
        Performs multi-criteria liveness assessment on a cropped face.
        Returns:
            is_live (bool): True if verified live human, False if suspected spoof.
            confidence (float): Score between 0.0 and 100.0.
            reason (str): Assessment details.
        """
        if face_crop is None or face_crop.size == 0 or face_crop.shape[0] < 30 or face_crop.shape[1] < 30:
            return False, 0.0, "Invalid or too small face crop"

        # 1. Texture check
        live_tex, tex_score, tex_msg = self.evaluate_texture(face_crop)

        # 2. Chromaticity check
        live_col, col_score, col_msg = self.evaluate_color_chroma(face_crop)

        # 3. Depth gradients
        live_grad, grad_score, grad_msg = self.evaluate_gradient_depth(face_crop)

        # Aggregate weighted score
        score = 0.0
        if live_tex: score += 0.40
        if live_col: score += 0.35
        if live_grad: score += 0.25

        confidence = round(score * 100.0, 1)

        if score >= self.liveness_threshold:
            return True, confidence, "Live Human Face Verified"
        else:
            reasons = []
            if not live_tex: reasons.append(tex_msg)
            if not live_col: reasons.append(col_msg)
            if not live_grad: reasons.append(grad_msg)
            return False, confidence, f"Suspected Spoof: {'; '.join(reasons)}"


# Module-level singleton instance
_detector = LivenessDetector()


def evaluate_liveness(face_crop):
    return _detector.check_liveness(face_crop)


def evaluate_face_quality(face_crop, min_size=70, blur_thresh=150.0, min_b=40.0, max_b=225.0, min_contrast=25.0):
    """
    Step 4 Quality Gate: Validates bounding-box dimensions, blur, brightness, and contrast.
    Returns:
        passed (bool): Whether the face crop qualifies for biometric recognition.
        reason (str): Human-readable failure reason if rejected.
        metrics (dict): Numeric quality indicators.
    """
    if face_crop is None or face_crop.size == 0:
        return False, "EMPTY_CROP", {}

    h, w = face_crop.shape[:2]
    if w < min_size or h < min_size:
        return False, f"FACE_TOO_SMALL ({w}x{h} < {min_size}px)", {"width": w, "height": h}

    gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean_brightness = float(np.mean(gray))
    std_contrast = float(np.std(gray))

    metrics = {
        "width": w,
        "height": h,
        "sharpness": round(blur_score, 1),
        "brightness": round(mean_brightness, 1),
        "contrast": round(std_contrast, 1)
    }

    if blur_score < blur_thresh:
        return False, f"BLURRY_FACE (Sharpness {blur_score:.1f} < {blur_thresh})", metrics

    if mean_brightness < min_b:
        return False, f"LOW_LIGHT (Brightness {mean_brightness:.1f} < {min_b})", metrics

    if mean_brightness > max_b:
        return False, f"OVEREXPOSED (Brightness {mean_brightness:.1f} > {max_b})", metrics

    if std_contrast < min_contrast:
        return False, f"LOW_CONTRAST (Contrast {std_contrast:.1f} < {min_contrast})", metrics

    return True, "QUALITY_PASSED", metrics

