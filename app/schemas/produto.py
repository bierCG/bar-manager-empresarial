from pydantic import ConfigDict, Field

from app.schemas.schemas import Base

class CreateRequest(Base):
    nome: str = Field(min_length=4)
    valor: float = Field(gt=0)

class CreateResponse(CreateRequest):
    id: int

    model_config = ConfigDict(from_attributes=True)

class UpdateRequest(Base):
    nome: str | None = Field(default=None, min_length=4)
    valor: float | None = Field(default=None, gt=0)

class UpdateResponse(UpdateRequest):
    id: int

    model_config = ConfigDict(from_attributes=True)