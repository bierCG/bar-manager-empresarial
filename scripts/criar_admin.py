from sqlalchemy import select

from app.core.database.connection import SessionLocal
from app.core.database.models import Usuario
from app.core.security.password import hash_senha

EMAIL = "admin@exemplo.com"
SENHA = "admin123"
ROLE = "admin"

def main():
    with SessionLocal() as db:
        existe = db.scalar(select(Usuario).where(Usuario.email == EMAIL))
        if existe:
            return

        db.add(Usuario(
            nome="Admin",
            email=EMAIL,
            senha=hash_senha(SENHA),
            role=ROLE,
        ))
        db.commit()


if __name__ == "__main__":
    main()