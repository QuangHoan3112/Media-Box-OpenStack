import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.db import get_connection


router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
password_hasher = PasswordHasher()

ALGORITHM = "HS256"
TOKEN_LIFETIME_MINUTES = 60


def get_jwt_secret():
    path = Path(
        os.getenv(
            "MEDIABOX_JWT_SECRET_FILE",
            str(Path.home() / ".config/mediabox/jwt_secret"),
        )
    )
    secret = path.read_text().strip()

    if len(secret) < 32:
        raise RuntimeError("JWT secret is too short")

    return secret


def invalid_credentials():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_access_token(user_id: int):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_LIFETIME_MINUTES),
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=ALGORITHM,
    )


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("Invalid user ID")

    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise invalid_credentials()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, email, display_name,
                       role, is_active
                FROM app_users
                WHERE id = %s
                """,
                (user_id,),
            )
            user = cur.fetchone()

    if not user or not user["is_active"]:
        raise invalid_credentials()

    return user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, password_hash, is_active
                FROM app_users
                WHERE username = %s OR email = %s
                LIMIT 1
                """,
                (form_data.username, form_data.username),
            )
            user = cur.fetchone()

    if not user or not user["is_active"]:
        raise invalid_credentials()

    try:
        password_hasher.verify(
            user["password_hash"],
            form_data.password,
        )
    except (VerificationError, InvalidHashError):
        raise invalid_credentials()

    token = create_access_token(user["id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_LIFETIME_MINUTES * 60,
    }


@router.get("/me")
def current_user(user=Depends(get_current_user)):
    return user
