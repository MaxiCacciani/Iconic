from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class ErrorDeNegocio(Exception):
    """Base de los errores de dominio. Se traduce a una respuesta HTTP."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontrado(ErrorDeNegocio):
    status_code = status.HTTP_404_NOT_FOUND


class Conflicto(ErrorDeNegocio):
    status_code = status.HTTP_409_CONFLICT


class ReglaInvalida(ErrorDeNegocio):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT


class TransicionInvalida(ErrorDeNegocio):
    """Una acción no permitida para el estado actual (patrón State)."""

    status_code = status.HTTP_409_CONFLICT


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDeNegocio)
    async def _error_de_negocio(_: Request, exc: ErrorDeNegocio) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.mensaje})
