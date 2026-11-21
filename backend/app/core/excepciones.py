from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
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


class ErrorDeCampo(ReglaInvalida):
    """Regla que falla sobre un campo concreto: el front la muestra junto a ese campo.

    Se responde con el mismo formato que los 422 de validación de FastAPI.
    """

    def __init__(self, campo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.campo = campo


class TransicionInvalida(ErrorDeNegocio):
    """Una acción no permitida para el estado actual (patrón State)."""

    status_code = status.HTTP_409_CONFLICT


# Mensajes en español para los errores de validación más comunes de Pydantic.
_MENSAJES: dict[str, str] = {
    "missing": "Este campo es obligatorio.",
    "string_too_short": "Tiene que tener al menos {min_length} caracteres.",
    "string_too_long": "Puede tener hasta {max_length} caracteres.",
    "enum": "Elegí una de las opciones.",
    "int_parsing": "Tiene que ser un número entero.",
    "float_parsing": "Tiene que ser un número.",
    "bool_parsing": "Tiene que ser sí o no.",
    "greater_than": "Tiene que ser mayor que {gt}.",
    "greater_than_equal": "Tiene que ser {ge} o más.",
    "less_than_equal": "Tiene que ser {le} o menos.",
}


def _traducir(error: dict) -> dict:
    tipo = error.get("type", "")
    if tipo == "value_error":
        # Los validadores propios lanzan ValueError con el mensaje ya en español.
        mensaje = str(error.get("ctx", {}).get("error", error["msg"]))
    elif tipo in _MENSAJES:
        try:
            mensaje = _MENSAJES[tipo].format(**error.get("ctx", {}))
        except KeyError:
            mensaje = error["msg"]
    else:
        mensaje = error["msg"]
    return {"loc": error["loc"], "msg": mensaje, "type": tipo}


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDeCampo)
    async def _error_de_campo(_: Request, exc: ErrorDeCampo) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": [{"loc": ["body", exc.campo], "msg": exc.mensaje, "type": "regla"}]},
        )

    @app.exception_handler(ErrorDeNegocio)
    async def _error_de_negocio(_: Request, exc: ErrorDeNegocio) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.mensaje})

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": jsonable_encoder([_traducir(e) for e in exc.errors()])},
        )
