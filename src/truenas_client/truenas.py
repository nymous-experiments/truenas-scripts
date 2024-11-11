from collections.abc import AsyncIterator
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, NewType, overload

from httpx import AsyncClient
from pydantic import AliasPath, BaseModel, Field, SecretStr, TypeAdapter

TruenasClient = NewType("TruenasClient", AsyncClient)


def get_truenas_client(
    url: str,
    api_key: str,
    verify: bool = True,
) -> TruenasClient:
    return TruenasClient(
        AsyncClient(
            base_url=url,
            headers={"Authorization": f"Bearer {api_key}"},
            verify=verify,
        )
    )


class Certificate(BaseModel):
    id: int
    type: int
    name: str
    certificate: str
    privatekey: SecretStr
    CSR: str | None
    revoked_date: datetime | None
    signedby: str | None
    root_path: str
    certificate_path: str
    privatekey_path: str
    csr_path: str
    cert_type: str
    revoked: bool
    can_be_revoked: bool
    internal: str
    CA_type_existing: bool
    CA_type_internal: bool
    CA_type_intermediate: bool
    cert_type_existing: bool
    cert_type_internal: bool
    cert_type_CSR: bool
    issuer: str
    chain_list: list[str]
    key_length: int
    key_type: str
    country: str | None
    state: str | None
    city: str | None
    organization: str | None
    organizational_unit: str | None
    common: str
    san: list[str]
    email: str | None
    DN: str
    subject_name_hash: int
    extensions: dict[str, str]
    digest_algorithm: str
    lifetime: int
    from_: Annotated[str, Field(alias="from")]
    until: str
    serial: int
    chain: bool
    fingerprint: str
    expired: bool
    parsed: bool


CertificateList = TypeAdapter(list[Certificate])


async def get_certificates(client: TruenasClient) -> list[Certificate]:
    r = await client.get("/certificate")
    r.raise_for_status()
    certificates = CertificateList.validate_json(r.text)
    return certificates


async def get_certificate(client: TruenasClient, certificate_id: int) -> Certificate:
    r = await client.get(f"/certificate/id/{certificate_id}")
    r.raise_for_status()
    certificate = Certificate.model_validate_json(r.text)
    return certificate


@overload
async def import_certificate(
    client: TruenasClient,
    name: str,
    certificate: str,
    private_key: str,
    wait: Literal[True],
) -> Certificate: ...


@overload
async def import_certificate(
    client: TruenasClient,
    name: str,
    certificate: str,
    private_key: str,
    wait: Literal[False] = False,
) -> int: ...


async def import_certificate(
    client: TruenasClient,
    name: str,
    certificate: str,
    private_key: str,
    wait: bool = False,
) -> int | Certificate:
    """
    With wait=False, returns the job ID.
    With wait=True, waits for the job and raises an exception if it fails.
    """
    r = await client.post(
        "/certificate",
        json={
            "create_type": "CERTIFICATE_CREATE_IMPORTED",
            "name": name,
            "certificate": certificate,
            "privatekey": private_key,
        },
    )
    r.raise_for_status()
    job_id = int(r.text)
    if wait:
        job = await wait_job(client, job_id)
        return await get_certificate(
            client, job_id
        )  # TODO: get certificate ID from job
    else:
        return job_id


@overload
async def delete_certificate(
    client: TruenasClient,
    certificate_id: int,
    *,
    force: bool = False,
    wait: Literal[True],
) -> None: ...


@overload
async def delete_certificate(
    client: TruenasClient,
    certificate_id: int,
    *,
    force: bool = False,
    wait: Literal[False] = False,
) -> int: ...


async def delete_certificate(
    client: TruenasClient,
    certificate_id: int,
    force: bool = False,
    wait: bool = False,
) -> int | None:
    """
    With wait=False, returns the job ID.
    With wait=True, waits for the job and raises an exception if it fails.
    """
    r = await client.delete(
        f"/certificate/id/{certificate_id}", params={"force": force}
    )
    r.raise_for_status()
    job_id = int(r.text)
    if wait:
        await wait_job(client, job_id)
        return None
    else:
        return job_id


class Progress(BaseModel):
    percent: int
    description: str
    extra: str | None


class _TokenCredentialsData(BaseModel):
    parent: dict[str, Any]
    username: str


class TokenCredentials(BaseModel):
    type: Literal["TOKEN"]
    data: _TokenCredentialsData


class _ApiKeyCredentialsData(BaseModel):
    api_key: dict[str, Any]


class ApiKeyCredentials(BaseModel):
    type: Literal["API_KEY"]
    data: _ApiKeyCredentialsData


class _UnixSocketCredentialsData(BaseModel):
    username: str


class UnixSocketCredentials(BaseModel):
    type: Literal["UNIX_SOCKET"]
    data: _UnixSocketCredentialsData


class _LoginPasswordCredentialsData(BaseModel):
    username: str


class LoginPasswordCredentials(BaseModel):
    type: Literal["LOGIN_PASSWORD"]
    data: _LoginPasswordCredentialsData


class ExcInfo(BaseModel):
    repr: str
    type: str
    extra: list[list[Any]] | None


class JobState(str, Enum):
    success = "SUCCESS"
    failed = "FAILED"


class Job(BaseModel):
    id: int
    method: str
    arguments: list[Any]
    transient: bool
    description: str | None
    abortable: bool
    logs_path: str | None
    logs_excerpt: str | None
    progress: Progress
    result: Certificate | Any
    error: str | None
    exc_info: ExcInfo | None
    state: JobState
    time_started: Annotated[
        datetime, Field(validation_alias=AliasPath("time_started", "$date"))
    ]
    time_finished: Annotated[
        datetime, Field(validation_alias=AliasPath("time_finished", "$date"))
    ]
    credentials: (
        Annotated[
            ApiKeyCredentials
            | LoginPasswordCredentials
            | TokenCredentials
            | UnixSocketCredentials,
            Field(discriminator="type"),
        ]
        | None
    )


JobList = TypeAdapter(list[Job])


async def get_jobs(
    client: TruenasClient,
    limit: int = 50,
    offset: int = 0,
) -> list[Job]:
    r = await client.get(
        "/core/get_jobs",
        params={
            "limit": limit,
            "offset": offset,
        },
    )
    r.raise_for_status()
    jobs = JobList.validate_json(r.text)
    return jobs


async def get_jobs_iter(
    client: TruenasClient,
    limit: int = 50,
    offset: int = 0,
) -> AsyncIterator[Job]:
    current_offset = offset
    might_have_more_jobs = True
    while might_have_more_jobs:
        jobs = await get_jobs(client, limit=limit, offset=current_offset)
        for job in jobs:
            yield job
        current_offset += limit
        might_have_more_jobs = len(jobs) > 0


async def get_job(client: TruenasClient, job_id: int) -> Job:
    """
    This method is inefficient; because TrueNAS doesn't provide a GET job API,
    we must get all jobs and iterate over them to find the ID we need.

    :raises IndexError: If the job ID is not found
    """
    async for job in get_jobs_iter(client):
        if job.id == job_id:
            return job

    raise IndexError(f"Could not find job with ID {job_id}")


async def wait_job(client: TruenasClient, job_id: int) -> Job:
    r = await client.post("/core/job_wait", content=str(job_id))
    r.raise_for_status()
    return await get_job(client, job_id)
