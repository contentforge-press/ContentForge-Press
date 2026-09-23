# ContentGuard — Headless Compliance API

Validate English marketing content (email / ad / social / webpage) against:
**FTC · EU AI Act · CAN-SPAM · GDPR** — in one HTTP call.

## Auth (v0.2.0)
All `/v1/*` endpoints require an `X-API-Key` header.
- Free key: `demo-key-1000` (1,000 calls/day)
- Paid keys: set env `CONTENTGUARD_API_KEYS=key:limit,key:limit`
- Check usage: `GET /v1/usage`
- Usage is logged to `usage.json` (swap for Redis at scale).

## Endpoints
- `GET /` landing page
- `GET /health` health check
- `GET /v1/usage` usage for the current key
- `POST /v1/check` run compliance check

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
  "violations": [ ... ],
  "auto_fix": { "fixed_version": "...", "manual_actions_required": [ ... ] }
}
```

## Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000/docs
```

## Deploy (free options)

### Option A — Render (easiest, no card)
1. Push this folder to a GitHub repo
2. New → Web Service → connect repo
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Free tier gives a public HTTPS URL

### Option B — Railway / Fly.io
Uses the included Dockerfile; auto-detected.

### Option C — Cloudflare Workers (scale / AI-agent pay-per-call via x402)
Later-stage; needs the MCP/x402 adapter.

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

## Status
- [x] Rule engine (FTC / AI Act / CAN-SPAM / GDPR)
- [x] Auto-fix (safe additions)
- [x] FastAPI endpoints + tests
- [x] API key auth + usage metering
- [x] MCP adapter (stdio + streamable-http)
- [ ] Public deploy
- [ ] RapidAPI listing
- [ ] x402 agent pay-per-call
