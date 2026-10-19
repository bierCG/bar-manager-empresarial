from pydantic import ConfigDict, field_validator, Field

from app.schemas.schemas import Base

def digito(cnpj: str, pesos: list[int]) -> str:
    soma = sum(int(n) * p for n, p in zip(cnpj, pesos))
    resto = soma % 11
    return str(0 if resto < 2 else 11 - resto)

class CreateRequestEmpresa(Base):
    nome: str = Field(min_length=4)
    cnpj: str
    usuario: str = Field(min_length=4)
    senha: str = Field(min_length=4)

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, cnpj: str) -> str:
        cnpj = "".join(filter(str.isdigit, cnpj))

        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            raise ValueError("CNPJ inválido")

        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [6, *pesos1]

        dv1 = digito(cnpj[:12], pesos1)
        dv2 = digito(cnpj[:12] + dv1, pesos2)

        if cnpj[-2:] != dv1 + dv2:
            raise ValueError("CNPJ inválido")

        return cnpj

class CreateResponseEmpresa(Base):
    nome: str
    cnpj: str
    usuario: str

    model_config = ConfigDict(from_attributes=True)

class UpdateRequestEmpresa(Base):
    nome: str = Field(min_length=4)
    # Acrescentar a medida que os casos demandarem

class UpdateResponseEmpresa(UpdateRequestEmpresa):
    pass

class ReadResponseEmpresa(CreateResponseEmpresa):
    pass