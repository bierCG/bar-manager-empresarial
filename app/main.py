from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    websocket, login, empresas, usuarios, produtos, pedidos 
)
from app.core.exceptions.errors import ErroDeNegocio, ErroOperacional
from app.core.exceptions.handlers import (
    erro_negocio_handler, erro_interno_handler, erro_operacional_handler
)

from app.admin import setup_admin

app = FastAPI(title="Sistema de Pedidos - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket.router)
app.include_router(login.router)
app.include_router(empresas.router)
app.include_router(usuarios.router)
app.include_router(produtos.router)
app.include_router(pedidos.router)

app.add_exception_handler(ErroDeNegocio, erro_negocio_handler)
app.add_exception_handler(ErroOperacional, erro_operacional_handler)
app.add_exception_handler(Exception, erro_interno_handler)

setup_admin(app)

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "API do Bar rodando com sucesso!"}