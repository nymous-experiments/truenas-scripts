import asyncio
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from truenas_client import delete_certificate, get_truenas_client, import_certificate


class Settings(BaseSettings):
    model_config = SettingsConfigDict(cli_parse_args=True)

    truenas_url: Annotated[str, Field(validation_alias="truenas-url")]
    truenas_ssl_verify: Annotated[
        bool, Field(validation_alias="truenas-ssl-verify")
    ] = True
    truenas_api_key: Annotated[SecretStr, Field(validation_alias="truenas-api-key")]
    truenas_cert_name: Annotated[str, Field(validation_alias="truenas-cert-name")]

    cert_fullchain_path: Annotated[Path, Field(validation_alias="cert-fullchain-path")]
    cert_privatekey_path: Annotated[
        Path, Field(validation_alias="cert-privatekey-path")
    ]


async def main() -> int:
    settings = Settings()

    async with get_truenas_client(
        url=settings.truenas_url,
        api_key=settings.truenas_api_key.get_secret_value(),
        verify=settings.truenas_ssl_verify,
    ) as client:
        with settings.cert_fullchain_path.open() as cert, settings.cert_privatekey_path.open() as key:
            certificate = await import_certificate(
                client,
                settings.truenas_cert_name,
                cert.read(),
                key.read(),
                wait=True,
            )
        print(await delete_certificate(client, certificate.id))
    return 0


def entrypoint_sync() -> None:
    raise SystemExit(asyncio.run(main()))


if __name__ == "__main__":
    entrypoint_sync()
