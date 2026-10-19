from pydantic import ConfigDict

from app.schemas.schemas import Base

class CreateRequest(Base):
    nome: str
    usuario: str
    senha: str
    role: str

class CreateResponse(Base):
    id: int
    nome: str
    usuario: str

    model_config = ConfigDict(from_attributes=True)

class UpdateRequest(Base):
    usuario: str | None = None
    senha: str | None = None
    role: str | None = None

class UpdateResponse(UpdateRequest):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ReadResponse(Base):
    nome: str
    usuario: str
    role: str