# ContentGuard — Headless Compliance API

**Live:** https://contentguard-api-bjex.onrender.com · **Interactive docs:** [/docs](https://contentguard-api-bjex.onrender.com/docs)

Validate marketing content (email / ad / social / webpage) against:
**FTC · EU AI Act · CAN-SPAM · GDPR** — in one HTTP call.

🌍 Read this in: [English](README.md) · [中文](docs/README_zh.md) · [Español](docs/README_es.md) · [Français](docs/README_fr.md) · [Deutsch](docs/README_de.md) · [日本語](docs/README_ja.md)

## Why
AI now writes most marketing email. Regulators require **AI disclosure**, ban **guaranteed-earnings / absolute claims**, and enforce **unsubscribe + physical address** rules. ContentGuard is a single endpoint that catches all of it and returns a safe repaired version — no UI to build, no rules to maintain.

## Auth (v0.3.0)
All `/v1/*` endpoints require an `X-API-Key` header.
- Free key: `demo-key-1000` (1,000 calls/day)
- Paid keys: set env `CONTENTGUARD_API_KEYS=key:limit,key:limit`
- Check usage: `GET /v1/usage`
- Usage is logged to `usage.json` (swap for Redis at scale).

## Endpoints
- `GET /` landing page
- `GET /health` health check (version + uptime)
- `GET /v1/usage` usage for the current key
- `POST /v1/check` run compliance check

## Quick start

### curl
```bash
curl -X POST https://contentguard-api-bjex.onrender.com/v1/check \
  -H "X-API-Key: demo-key-1000" \
  -H "Content-Type: application/json" \
  -d '{"text":"Guarantee you earn $3000/week, risk free. Buy now.","content_type":"email","return_fix":true}'
```

### Python
```python
import requests

resp = requests.post(
    "https://contentguard-api-bjex.onrender.com/v1/check",
    headers={"X-API-Key": "demo-key-1000"},
    json={"text": "your copy", "content_type": "email", "return_fix": True},
)
data = resp.json()
print(data["compliance_score"], data["violations"])
print(data["auto_fix"]["fixed_version"])
```

### Request
```json
{
  "text": "Hi, guarantee you earn $3000/week, risk free. Buy now.",
  "content_type": "email",
  "is_ai_generated": true,
  "subject": "Re: hello",
  "return_fix": true
}
```

### Response
```json
{
  "compliance_score": 0,
  "is_compliant": false,
  "summary": "5 high-severity issue(s) must be fixed before sending.",
  "counts": {"high": 5, "medium": 2, "low": 1},
  "violations": [
    {
      "rule": "FTC_DECEPTIVE_CLAIM",
      "name": "Deceptive / Unsubstantiated Claim",
      "severity": "high",
      "category": "FTC Act §5",
      "message": "Guarantee of results/profit is a high-risk deceptive claim under FTC.",
      "fix": "Remove the absolute/guarantee claim ...",
      "snippet": "..."
    }
  ],
  "auto_fix": {"fixed_version": "...", "manual_actions_required": ["..."]},
  "request_id": "a1b2c3d4e5f6"
}
```

## Response headers
| Header | Meaning |
|---|---|
| `X-Request-Id` | Correlation id (send your own `X-Request-Id` to trace) |
| `X-RateLimit-Limit` | Daily limit for the key |
| `X-RateLimit-Remaining` | Calls left today (resets 00:00 UTC) |
| `X-RateLimit-Day` | Current UTC day |

## Errors
Errors share one shape: `{"error": {"code", "message", "request_id"}}`

| HTTP | code | When |
|---|---|---|
| 401 | `unauthorized` | Missing or invalid API key |
| 422 | `validation_error` | Bad request (e.g. empty `text`) |
| 429 | `rate_limited` | Daily limit reached |
| 500 | `server_error` | Unexpected failure |

## CORS
Open by default (for browser demos). Restrict origins with env `CORS_ORIGINS=https://app.example.com,https://other.com`.

## Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000/docs
```

### Tests
```bash
pip install -r requirements-dev.txt
pytest -q          # 17 tests: engine edges, endpoints, auth, rate limit, CORS
```

## Deploy (free options)

### Option A — Render (current host, no card)
1. Push this folder to a GitHub repo
2. New → Web Service → connect repo
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. (optional) Env `PUBLIC_BASE_URL=https://your-host` so the homepage examples use it
6. Free tier gives a public HTTPS URL (first cold request may take ~50 s after idle)

> Note: use Python 3.12+. The free builder's newest Python needs wheels; loose pins (`pydantic>=2.11`) install cleanly where old exact pins fail.

### Option B — Railway / Fly.io
Uses the included Dockerfile; auto-detected.

### Option C — Cloudflare Workers (AI-agent pay-per-call via x402)
Later-stage; needs the x402 adapter.

## MCP (AI agents)
`mcp_server.py` exposes the checker as MCP tools, so agents (Claude Desktop, Cursor, etc.) call it directly.

Tools:
- `check_compliance(text, content_type, is_ai_generated, subject, return_fix)`
- `get_compliance_score(text, content_type, is_ai_generated, subject)`

Run locally (stdio):
```bash
python mcp_server.py
```
Configure a client with `mcp_client_config.example.json` (replace the absolute path).

Remote (multi-agent over network, after deploy):
```bash
python mcp_server.py --transport streamable-http --port 8200
```
Verified end-to-end with a real MCP client session.

## Project layout
```
headless_api/
├── main.py                 # FastAPI app
├── compliance_engine.py    # deterministic rule engine
├── auth_metering.py        # API key auth + daily metering
├── mcp_server.py           # MCP adapter
├── test_contentguard.py    # pytest suite
├── provision_key.py        # issue/manage paid keys
├── requirements*.txt
├── Dockerfile
└── docs/                   # multilingual intros
```

## Status
- [x] Rule engine (FTC / AI Act / CAN-SPAM / GDPR)
- [x] Auto-fix (safe additions)
- [x] FastAPI endpoints + CORS + unified errors + request id
- [x] API key auth + usage metering + rate-limit headers
- [x] 17-test automated suite
- [x] MCP adapter (stdio + streamable-http)
- [x] Public deploy (Render)
- [x] Paid-key provisioning tool
- [ ] RapidAPI listing
- [ ] x402 agent pay-per-call
