from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.errors import (
    ErroDeNegocio,
    ErroOperacional,
    PedidoNaoEncontrado,
    SemPermissao
) 

from app.core.logger import logger

# mapa: tipo de erro de negócio -> status HTTP
STATUS_POR_ERRO = {
    PedidoNaoEncontrado: 404,
    SemPermissao: 403,
}

async def erro_negocio_handler(request: Request, exc: ErroDeNegocio) -> JSONResponse:
    logger.info("Erro de negócio: %s - %s", exc.status_code, exc.message)

    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.message},
    )

async def erro_operacional_handler(request: Request, exc: ErroOperacional) -> JSONResponse:
    logger.info("Erro de operação: %s - %s", exc.status_code, exc.message)

    return JSONResponse(
        status_code=500,
        content={"message": exc.message}
    )

async def erro_interno_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro interno não tratado")

    return JSONResponse(
        status_code=500,
        content={"code": "erro_interno", "message": "Erro interno do servidor"},
    )