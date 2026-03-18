from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.time import utcnow
from app.db.session import get_session
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.tokens import RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _revoke_refresh_token(rt: RefreshToken) -> None:
    if rt.revoked_at is None:
        rt.revoked_at = utcnow()


def _revoke_all_user_refresh_tokens(session: Session, user_id: int) -> int:
    tokens = session.exec(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    ).all()

    now = utcnow()
    for t in tokens:
        t.revoked_at = now

    return len(tokens)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um usuário (register)",
)
@limiter.limit("5/minute")
def register(
    request: Request,
    user_in: UserCreate,
    session: Session = Depends(get_session),
):
    existing = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_in.email, hashed_password=hash_password(user_in.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserRead(id=user.id, email=user.email)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login (OAuth2 Password Form)",
    description=(
        "Endpoint padrão OAuth2. Envia form-urlencoded com fields: "
        "`username` (email) e `password`.\n\n"
        "Para facilitar teste via Swagger com JSON, use `/auth/login-json`."
    ),
)
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=str(user.id), expires_delta=access_expires)

    refresh_token_plain = create_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token_plain)
    expires_at = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    rt = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires_at,
    )
    session.add(rt)
    session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_plain,
        expires_in=int(access_expires.total_seconds()),
    )


@router.post(
    "/login-json",
    response_model=TokenResponse,
    summary="Login (JSON) - para facilitar no Swagger",
    description="Endpoint auxiliar (UX). Recebe JSON {email, password}.",
)
@limiter.limit("10/minute")
def login_json(
    request: Request,
    body: UserLogin,
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=str(user.id), expires_delta=access_expires)

    refresh_token_plain = create_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token_plain)
    expires_at = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    rt = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires_at,
    )
    session.add(rt)
    session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_plain,
        expires_in=int(access_expires.total_seconds()),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotaciona refresh token")
@limiter.limit("20/minute")
def refresh_tokens(
    request: Request,
    body: RefreshRequest,
    session: Session = Depends(get_session),
):
    token_hash = hash_refresh_token(body.refresh_token)

    rt = session.exec(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    now = utcnow()
    rt.expires_at = _ensure_aware(rt.expires_at)
    if rt.revoked_at is not None:
        rt.revoked_at = _ensure_aware(rt.revoked_at)

    # Opção A: reuse detection
    if rt.revoked_at is not None:
        _revoke_all_user_refresh_tokens(session, rt.user_id)
        session.commit()
        raise HTTPException(
            status_code=401,
            detail="Refresh token reuse detected. All sessions revoked.",
        )

    if rt.expires_at <= now:
        _revoke_refresh_token(rt)
        session.add(rt)
        session.commit()
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Rotation
    _revoke_refresh_token(rt)

    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access = create_access_token(subject=str(rt.user_id), expires_delta=access_expires)

    new_refresh_plain = create_refresh_token()
    new_refresh_hash = hash_refresh_token(new_refresh_plain)
    new_expires_at = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_rt = RefreshToken(
        user_id=rt.user_id,
        token_hash=new_refresh_hash,
        expires_at=new_expires_at,
    )

    session.add(rt)
    session.add(new_rt)
    session.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh_plain,
        expires_in=int(access_expires.total_seconds()),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoga um refresh token")
@limiter.limit("30/minute")
def logout(
    request: Request,
    body: RefreshRequest,
    session: Session = Depends(get_session),
):
    token_hash = hash_refresh_token(body.refresh_token)
    rt = session.exec(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()
    if not rt:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    _revoke_refresh_token(rt)
    session.add(rt)
    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT, summary="Revoga todas as sessões do usuário")
@limiter.limit("10/minute")
def logout_all(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _revoke_all_user_refresh_tokens(session, user.id)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead, summary="Retorna o usuário logado")
@limiter.limit("60/minute")
def me(
    request: Request,
    user: User = Depends(get_current_user),
):
    return UserRead(id=user.id, email=user.email)
