"""
Poker Coach — FastAPI application entry point.
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db.session import engine
from app.db.models import Base
from app.api.routers import auth, tables, sessions, hands, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (dev convenience; use alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Poker Coach API",
    version="0.1.0",
    description=(
        "Poker hand analyzer + bankroll tracker. "
        "Advice is Monte Carlo + simplified ranges — NOT a Nash solver."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tables.router)
app.include_router(sessions.router)
app.include_router(hands.router)
app.include_router(stats.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "poker-coach"}
