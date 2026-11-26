import pytest
from pydantic import TypeAdapter, ValidationError

from app.common.tipos import DNI, IMEI, Telefono


def test_imei_valido():
    assert TypeAdapter(IMEI).validate_python("490154203237518") == "490154203237518"


@pytest.mark.parametrize("valor", ["490154203237519", "12345", "49015420323751a"])
def test_imei_invalido(valor):
    with pytest.raises(ValidationError):
        TypeAdapter(IMEI).validate_python(valor)


@pytest.mark.parametrize("valor,ok", [("1234567", True), ("12345678", True), ("123456", False)])
def test_dni(valor, ok):
    if ok:
        TypeAdapter(DNI).validate_python(valor)
    else:
        with pytest.raises(ValidationError):
            TypeAdapter(DNI).validate_python(valor)


def test_telefono_largo_invalido():
    with pytest.raises(ValidationError):
        TypeAdapter(Telefono).validate_python("1" * 16)


def test_dni_y_telefono_aceptan_separadores():
    assert TypeAdapter(DNI).validate_python("30.123.456") == "30123456"
    assert TypeAdapter(DNI).validate_python("7 123 456") == "7123456"
    assert TypeAdapter(Telefono).validate_python("+54 9 (341) 555-1234") == "5493415551234"
    with pytest.raises(ValidationError):
        TypeAdapter(DNI).validate_python("30/123/456")
