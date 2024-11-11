import asyncio
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from truenas_client import (
    delete_certificate,
    get_certificate,
    get_certificates,
    get_job,
    get_jobs,
    get_truenas_client,
    import_certificate,
    wait_job,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(cli_parse_args=True)

    truenas_url: Annotated[str, Field(validation_alias="truenas-url")]
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
        verify=False,
    ) as client:
        print((await get_certificates(client))[0])
        print((await get_certificates(client))[1])
        print(await get_certificate(client, 1))
        with settings.cert_fullchain_path.open() as cert, settings.cert_privatekey_path.open() as key:
            create_job_id = await import_certificate(
                client,
                settings.truenas_cert_name,
                cert.read(),
                key.read(),
                wait=False,
            )
        print(await get_jobs(client))
        await get_job(client, 11)
        print(await wait_job(client, create_job_id))
        print(await delete_certificate(client, 8))
    return 0


def entrypoint_sync() -> None:
    raise SystemExit(asyncio.run(main()))


if __name__ == "__main__":
    entrypoint_sync()
