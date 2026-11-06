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

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "demo_cases.json"
DEMO_OFFICIAL_PCT = 20
DEMO_SATELLITE_STYLE_PCT = 40


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
    form = json.loads(row["form_json"])
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "locale": row["locale"],
        "form": form,
        "status": row["status"],
        "review_note": row["review_note"],
        "official_pct": DEMO_OFFICIAL_PCT,
        "satellite_style_pct": DEMO_SATELLITE_STYLE_PCT,
        "explanation": dynamic_explanation(
            official_pct=DEMO_OFFICIAL_PCT,
            satellite_style_pct=DEMO_SATELLITE_STYLE_PCT,
            farmer_report_pct=form["damaged_share_pct"],
        ),
        "data_status": "synthetic demo example",
    }


def dynamic_explanation(
    *,
    official_pct: int | None,
    satellite_style_pct: int | None,
    farmer_report_pct: int | None,
) -> str:
    """Explain the displayed demo values without interpreting missing evidence as zero."""
    values = {
        "official assessment": official_pct,
        "satellite-style example": satellite_style_pct,
        "farmer report": farmer_report_pct,
    }
    missing = [name for name, value in values.items() if value is None]
    if missing:
        unknown = ", ".join(missing)
        return (
            f"Insufficient evidence: {unknown} is unknown. No missing value is inferred; "
            "a person must review the available evidence."
        )

    shown = ", ".join(f"{name} ({value}%)" for name, value in values.items())
    present_values = [value for value in values.values() if value is not None]
    spread = max(present_values) - min(present_values)
    if spread >= 25:
        return (
            f"Synthetic demo values: {shown}. They span {spread} percentage points; "
            "ask a person to compare the sources. This is not an eligibility decision."
        )
    return (
        f"Synthetic demo values: {shown}. They are shown side by side for human review; "
        "this is not an eligibility decision."
    )


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
        "official_pct": DEMO_OFFICIAL_PCT,
        "satellite_style_pct": DEMO_SATELLITE_STYLE_PCT,
        "explanation": dynamic_explanation(
            official_pct=DEMO_OFFICIAL_PCT,
            satellite_style_pct=DEMO_SATELLITE_STYLE_PCT,
            farmer_report_pct=form["damaged_share_pct"],
        ),
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


@app.delete("/demo/reports", status_code=204, response_model=None)
def reset_reports() -> None:
    with connect() as connection:
        connection.execute("DELETE FROM demo_reports")
