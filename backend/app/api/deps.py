from datetime import UTC, datetime

from backend.app.core.config import settings
from backend.app.core.security import hash_session_token
from backend.app.db.session import get_db
from backend.app.models.session import UserSession
from backend.app.models.user import User
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_current_user(
    aicf_session: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate server-managed session from HttpOnly cookie or Authorization header."""
    token: str | None = aicf_session

    # Support optional Bearer token header for programmatic clients
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access this resource.",
        )

    token_hash = hash_session_token(token)
    now = datetime.now(UTC)

    stmt = (
        select(UserSession)
        .where(UserSession.token_hash == token_hash)
        .options(selectinload(UserSession.user))
    )
    result = await db.execute(stmt)
    session_record = result.scalars().first()

    if not session_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or has been revoked. Please sign in again.",
        )

    # Convert session_record.expires_at to UTC timezone if naive (e.g. SQLite driver)
    expires_at = session_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= now:
        await db.delete(session_record)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please sign in again.",
        )

    user: User = session_record.user
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated.",
        )

    return user
