"""Authentication API endpoints."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.permissions import get_current_user, require_role
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    CreateUserRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
    UpdateUserRequest,
    UserResponse,
)
from app.modules.auth.service import (
    authenticate_user,
    change_password,
    create_user,
    get_all_users,
    get_user_by_email,
    get_user_by_id,
    update_user,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise UnauthorizedError()

    token_data = {"sub": str(user.id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise UnauthorizedError()

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError()

    user = await get_user_by_id(db, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise UnauthorizedError()

    token_data = {"sub": str(user.id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", response_model=MessageResponse)
async def change_my_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import verify_password

    if not verify_password(body.current_password, current_user.password_hash):
        raise UnauthorizedError()

    if len(body.new_password) < 6:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="A nova senha deve ter no mínimo 6 caracteres.")

    await change_password(db, current_user, body.new_password)
    return MessageResponse(message="Senha alterada com sucesso.")


# --- Admin: gerenciamento de usuários ---

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_users(db)


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_new_user(
    body: CreateUserRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    if body.role not in ("admin", "secretary"):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Role deve ser 'admin' ou 'secretary'.")

    existing = await get_user_by_email(db, body.email)
    if existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")

    return await create_user(
        db,
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        role=body.role,
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_existing_user(
    user_id: uuid.UUID,
    body: UpdateUserRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if body.role is not None and body.role not in ("admin", "secretary"):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Role deve ser 'admin' ou 'secretary'.")

    if body.email is not None:
        existing = await get_user_by_email(db, body.email)
        if existing and existing.id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="E-mail já cadastrado.")

    return await update_user(
        db, user,
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        is_active=body.is_active,
    )


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
async def admin_reset_password(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin reseta a senha de um usuário para o padrão do role."""
    user = await get_user_by_id(db, user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    default_password = "admin" if user.role == "admin" else "secretaria"
    await change_password(db, user, default_password)
    user.must_change_password = True
    await db.commit()

    return MessageResponse(message=f"Senha resetada para o padrão. Usuário deverá alterar no próximo login.")
