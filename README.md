# TrueNAS helper scripts

> A library of helpful scripts to manage TrueNAS

Tested on TrueNAS Scale 24.04

## How to use (helper scripts)

First create a virtualenv and install the project.

All helper scripts can be used as Python modules (with `python -m truenas_client.import_truenas_cert` for example),
or as a command (with `import-truenas-cert`).
The commands will be used in the documentation below.

All command arguments can also be passed as environment variables, to avoid leaking tokens in shell history.
For example, `--truenas-url` can be replaced by the environment variable `TRUENAS_URL`.

### Import a certificate in TrueNAS

```shell
import-truenas-cert \
  --truenas-url=https://truenas.domain.or.ip/api/v2.0 \
  --truenas-api-key=<api key created on https://truenas.domain.or.ip/ui/apikeys> \
  --truenas-cert-name=<certificate name> \
  --cert-fullchain-path=<certificate path> \
  --cert-privatekey-path=<private key path>
  # Optional, add this if your TrueNAS cert is not trusted, e.g. for the first run
  # --truenas-ssl-verify=false
```

## Python API client

A Python API client is being developed alongside the scripts, you can reuse and extend it as you see fit.

HTTP requests are made using [HTTPX][python-httpx] against the HTTP REST API (not the Websocket one),
and API responses are parsed with [Pydantic][python-pydantic] to ensure they look like what we expect.

You can find the TrueNAS REST API documentation at https://<truenas.domain.or.ip>/api/docs/#restful

## References and inspirations

- [TrueNAS server "middleware" (the code that runs their API)][truenas-middleware]
- [TrueNAS official Websocket client][truenas-websocket-client]
- [Async TrueNAS API client (unofficial, uses the Websocket API)][truenas-async-websocket-client]
- [Another async TrueNAS API client (unofficial, uses the REST API)][truenas-async-rest-client]
- [TrueNAS cert updater][truenas-cert-updater]
- [deploy freenas][truenas-deploy-freenas]

[python-httpx]: https://www.python-httpx.org/
[python-pydantic]: https://docs.pydantic.dev/
[truenas-async-rest-client]: https://github.com/cyr-ius/truenaspy
[truenas-async-websocket-client]: https://github.com/sdwilsh/aiotruenas-client
[truenas-cert-updater]: https://github.com/mcao2/truenas-cert-updater
[truenas-deploy-freenas]: https://github.com/danb35/deploy-freenas
[truenas-middleware]: https://github.com/truenas/middleware
[truenas-websocket-client]: https://github.com/truenas/api_client
