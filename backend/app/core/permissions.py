"""RBAC dependencies for FastAPI routes."""
import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_user_by_id

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT access token."""
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise UnauthorizedError()

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError()

    try:
        user = await get_user_by_id(db, uuid.UUID(user_id))
    except ValueError:
        raise UnauthorizedError()

    if user is None or not user.is_active:
        raise UnauthorizedError()

    return user


def require_role(*roles: str):
    """Dependency factory that checks if the current user has one of the required roles."""
    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError()
        return current_user
    return check_role
