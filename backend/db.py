"""Async PostgreSQL pool and transaction helper."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

pool: asyncpg.Pool | None = None


async def _init_connection(connection: asyncpg.Connection) -> None:
    await connection.execute("SET TIME ZONE 'UTC'")


async def open_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL", "postgresql://reconciliation:reconciliation@localhost:5432/reconciliation"),
            min_size=1,
            max_size=10,
            init=_init_connection,
            command_timeout=30,
        )
    return pool


async def close_pool() -> None:
    global pool
    if pool is not None:
        await pool.close()
        pool = None


@asynccontextmanager
async def transaction() -> AsyncIterator[asyncpg.Connection]:
    """Yield a UTC connection in a transaction; roll back on any exception."""
    active_pool = pool or await open_pool()
    async with active_pool.acquire() as connection:
        async with connection.transaction():
            yield connection


async def ping() -> bool:
    active_pool = pool or await open_pool()
    async with active_pool.acquire() as connection:
        await connection.execute("SET TIME ZONE 'UTC'")
        return await connection.fetchval("SELECT 1") == 1
