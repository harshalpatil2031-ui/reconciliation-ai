"""Small localhost-only API for the interactive synthetic prototype demo."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import AsyncIterator, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "demo_cases.json"


def database_path() -> Path:
    return Path(os.environ.get("RECON_DEMO_DB", ROOT / "data" / "demo.sqlite3"))


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize() -> None:
    with connect() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS demo_reports (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                locale TEXT NOT NULL,
                form_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'NEEDS_HUMAN_REVIEW',
                review_note TEXT
            )"""
        )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize()
    yield


app = FastAPI(
    title="Reconciliation AI Local Demo API",
    version="0.1.0",
    description="Local synthetic prototype storage; not a production or pilot API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


class DemoForm(BaseModel):
    damaged_share_pct: int = Field(ge=0, le=100)
    water_depth_band: Literal["NONE", "ANKLE", "KNEE", "WAIST", "ABOVE_WAIST"]
    water_days: int = Field(ge=0, le=14)
    crop_stage: Literal["SOWN_ONLY", "VEGETATIVE", "FLOWERING", "PODDING_OR_MATURE"]
    note: str | None = Field(default=None, max_length=300)


class DemoReportIn(BaseModel):
    locale: Literal["mr", "en"]
    form: DemoForm


class ReviewIn(BaseModel):
    note: str = Field(min_length=1, max_length=300)


@app.get("/demo/cases")
def get_cases() -> list[dict[str, object]]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


@app.get("/demo/reports")
def get_reports() -> list[dict[str, object]]:
    with connect() as connection:
        rows = connection.execute("SELECT * FROM demo_reports ORDER BY created_at DESC").fetchall()
    return [serialize_report(row) for row in rows]


def serialize_report(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "locale": row["locale"],
        "form": json.loads(row["form_json"]),
        "status": row["status"],
        "review_note": row["review_note"],
        "official_pct": 20,
        "satellite_style_pct": 40,
        "explanation": dynamic_explanation(json.loads(row["form_json"])),
        "data_status": "synthetic demo example",
    }


def dynamic_explanation(form: dict[str, object]) -> str:
    farmer_pct = int(form["damaged_share_pct"])
    difference = abs(farmer_pct - 40)
    if difference >= 25:
        return f"Farmer report ({farmer_pct}%) differs from the illustrative satellite-style value (40%); ask a person to compare the sources."
    return f"Farmer report ({farmer_pct}%) and the illustrative satellite-style value (40%) are shown side by side for human review."


@app.post("/demo/reports", status_code=201)
def create_report(report: DemoReportIn) -> dict[str, object]:
    report_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()
    form = report.form.model_dump()
    with connect() as connection:
        connection.execute(
            "INSERT INTO demo_reports (id, created_at, locale, form_json) VALUES (?, ?, ?, ?)",
            (report_id, created_at, report.locale, json.dumps(form, ensure_ascii=False)),
        )
    return {
        "id": report_id,
        "created_at": created_at,
        "locale": report.locale,
        "form": form,
        "status": "NEEDS_HUMAN_REVIEW",
        "review_note": None,
        "official_pct": 20,
        "satellite_style_pct": 40,
        "explanation": dynamic_explanation(form),
        "data_status": "synthetic demo example",
    }


@app.post("/demo/reports/{report_id}/review")
def review_report(report_id: str, review: ReviewIn) -> dict[str, object]:
    with connect() as connection:
        result = connection.execute(
            "UPDATE demo_reports SET status='REVIEWED_FOR_DEMO', review_note=? WHERE id=?",
            (review.note, report_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Demo report not found")
        row = connection.execute("SELECT * FROM demo_reports WHERE id=?", (report_id,)).fetchone()
    return serialize_report(row)


@app.delete("/demo/reports", status_code=204)
def reset_reports() -> None:
    with connect() as connection:
        connection.execute("DELETE FROM demo_reports")
