import asyncio
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, Integer, String
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class SearchRecord(Base):
    __tablename__ = "searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    origin: Mapped[str] = mapped_column(String(3), index=True)
    destination: Mapped[str] = mapped_column(String(3), index=True)
    trip_type: Mapped[str] = mapped_column(String(10))
    depart_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    adults: Mapped[int] = mapped_column(Integer)
    children: Mapped[int] = mapped_column(Integer, default=0)
    infants: Mapped[int] = mapped_column(Integer, default=0)
    cabin: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3))
    result_count: Mapped[int] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)


class SearchResultRecord(Base):
    """Search results in the database instead of one task's memory: any backend task can serve the detail page,
    and the same search within the TTL is answered from here instead of calling Sabre again."""

    __tablename__ = "search_results"

    search_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    query_key: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    # Naive UTC: MySQL DATETIME and SQLite both drop the timezone.
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


def make_engine(url: str) -> AsyncEngine:
    if url.endswith(":memory:"):
        # Each SQLite connection gets its own in-memory database, so share one.
        return create_async_engine(url, poolclass=StaticPool, connect_args={"check_same_thread": False})
    if url.startswith("sqlite"):
        return create_async_engine(url)
    # A server database (MySQL on RDS) closes idle connections: test each one before use and recycle hourly.
    return create_async_engine(url, pool_pre_ping=True, pool_recycle=3600)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_tables(engine: AsyncEngine) -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except DBAPIError:
        # Two tasks starting together on an empty database race to create the same table; the loser tries again
        # and finds it there.
        await asyncio.sleep(1)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
