from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.core.database.connection import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=False)
    usuario = Column(String(100), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    valor = Column(Float, nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    produto = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    status = Column(String(20), nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    usuario = Column(String(150), nullable=False, unique=True, index=True)
    role = Column(String(100), nullable=False)
    senha_hash = Column(String(255), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)