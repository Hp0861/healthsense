"""
explanation_engine.py – Generates safe, non-diagnostic explanations
for individual test results.

STRICT RULES (healthcare safety):
  ✗  No diagnosis
  ✗  No medical advice
  ✗  No panic language ("serious", "dangerous", "cancer", etc.)
  ✓  Factual comparisons to reported reference range
  ✓  Neutral, calm language
  ✓  Always include the informational disclaimer
"""

from typing import Optional

DISCLAIMER = (
    "⚕️ This information is for educational purposes only. "
    "Please consult a qualified doctor or healthcare professional "
    "for personalised medical advice."
)

# ─────────────────────────────────────────────────────────
# Per-test educational context (India-relevant tests)
# ─────────────────────────────────────────────────────────

_TEST_INFO: dict = {
    # CBC
    "haemoglobin":        "Haemoglobin carries oxygen in the blood.",
    "hb":                 "Haemoglobin carries oxygen in the blood.",
    "wbc":                "White blood cells are part of the immune system.",
    "total wbc count":    "White blood cells are part of the immune system.",
    "platelet":           "Platelets help the blood to clot.",
    "platelet count":     "Platelets help the blood to clot.",
    "pcv":                "PCV (Haematocrit) measures the proportion of red blood cells.",
    "haematocrit":        "PCV (Haematocrit) measures the proportion of red blood cells.",
    "rbc count":          "Red blood cells carry oxygen throughout the body.",
    "mcv":                "MCV reflects the average size of red blood cells.",
    "mch":                "MCH reflects the average haemoglobin content per red blood cell.",
    "mchc":               "MCHC measures the haemoglobin concentration in red blood cells.",
    "neutrophils":        "Neutrophils are a type of white blood cell involved in immunity.",
    "lymphocytes":        "Lymphocytes are white blood cells involved in immune response.",
    # Biochemistry
    "blood glucose":      "Blood glucose measures sugar levels in the blood.",
    "blood glucose (f)":  "Fasting blood glucose measures sugar levels after fasting.",
    "serum creatinine":   "Creatinine is a waste product filtered by the kidneys.",
    "blood urea":         "Urea is a waste product related to protein metabolism.",
    "sgpt":               "SGPT (ALT) is an enzyme related to liver function.",
    "sgot":               "SGOT (AST) is an enzyme related to liver and heart function.",
    "alt":                "ALT is an enzyme related to liver function.",
    "ast":                "AST is an enzyme related to liver and heart function.",
    "total cholesterol":  "Cholesterol is a fatty substance found in the blood.",
    "hdl cholesterol":    "HDL is often referred to as 'good' cholesterol.",
    "ldl cholesterol":    "LDL is often referred to as 'bad' cholesterol.",
    "triglycerides":      "Triglycerides are a type of fat found in the blood.",
    "serum sodium":       "Sodium is an electrolyte that helps regulate fluid balance.",
    "serum potassium":    "Potassium is an electrolyte important for heart and muscle function.",
    # Thyroid
    "tsh":                "TSH (Thyroid Stimulating Hormone) regulates thyroid function.",
    "t3":                 "T3 is a hormone produced by the thyroid gland.",
    "t4":                 "T4 is the main hormone produced by the thyroid gland.",
    # Vitamins
    "vitamin d":          "Vitamin D supports bone health and immune function.",
    "vitamin b12":        "Vitamin B12 is important for nerve function and red blood cell formation.",
    "iron":               "Iron is essential for haemoglobin production.",
    "ferritin":           "Ferritin is a protein that stores iron in the body.",
    # Diabetes
    "hba1c":              "HbA1c reflects average blood sugar levels over the past 2–3 months.",
    "fasting glucose":    "Fasting glucose measures blood sugar after a period of fasting.",
}


def _lookup_info(test_name: str) -> str:
    """Return a short educational sentence about the test."""
    key = test_name.lower().strip()
    for k, v in _TEST_INFO.items():
        if k in key or key in k:
            return v
    return f"{test_name} is a parameter measured in the blood or body."


# ─────────────────────────────────────────────────────────
# Core explanation builder
# ─────────────────────────────────────────────────────────

def generate_explanation(
    test_name: str,
    value: Optional[str],
    unit: Optional[str],
    range_low: Optional[str],
    range_high: Optional[str],
    flag: str,
) -> str:
    """
    Build a safe, informational explanation string.
    """
    info = _lookup_info(test_name)
    unit_str = f" {unit}" if unit else ""

    if not value:
        return f"{info}\n\nNo value was detected for this test. {DISCLAIMER}"

    # ── Compose range description ────────────────────────────
    if range_low and range_high:
        range_desc = f"The reference range is {range_low}–{range_high}{unit_str}."
    elif range_high:
        range_desc = f"The reference value is less than {range_high}{unit_str}."
    elif range_low:
        range_desc = f"The reference value is greater than {range_low}{unit_str}."
    else:
        range_desc = "No reference range was found in the report."

    # ── Compose flag sentence ────────────────────────────────
    if flag == "HIGH":
        flag_sentence = (
            f"Your recorded value of {value}{unit_str} is higher than the normal range. "
            "This may warrant a discussion with a healthcare professional."
        )
        emoji = "🔴"
    elif flag == "LOW":
        flag_sentence = (
            f"Your recorded value of {value}{unit_str} is lower than the normal range. "
            "This may warrant a discussion with a healthcare professional."
        )
        emoji = "🔵"
    else:  # NORMAL
        flag_sentence = (
            f"Your recorded value of {value}{unit_str} is within the normal range. "
            "No immediate action appears necessary based on this value alone."
        )
        emoji = "🟢"

    explanation = (
        f"{emoji} **{test_name}**\n\n"
        f"{info}\n\n"
        f"{range_desc}\n\n"
        f"{flag_sentence}\n\n"
        f"_{DISCLAIMER}_"
    )
    return explanation


# ─────────────────────────────────────────────────────────
# Quick self-test
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(generate_explanation("Haemoglobin (Hb)", "10.2", "g/dL", "13.0", "17.0", "LOW"))
    print()
    print(generate_explanation("TSH", "5.8", "uIU/mL", "0.5", "5.0", "HIGH"))
    print()
    print(generate_explanation("Total Cholesterol", "210", "mg/dL", None, "200", "HIGH"))
