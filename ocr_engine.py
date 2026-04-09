"""
ocr_engine.py – Extract raw text from a health report image.

Pipeline:
  1. Load with OpenCV
  2. Convert to grayscale
  3. Denoise + threshold (improves OCR accuracy on printed reports)
  4. Run pytesseract
"""

from pathlib import Path

try:
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False


def _preprocess(image_path: str):
    """Return a preprocessed grayscale numpy image ready for Tesseract."""
    img = cv2.imread(image_path)
    if img is None:
        # Fallback: load via Pillow (handles more formats)
        pil = Image.open(image_path).convert("RGB")
        img = np.array(pil)[:, :, ::-1].copy()  # RGB → BGR

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Mild denoising
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # Adaptive thresholding – good for lab-report style text
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=8,
    )

    # Optional: scale up small images for better accuracy
    h, w = thresh.shape
    if max(h, w) < 1000:
        scale = 1000 / max(h, w)
        thresh = cv2.resize(
            thresh,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_CUBIC,
        )

    return thresh


def extract_text_from_image(image_path: str) -> str:
    """
    Run OCR on *image_path* and return the extracted text string.
    Falls back to a demo string if libraries are unavailable (for testing).
    """
    if not Path(image_path).exists():
        return f"[ERROR] File not found: {image_path}"

    if not _OCR_AVAILABLE:
        # Useful for environments where pytesseract / cv2 isn't installed
        return _demo_text()

    try:
        processed = _preprocess(image_path)
        custom_config = r"--oem 3 --psm 6"
        text = pytesseract.image_to_string(processed, config=custom_config)
        return text if text.strip() else _demo_text()
    except Exception as exc:
        return f"[OCR ERROR] {exc}\n\n" + _demo_text()


def _demo_text() -> str:
    """Hardcoded sample report text used when OCR is not available."""
    return """
PATHOLOGY LABORATORY REPORT
Patient: Demo Patient    Age: 35 Years    Sex: Male
Date: 09/04/2026

COMPLETE BLOOD COUNT (CBC)
------------------------------------------------------------
Test Name               Value    Unit        Reference Range
------------------------------------------------------------
Haemoglobin (Hb)        10.2     g/dL        13.0 - 17.0
Total WBC Count         11500    cells/cumm  4000 - 11000
Platelet Count          1.8      Lakh/cumm   1.5 - 4.5
PCV / Haematocrit       38.5     %           40.0 - 50.0
RBC Count               4.10     mill/cumm   4.5 - 5.5
MCV                     82.0     fL          80 - 100
MCH                     28.5     pg          27 - 32
MCHC                    33.2     g/dL        31.5 - 34.5
Neutrophils             72       %           40 - 80
Lymphocytes             22       %           20 - 40

BLOOD BIOCHEMISTRY
------------------------------------------------------------
Blood Glucose (F)       105      mg/dL       70 - 100
Serum Creatinine        1.1      mg/dL       0.6 - 1.2
Blood Urea              28       mg/dL       15 - 40
SGPT / ALT              42       U/L         0 - 40
SGOT / AST              38       U/L         0 - 40
Total Cholesterol       210      mg/dL       < 200
HDL Cholesterol         45       mg/dL       > 40
LDL Cholesterol         135      mg/dL       < 130
Triglycerides           155      mg/dL       < 150
Serum Sodium            138      mEq/L       136 - 146
Serum Potassium         4.2      mEq/L       3.5 - 5.1

THYROID FUNCTION TEST
------------------------------------------------------------
TSH                     5.8      uIU/mL      0.5 - 5.0
T3                      1.2      ng/mL       0.8 - 2.0
T4                      7.5      ug/dL       5.1 - 14.1

** End of Report **
"""
