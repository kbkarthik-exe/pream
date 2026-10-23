from datetime import UTC, datetime, timedelta

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.core.rate_limiter import rate_limiter
from backend.app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from backend.app.db.session import get_db
from backend.app.models.session import UserSession
from backend.app.models.user import User
from backend.app.schemas.auth import (
    ProfileUpdate,
    SessionStatusResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _set_session_cookie(response: Response, raw_token: str) -> None:
    """Set hardened session cookie on response."""
    max_age_seconds = settings.SESSION_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=raw_token,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        path="/",
        domain=None,
        secure=settings.COOKIE_SECURE,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=settings.COOKIE_SAMESITE,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Analyst Account",
    description=(
        "Creates a persistent user account with Argon2id password hashing and session cookie."
    ),
)
async def register(
    request: Request,
    response: Response,
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    # 1. Rate limiting
    rate_limiter.check(
        request=request,
        action="registration",
        max_requests=settings.RATE_LIMIT_REGISTER_MAX,
        window_seconds=settings.RATE_LIMIT_REGISTER_WINDOW,
    )

    # 2. Check existing user
    stmt = select(User).where(or_(User.email == payload.email, User.username == payload.username))
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        if existing.email == payload.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken. Please choose another.",
        )

    # 3. Create user with Argon2id hash
    hashed = hash_password(payload.password)
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hashed,
        full_name=payload.full_name,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # populate user.id

    # 4. Create initial authenticated session
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)

    session_record = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
        expires_at=expires_at,
    )
    db.add(session_record)
    await db.commit()
    await db.refresh(user)

    # 5. Attach HttpOnly session cookie
    _set_session_cookie(response, raw_token)

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Authenticate Analyst",
    description=(
        "Authenticates credentials against Argon2id hash and issues a server-managed session."
    ),
)
async def login(
    request: Request,
    response: Response,
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    # 1. Rate limiting
    rate_limiter.check(
        request=request,
        action="login",
        max_requests=settings.RATE_LIMIT_LOGIN_MAX,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW,
    )

    # 2. Look up user by email or username
    identifier = payload.identifier.strip().lower()
    stmt = select(User).where(or_(User.email == identifier, User.username == identifier))
    user = (await db.execute(stmt)).scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password. Please verify your credentials.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact support.",
        )

    # 3. Create new session
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)

    session_record = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
        expires_at=expires_at,
    )
    db.add(session_record)
    await db.commit()
    await db.refresh(user)

    # 4. Attach HttpOnly session cookie
    _set_session_cookie(response, raw_token)

    return UserResponse.model_validate(user)


@router.post(
    "/logout",
    summary="Terminate Session",
    description="Revokes server session in database and clears client session cookie.",
)
async def logout(
    response: Response,
    aicf_session: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if aicf_session:
        token_hash = hash_session_token(aicf_session)
        stmt = select(UserSession).where(UserSession.token_hash == token_hash)
        session_record = (await db.execute(stmt)).scalars().first()
        if session_record:
            await db.delete(session_record)
            await db.commit()

    # Clear cookie
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        secure=settings.COOKIE_SECURE,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=settings.COOKIE_SAMESITE,
    )
    return {"message": "Session successfully terminated."}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current Analyst Profile",
    description="Returns profile of the currently authenticated analyst.",
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get(
    "/status",
    response_model=SessionStatusResponse,
    summary="Check Authentication Status",
    description=(
        "Returns whether the caller has an active authenticated session without throwing 401."
    ),
)
async def get_status(
    aicf_session: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> SessionStatusResponse:
    if not aicf_session:
        return SessionStatusResponse(authenticated=False, user=None)

    token_hash = hash_session_token(aicf_session)
    now = datetime.now(UTC)
    stmt = select(UserSession).where(UserSession.token_hash == token_hash)
    session_record = (await db.execute(stmt)).scalars().first()
    if not session_record:
        return SessionStatusResponse(authenticated=False, user=None)

    expires_at = session_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= now:
        await db.delete(session_record)
        await db.commit()
        return SessionStatusResponse(authenticated=False, user=None)

    user = await db.get(User, session_record.user_id)
    if not user or not user.is_active:
        return SessionStatusResponse(authenticated=False, user=None)

    return SessionStatusResponse(
        authenticated=True,
        user=UserResponse.model_validate(user),
    )


@router.patch(
    "/profile",
    response_model=UserResponse,
    summary="Update Analyst Profile",
    description="Updates analyst settings including full name or credentials.",
)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip() or None

    if payload.new_password:
        if not payload.current_password or not verify_password(
            payload.current_password, current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password verification failed.",
            )
        current_user.hashed_password = hash_password(payload.new_password)

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)
