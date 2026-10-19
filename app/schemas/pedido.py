from pydantic import ConfigDict

from app.schemas.schemas import Base

class CreateRequest(Base):
    produto: int

class CreateResponse(Base):
    id: int
    drink: str
    cliente_nome: str
    status: str

    model_config = ConfigDict(from_attributes=True)