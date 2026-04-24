"""
Cria os usuários iniciais do sistema (admin + secretária).

Executar via:
  docker compose exec backend python -m app.scripts.create_admin

Senhas padrão:
  admin@openclinic.local    → admin
  secretaria@openclinic.local → secretaria

IMPORTANTE: Altere as senhas no primeiro acesso!
"""
import asyncio
import sys

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal, engine, Base
from app.modules.auth.models import User
from app.core.security import hash_password


INITIAL_USERS = [
    {
        "email": "admin@openclinic.local",
        "full_name": "Administrador",
        "password": "admin",
        "role": "admin",
    },
    {
        "email": "secretaria@openclinic.local",
        "full_name": "Secretária",
        "password": "secretaria",
        "role": "secretary",
    },
]


async def create_initial_users():
    # Garante que as tabelas existem (para rodar antes do Alembic se necessário)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        for user_data in INITIAL_USERS:
            result = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  [SKIP] {user_data['email']} já existe.")
                continue

            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                password_hash=hash_password(user_data["password"]),
                role=user_data["role"],
                must_change_password=True,
            )
            db.add(user)
            await db.commit()
            print(f"  [OK]   {user_data['email']} criado (role: {user_data['role']})")

    await engine.dispose()


def main():
    print("")
    print("Criando usuários iniciais...")
    print("")
    asyncio.run(create_initial_users())
    print("")
    print("=" * 50)
    print("  CREDENCIAIS INICIAIS")
    print("=" * 50)
    print(f"  Admin:      admin@openclinic.local / admin")
    print(f"  Secretária: secretaria@openclinic.local / secretaria")
    print("")
    print("  ALTERE AS SENHAS NO PRIMEIRO ACESSO!")
    print("=" * 50)
    print("")


if __name__ == "__main__":
    main()
