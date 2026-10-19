from app.schemas.schemas import Base

class Auth(Base):
    sub: int
    role: str