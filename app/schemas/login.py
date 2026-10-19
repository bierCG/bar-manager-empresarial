from app.schemas.schemas import Base

class LoginRequest(Base):
    usuario: str
    senha: str

class LoginResponse(Base):
    usuario: str
    token: str