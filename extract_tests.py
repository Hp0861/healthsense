"""
extract_tests.py – Parse raw OCR text and extract structured test results.
"""

import re
from typing import Any, Dict, List, Optional


# ── Patterns – named group for test name is 'n' throughout ────────────────

# Pattern A: "Name   12.3   mg/dL   10.0 - 20.0"
_PATTERN_A = re.compile(
    r"^(?P<n>[A-Za-z][A-Za-z0-9 /()%\-\.]+?)\s+"
    r"(?P<value>\d+\.?\d*)\s+"
    r"(?P<unit>[A-Za-z/%][A-Za-z0-9/%\.]*)\s+"
    r"(?P<low>\d+\.?\d*)\s*[-]\s*(?P<high>\d+\.?\d*)",
    re.IGNORECASE,
)

# Pattern B: "Name   12.3   mg/dL   < 200"
_PATTERN_B = re.compile(
    r"^(?P<n>[A-Za-z][A-Za-z0-9 /()%\-\.]+?)\s+"
    r"(?P<value>\d+\.?\d*)\s+"
    r"(?P<unit>[A-Za-z/%][A-Za-z0-9/%\.]*)\s+"
    r"<\s*(?P<high>\d+\.?\d*)",
    re.IGNORECASE,
)

# Pattern C: "Name   12.3   mg/dL   > 40"
_PATTERN_C = re.compile(
    r"^(?P<n>[A-Za-z][A-Za-z0-9 /()%\-\.]+?)\s+"
    r"(?P<value>\d+\.?\d*)\s+"
    r"(?P<unit>[A-Za-z/%][A-Za-z0-9/%\.]*)\s+"
    r">\s*(?P<low>\d+\.?\d*)",
    re.IGNORECASE,
)

# Pattern D: "Name   12.3   mg/dL"  (no range)
_PATTERN_D = re.compile(
    r"^(?P<n>[A-Za-z][A-Za-z0-9 /()%\-\.]+?)\s+"
    r"(?P<value>\d+\.?\d*)\s+"
    r"(?P<unit>[A-Za-z/%][A-Za-z0-9/%\.]*)\s*$",
    re.IGNORECASE,
)

_SKIP = re.compile(
    r"(patient|date|name|age|sex|gender|report|doctor|lab|sample|refer|sign"
    r"|barcode|page|address|tel|phone|fax|email|hospital|clinic|result"
    r"|test\s+name|reference\s+range|unit|value|parameter"
    r"|investigation|collected|received)",
    re.IGNORECASE,
)

_NOISE = re.compile(r"^[-=*_\s|]+$")


def _safe_group(m, grp):
    try:
        v = m.group(grp)
        return v.strip() if v else None
    except IndexError:
        return None


def _flag(value_str, low_str, high_str):
    if not value_str:
        return "NORMAL"
    try:
        v = float(value_str)
        if low_str and high_str:
            if v < float(low_str): return "LOW"
            if v > float(high_str): return "HIGH"
        elif high_str:
            if v > float(high_str): return "HIGH"
        elif low_str:
            if v < float(low_str): return "LOW"
    except ValueError:
        pass
    return "NORMAL"


def parse_test_results(raw_text: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen = set()

    for line in raw_text.splitlines():
        line = line.strip()
        if not line or _NOISE.match(line) or _SKIP.search(line):
            continue

        entry = None
        for pat in [_PATTERN_A, _PATTERN_B, _PATTERN_C, _PATTERN_D]:
            m = pat.match(line)
            if not m:
                continue
            raw_name = _safe_group(m, "n")
            if not raw_name:
                continue
            name = re.sub(r"\s+", " ", raw_name.strip().rstrip(".:- "))
            if len(name) < 2:
                continue

            value = _safe_group(m, "value")
            unit  = _safe_group(m, "unit")
            low   = _safe_group(m, "low")
            high  = _safe_group(m, "high")

            if low and high:     rng = f"{low} - {high}"
            elif high:           rng = f"< {high}"
            elif low:            rng = f"> {low}"
            else:                rng = None

            entry = dict(
                test_name=name, value=value, unit=unit,
                range_low=low, range_high=high, range_text=rng,
                flag=_flag(value, low, high),
            )
            break

        if not entry:
            continue
        key = entry["test_name"].lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(entry)

    return results


if __name__ == "__main__":
    SAMPLE = """
    Haemoglobin (Hb)        10.2     g/dL        13.0 - 17.0
    Total WBC Count         11500    cells/cumm  4000 - 11000
    Blood Glucose (F)       105      mg/dL       70 - 100
    Total Cholesterol       210      mg/dL       < 200
    HDL Cholesterol         45       mg/dL       > 40
    TSH                     5.8      uIU/mL      0.5 - 5.0
    """
    for r in parse_test_results(SAMPLE):
        print(r)
