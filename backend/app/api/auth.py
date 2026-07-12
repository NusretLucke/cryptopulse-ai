"""Authentifizierung - API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt

from app.core.config import settings
from app.db.database import get_db
from app.models.database import User, AuditLog
from app.schemas.schemas import UserCreate, UserLogin, TokenResponse, UserSettings, BinanceCredentials
from app.utils.security import encrypt_api_key, decrypt_api_key

router = APIRouter()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Neuen Benutzer registrieren"""
    # Prüfen ob Username existiert
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username bereits vergeben")

    # Prüfen ob Email existiert
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email bereits registriert")

    # User erstellen
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        created_at=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()

    # Audit-Log
    audit = AuditLog(user_id=user.id, action="register", details={"username": user.username})
    db.add(audit)

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token, user_id=user.id, username=user.username)


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Benutzer anmelden"""
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")

    audit = AuditLog(user_id=user.id, action="login")
    db.add(audit)

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token, user_id=user.id, username=user.username)


@router.put("/settings")
async def update_settings(settings_data: UserSettings, user_id: int, db: AsyncSession = Depends(get_db)):
    """Benutzereinstellungen aktualisieren"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")

    if settings_data.preferred_currency:
        user.preferred_currency = settings_data.preferred_currency
    if settings_data.risk_tolerance:
        user.risk_tolerance = settings_data.risk_tolerance
    if settings_data.language:
        user.language = settings_data.language

    return {"message": "Einstellungen aktualisiert"}


@router.post("/binance")
async def connect_binance(creds: BinanceCredentials, user_id: int, db: AsyncSession = Depends(get_db)):
    """Binance API verbinden (verschlüsselt)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")

    user.binance_api_key_encrypted = encrypt_api_key(creds.api_key)
    user.binance_secret_key_encrypted = encrypt_api_key(creds.secret_key)
    user.is_binance_connected = True

    audit = AuditLog(user_id=user_id, action="binance_connect")
    db.add(audit)

    return {"message": "Binance erfolgreich verbunden", "status": "connected"}


@router.post("/binance/disconnect")
async def disconnect_binance(user_id: int, db: AsyncSession = Depends(get_db)):
    """Binance API trennen"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")

    user.binance_api_key_encrypted = None
    user.binance_secret_key_encrypted = None
    user.is_binance_connected = False

    audit = AuditLog(user_id=user_id, action="binance_disconnect")
    db.add(audit)

    return {"message": "Binance getrennt"}