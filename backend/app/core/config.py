from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "CryptoPulse AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database — automatisch PostgreSQL auf Render, SQLite lokal
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./cryptopulse.db"
    )
    # Render gibt postgres://, SQLAlchemy braucht postgresql+asyncpg://
    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # Redis (optional — auf Render deaktiviert)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cryptopulse-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Binance API
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    BINANCE_TESTNET: bool = True

    # Fernet encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "cryptopulse-encryption-key-32bytes!")

    # Market data
    UPDATE_INTERVAL_SECONDS: int = 300
    MAX_HISTORY_DAYS: int = 30
    TOP_COINS: int = 50

    # AI/ML
    MODEL_PATH: str = "data/models"
    CONFIDENCE_THRESHOLD: float = 0.6
    MIN_TRADES_FOR_LEARNING: int = 10

    # Risk Management
    MAX_POSITION_SIZE_PERCENT: float = 10.0
    MAX_DAILY_LOSS_PERCENT: float = 5.0
    STOP_LOSS_DEFAULT_PERCENT: float = 5.0
    TAKE_PROFIT_DEFAULT_PERCENT: float = 15.0

    # CORS —在生产中 auf die echte Domain setzen
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

    class Config:
        env_file = ".env"


settings = Settings()