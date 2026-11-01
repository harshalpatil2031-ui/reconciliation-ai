"""FastAPI application shell shared by all project stages."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import db
from backend.config import config_sha
from backend.routers import analyze, audit, cases, events, ground, reports


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await db.open_pool()
    try:
        yield
    finally:
        await db.close_pool()


app = FastAPI(
    title="Reconciliation AI API",
    version="0.1.0",
    description="Evidence-led, human-reviewed compensation assessment QA.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for route_group in (cases, ground, analyze, reports, audit, events):
    app.include_router(route_group.router)


@app.get("/health", tags=["health"], responses={200: {"description": "API and database health"}})
async def health() -> dict[str, object]:
    try:
        database_available = await db.ping()
    except Exception:
        database_available = False
    return {"status": "ok", "db": database_available, "config_sha": config_sha()}
