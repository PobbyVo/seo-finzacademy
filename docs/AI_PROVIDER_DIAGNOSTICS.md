# Gemini Test Connection — diagnosis (2026-11-21)

## Evidence and limits

Original request ID: `521d0a80-ec52-4e0d-a8ae-7d304729d2f5`.
The previous implementation did not persist correlated upstream diagnostics. No record for that ID exists in the new local diagnostic file. Its exact original upstream status cannot be recovered from the ID alone; the old application code merged multiple distinct failures into PROVIDER_UNAVAILABLE.

One user-authorized diagnostic Test Connection reproduced:

```json
{
  "request_id": "fba81e90-302a-4c20-a604-15b66fe141a2",
  "provider": "gemini",
  "method": "POST",
  "endpoint": "https://generativelanguage.googleapis.com/v1beta/interactions",
  "upstream_status": 503,
  "upstream_code": "service_unavailable",
  "network_reason": null,
  "code": "PROVIDER_UNAVAILABLE",
  "latency_ms": 1194
}
```

For this reproduced request, the failure is an upstream HTTP service-unavailable response, not a local socket timeout. It does not establish whether the supplied credential/model would succeed after service recovery. No automatic retry, provider fallback or model change was introduced. Project, snapshot and audit table hashes were identical before/after the diagnostic request. Only the existing AI settings test status/time changed.

## Trace

1. `/settings/ai` requires saved settings and explicit consent. Browser sends `POST /api/v1/settings/ai/test`, Content-Type application/json, body `{consent:true}` to the same-origin Next proxy.
2. Next rewrites `/api/v1/*` to FastAPI localhost. Middleware generates a UUID and returns it in X-Request-ID and the application error envelope.
3. Settings reads the active provider/model and secret UUID from SQLite. OSSecretStore obtains the key from Keychain; no key is returned to the browser or read from project data.
4. Registry validates consent/mock mode. Connection test prompt asks only for `{"ok":true}`; no project or Semrush data is included.
5. GeminiAdapter sends POST to the fixed HTTPS Interactions endpoint, x-goog-api-key, Content-Type application/json, Api-Revision 2026-05-20; body `{model: <saved model>, input: <short check prompt>, store:false}`. Redirects are disabled; urllib timeout remains 20 seconds.
6. Response parsing requires completed status, reads steps of type model_output and text content, validates the resulting JSON before marking CONNECTED. Errors keep Settings in ERROR.

The method, endpoint, input/model/store fields and steps schema match the official Interactions reference. The model gemini-3.8-flash is listed in that reference. No proven request-construction error was found, so these fields and the timeout duration were retained.

## Proven defects fixed

- HTTP 503 previously became application 502. Its status is now preserved as 503, with upstream_status 503 and service_unavailable when present.
- HTTP 400 previously became INVALID_PROVIDER_RESPONSE/502. It is now PROVIDER_BAD_REQUEST/400 for ordinary invalid request parameters.
- URLError wrapping TimeoutError previously became PROVIDER_UNAVAILABLE/503. It now becomes CONNECTION_TIMEOUT/504.
- DNS/TLS/refused/reset/network failures previously became the same provider-unavailable error as an actual HTTP outage. They now have NETWORK_ERROR plus network_reason and null upstream_status.
- Upstream machine code and request ID were discarded. They now survive as allowlisted diagnostics.
- A failed metadata refresh after the Test response could replace the original UI error. Refresh now preserves the original error; UI shows local Request ID, application/upstream status, upstream code and network category.

## Classification

| Upstream / transport | Application code | Application HTTP |
|---|---|---|
| 400 invalid_request / invalid parameters | PROVIDER_BAD_REQUEST | 400 |
| 401 authentication | API_KEY_INVALID | 401 |
| 403 permission_denied | PERMISSION_DENIED | 403 |
| 404 model_not_found | MODEL_NOT_FOUND | 404 |
| 429 rate_limit_exceeded | RATE_LIMITED | 429 |
| 429 quota_exceeded / insufficient_quota | QUOTA_EXCEEDED | 429 |
| 503 service_unavailable | PROVIDER_UNAVAILABLE | 503 |
| 504 deadline_exceeded or wrapped/direct socket timeout | CONNECTION_TIMEOUT | 504 |
| DNS, TLS, connection refused/reset, other network failures | NETWORK_ERROR | 503, upstream_status null |

Other upstream 5xx remain a gateway failure; the actual upstream status remains available independently. Raw provider messages are intentionally not logged or exposed: they may echo credentials or request content. Safe error codes and local Vietnamese guidance provide actionable context without that exposure.

## Safe logs and verification

Local runtime writes rotating JSON lines to `data/provider_diagnostics.jsonl` (1 MB, two backups, gitignored). The initial file has mode 0600. Each record contains timestamp, local Request ID, fixed provider/endpoint, method, latency, upstream status, allowlisted error code/upstream request ID and network category. No key, headers, payload, model-generated content, raw error message, raw exception or project data is serialized. Automated tests use temporary diagnostic files/in-memory transports.

Search a request:

```sh
rg 'fba81e90-302a-4c20-a604-15b66fe141a2' data/provider_diagnostics.jsonl
```

Use `/settings/ai` and explicitly click Test Connection once to obtain a new Request ID. Do not paste credentials into log commands. For deterministic tests:

```sh
cd services/api
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
```

From repository root:

```sh
make lint-web typecheck build-web
npm --prefix e2e run typecheck
npm --prefix e2e test
```

## Primary references

- [Interactions create API](https://aistudio.google.com/api-reference/interactions-api/create-interaction)
- [Interactions API errors](https://aistudio.google.com/docs/api-errors)
- [Gemini troubleshooting](https://aistudio.google.com/docs/troubleshooting)

No migration, credential-storage change or research/project-data change was required. No commit/push/deploy performed.
