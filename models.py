"""
models.py – Pydantic schemas used by FastAPI endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    message: str = ""


# ──────────────────────────────────────────────
# Profiles
# ──────────────────────────────────────────────

class ProfileCreate(BaseModel):
    user_id: int
    name: str = Field(..., min_length=1, max_length=100)
    relation: str = "Self"          # Self / Father / Mother / Child / Other
    age: Optional[int] = None


class ProfileOut(BaseModel):
    id: int
    user_id: int
    name: str
    relation: str
    age: Optional[int]
    created_at: str


# ──────────────────────────────────────────────
# Test Results
# ──────────────────────────────────────────────

class TestResultOut(BaseModel):
    id: int
    report_id: int
    test_name: str
    value: Optional[str]
    unit: Optional[str]
    range_low: Optional[str]
    range_high: Optional[str]
    range_text: Optional[str]
    flag: str
    explanation: Optional[str] = None


# ──────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────

class ReportOut(BaseModel):
    id: int
    profile_id: int
    file_path: str
    report_date: Optional[str]
    created_at: str
    test_results: List[TestResultOut] = []
