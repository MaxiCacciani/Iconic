"""Adapter de archivos: los services no conocen boto3.

En producción se usa `AlmacenR2` (bucket privado de Cloudflare R2); en tests, `AlmacenEnMemoria`.
"""

from typing import Protocol

from app.common.enums import TipoArchivo
from app.core.config import Settings

CONTENT_TYPES = {TipoArchivo.pdf: "application/pdf", TipoArchivo.jpg: "image/jpeg"}


class AlmacenArchivos(Protocol):
    def subir(self, clave: str, datos: bytes, tipo: TipoArchivo) -> None: ...
    def url_firmada(self, clave: str, ttl: int) -> str: ...
    def eliminar(self, clave: str) -> None: ...


class AlmacenR2:
    def __init__(self, settings: Settings) -> None:
        import boto3

        self.bucket = settings.r2_bucket
        self.cliente = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )

    def subir(self, clave: str, datos: bytes, tipo: TipoArchivo) -> None:
        self.cliente.put_object(
            Bucket=self.bucket, Key=clave, Body=datos, ContentType=CONTENT_TYPES[tipo]
        )

    def url_firmada(self, clave: str, ttl: int) -> str:
        return self.cliente.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": clave}, ExpiresIn=ttl
        )

    def eliminar(self, clave: str) -> None:
        self.cliente.delete_object(Bucket=self.bucket, Key=clave)


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.archivos: dict[str, tuple[bytes, TipoArchivo]] = {}

    def subir(self, clave: str, datos: bytes, tipo: TipoArchivo) -> None:
        self.archivos[clave] = (datos, tipo)

    def url_firmada(self, clave: str, ttl: int) -> str:
        return f"memoria://{clave}?ttl={ttl}"

    def eliminar(self, clave: str) -> None:
        self.archivos.pop(clave, None)
