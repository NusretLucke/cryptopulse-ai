"""Datenbank-Setup und Session-Management"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.models.database import Base

# Async Engine — nutzt async_database_url für PostgreSQL-Kompatibilität
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    future=True,
)

# Session-Factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency für FastAPI-Endpunkte"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Datenbank initialisieren (Tabellen erstellen)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Verbindung schließen"""
    await engine.dispose()