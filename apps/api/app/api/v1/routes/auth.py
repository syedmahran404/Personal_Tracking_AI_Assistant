"""Auth: signup, login, refresh, logout."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.session import RefreshToken
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserPublic

router = APIRouter()


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ua = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return ua, ip


async def _issue_token_pair(
    db: AsyncSession,
    user: User,
    request: Request,
) -> TokenPair:
    access = create_token(user.id, "access")
    refresh = create_token(user.id, "refresh")
    payload = decode_token(refresh, expected_type="refresh")
    ua, ip = _client_meta(request)

    db.add(
        RefreshToken(
            user_id=user.id,
            jti=payload["jti"],
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            user_agent=ua,
            ip_address=ip,
        )
    )
    await db.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: UserCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    existing = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        timezone=payload.timezone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    pair = await _issue_token_pair(db, user, request)
    return AuthResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")

    pair = await _issue_token_pair(db, user, request)
    return AuthResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenPair:
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from None

    jti = decoded["jti"]
    user_id = uuid.UUID(decoded["sub"])

    rt = await db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if rt is None or rt.revoked:
        # Token replay or unknown — revoke all of this user's tokens.
        from sqlalchemy import update
        await db.execute(
            update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        )
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token revoked")

    # Rotate: revoke the old, issue a new pair.
    rt.revoked = True
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return await _issue_token_pair(db, user, request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Revoke all refresh tokens for the current user."""
    from sqlalchemy import update
    await db.execute(
        update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked=True)
    )
    await db.commit()
