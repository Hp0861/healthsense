"""
routes.py – All FastAPI route handlers for HealthSense.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.auth import login_user, register_user
from backend.database import get_connection
from backend.models import (
    AuthResponse,
    LoginRequest,
    ProfileCreate,
    ProfileOut,
    RegisterRequest,
    ReportOut,
    TestResultOut,
)
from explain.explanation_engine import generate_explanation
from ocr.ocr_engine import extract_text_from_image
from parser.extract_tests import parse_test_results

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────

@router.post("/auth/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    success, msg = register_user(req.username, req.password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return AuthResponse(success=True, message=msg)


@router.post("/auth/login", response_model=AuthResponse)
def login(req: LoginRequest):
    success, user_id, msg = login_user(req.username, req.password)
    if not success:
        raise HTTPException(status_code=401, detail=msg)
    return AuthResponse(success=True, user_id=user_id, username=req.username, message=msg)


# ─────────────────────────────────────────────
# Profile routes
# ─────────────────────────────────────────────

@router.post("/profiles", response_model=ProfileOut)
def create_profile(req: ProfileCreate):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO profiles (user_id, name, relation, age) VALUES (?, ?, ?, ?)",
            (req.user_id, req.name, req.relation, req.age),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _profile_row(row)
    finally:
        conn.close()


@router.get("/profiles/{user_id}", response_model=List[ProfileOut])
def get_profiles(user_id: int):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM profiles WHERE user_id = ? ORDER BY id", (user_id,)
        ).fetchall()
        return [_profile_row(r) for r in rows]
    finally:
        conn.close()


def _profile_row(row) -> ProfileOut:
    return ProfileOut(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        relation=row["relation"],
        age=row["age"],
        created_at=row["created_at"],
    )


# ─────────────────────────────────────────────
# Report upload + OCR + parse + save
# ─────────────────────────────────────────────

@router.post("/reports/upload")
async def upload_report(
    profile_id: int = Form(...),
    report_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    # 1. Save file
    ext = Path(file.filename).suffix or ".png"
    dest = UPLOAD_DIR / f"profile_{profile_id}_{file.filename}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 2. OCR
    raw_text = extract_text_from_image(str(dest))

    # 3. Parse
    tests = parse_test_results(raw_text)

    # 4. Save report
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO reports (profile_id, file_path, report_date) VALUES (?, ?, ?)",
            (profile_id, str(dest), report_date),
        )
        report_id = cur.lastrowid

        results_out = []
        for t in tests:
            conn.execute(
                """INSERT INTO test_results
                   (report_id, test_name, value, unit, range_low, range_high, range_text, flag)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    report_id,
                    t["test_name"],
                    t.get("value"),
                    t.get("unit"),
                    t.get("range_low"),
                    t.get("range_high"),
                    t.get("range_text"),
                    t.get("flag", "NORMAL"),
                ),
            )
            explanation = generate_explanation(
                t["test_name"],
                t.get("value"),
                t.get("unit"),
                t.get("range_low"),
                t.get("range_high"),
                t.get("flag", "NORMAL"),
            )
            results_out.append(
                {
                    "test_name": t["test_name"],
                    "value": t.get("value"),
                    "unit": t.get("unit"),
                    "range_text": t.get("range_text"),
                    "flag": t.get("flag", "NORMAL"),
                    "explanation": explanation,
                }
            )

        conn.commit()
        return {
            "success": True,
            "report_id": report_id,
            "raw_text_preview": raw_text[:500],
            "tests_found": len(tests),
            "results": results_out,
        }
    finally:
        conn.close()


# ─────────────────────────────────────────────
# Dashboard / history routes
# ─────────────────────────────────────────────

@router.get("/reports/profile/{profile_id}", response_model=List[ReportOut])
def get_reports_for_profile(profile_id: int):
    conn = get_connection()
    try:
        reports = conn.execute(
            "SELECT * FROM reports WHERE profile_id = ? ORDER BY created_at DESC",
            (profile_id,),
        ).fetchall()
        result = []
        for rpt in reports:
            tests = conn.execute(
                "SELECT * FROM test_results WHERE report_id = ?", (rpt["id"],)
            ).fetchall()
            test_list = []
            for t in tests:
                explanation = generate_explanation(
                    t["test_name"],
                    t["value"],
                    t["unit"],
                    t["range_low"],
                    t["range_high"],
                    t["flag"],
                )
                test_list.append(
                    TestResultOut(
                        id=t["id"],
                        report_id=t["report_id"],
                        test_name=t["test_name"],
                        value=t["value"],
                        unit=t["unit"],
                        range_low=t["range_low"],
                        range_high=t["range_high"],
                        range_text=t["range_text"],
                        flag=t["flag"],
                        explanation=explanation,
                    )
                )
            result.append(
                ReportOut(
                    id=rpt["id"],
                    profile_id=rpt["profile_id"],
                    file_path=rpt["file_path"],
                    report_date=rpt["report_date"],
                    created_at=rpt["created_at"],
                    test_results=test_list,
                )
            )
        return result
    finally:
        conn.close()


@router.get("/reports/{report_id}/results")
def get_report_results(report_id: int):
    conn = get_connection()
    try:
        tests = conn.execute(
            "SELECT * FROM test_results WHERE report_id = ?", (report_id,)
        ).fetchall()
        results = []
        for t in tests:
            explanation = generate_explanation(
                t["test_name"],
                t["value"],
                t["unit"],
                t["range_low"],
                t["range_high"],
                t["flag"],
            )
            results.append(
                {
                    "id": t["id"],
                    "test_name": t["test_name"],
                    "value": t["value"],
                    "unit": t["unit"],
                    "range_text": t["range_text"],
                    "flag": t["flag"],
                    "explanation": explanation,
                }
            )
        return {"report_id": report_id, "results": results}
    finally:
        conn.close()


@router.delete("/profiles/{profile_id}")
def delete_profile(profile_id: int):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()
        return {"success": True, "message": "Profile deleted."}
    finally:
        conn.close()
