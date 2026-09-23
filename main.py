"""
🌐 ContentGuard Headless API — FastAPI 应用
对外暴露合规检测端点，可被任何软件 / AI Agent 通过 HTTP 调用。
本地运行: uvicorn main:app --host 0.0.0.0 --port 8000
鉴权: X-API-Key 请求头（免费 key: demo-key-1000，每日 1000 次）
"""
import os
import uuid
import time
import datetime
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from compliance_engine import analyze_content, auto_fix
from auth_metering import require_api_key, increment_usage, get_usage_for, PLAN_LIMITS

VERSION = "0.3.0"
START_TS = time.time()


def get_origin_list():
    raw = os.environ.get("CORS_ORIGINS", "*").strip()
    return [o.strip() for o in raw.split(",")] if raw != "*" else ["*"]


app = FastAPI(
    title="ContentGuard Headless API",
    description="AI content compliance validation for FTC, EU AI Act, CAN-SPAM and GDPR. "
                "Built for software and AI agents.",
    version=VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_origin_list(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 中间件：为每个请求注入 request_id 并回写到响应头
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


# ---------------------------------------------------------------------------
# 统一错误格式：{"error": {code, message, request_id}}
# ---------------------------------------------------------------------------
def _error_body(code: str, message: str, request_id: str):
    return {"error": {"code": code, "message": message, "request_id": request_id}}


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    code_map = {401: "unauthorized", 403: "forbidden", 404: "not_found",
                422: "validation_error", 429: "rate_limited", 500: "server_error"}
    code = code_map.get(exc.status_code, "error")
    detail = exc.detail
    message = detail if isinstance(detail, str) else str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(code, message, getattr(request.state, "request_id", "")),
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exc_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(x) for x in first.get("loc", []) if x != "body")
    message = f"Invalid request field '{loc}': {first.get('msg', 'validation failed')}" if loc else "Invalid request body."
    return JSONResponse(
        status_code=422,
        content=_error_body("validation_error", message, getattr(request.state, "request_id", "")),
    )


@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=_error_body("server_error", "Internal server error.", getattr(request.state, "request_id", "")),
    )


class CheckRequest(BaseModel):
    text: str = Field(..., description="The marketing content body to validate.", min_length=1)
    content_type: Literal["email", "ad", "social", "webpage"] = "email"
    is_ai_generated: bool = True
    subject: Optional[str] = ""
    return_fix: bool = False


HOME_HTML = """
<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ContentGuard Headless API</title>
<style>
 body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0b1020;color:#e6e9f0}
 .wrap{max-width:820px;margin:0 auto;padding:56px 22px}
 h1{font-size:34px;margin:0 0 8px}.sub{color:#9aa3bd;font-size:17px;margin:0 0 28px}
 .card{background:#131a2e;border:1px solid #232c47;border-radius:14px;padding:22px 24px;margin:18px 0}
 h2{font-size:18px;margin:0 0 12px} code{background:#0b1020;border:1px solid #26304d;border-radius:6px;padding:2px 7px}
 pre{background:#0b1020;border:1px solid #26304d;border-radius:10px;padding:15px;overflow:auto;font-size:13px;line-height:1.55}
 a{color:#6ea8fe}.pill{display:inline-block;background:#16315e;color:#cfe0ff;border-radius:999px;padding:3px 11px;font-size:12px;margin-right:6px}
 ul{line-height:1.9} .foot{color:#6b7594;font-size:13px;margin-top:30px}
</style></head><body><div class="wrap">
<h1>🛡️ ContentGuard Headless API</h1>
<p class="sub">Validate AI marketing copy against <b>FTC · EU AI Act · CAN-SPAM · GDPR</b> in one call. Built for software and AI agents.</p>
<div><span class="pill">0–100 score</span><span class="pill">violation locations</span><span class="pill">auto-fixed version</span><span class="pill">MCP ready</span></div>
<div class="card"><h2>Get started</h2>
<p>Send header <code>X-API-Key: demo-key-1000</code> — free, 1,000 calls/day. Interactive docs: <a href="/docs">/docs</a></p>
<pre>curl -X POST __HOME__/v1/check \\
  -H "X-API-Key: demo-key-1000" \\
  -H "Content-Type: application/json" \\
  -d '{"text":"Earn $10,000 guaranteed in a week!","content_type":"email"}'</pre></div>
<div class="card"><h2>Python</h2>
<pre>import requests
r = requests.post("__HOME__/v1/check",
  headers={"X-API-Key": "demo-key-1000"},
  json={"text": "your copy", "content_type": "email", "return_fix": True})
print(r.json()["compliance_score"], r.json()["violations"])</pre></div>
<div class="card"><h2>What it returns</h2>
<ul><li><code>compliance_score</code> — 0 (risky) to 100 (clean)</li>
<li><code>violations[]</code> — rule, severity, matched text, location, legal basis, suggested fix</li>
<li><code>counts</code> / <code>summary</code> — quick triage</li>
<li><code>auto_fix</code> — safe repaired version (when <code>return_fix=true</code>)</li></ul></div>
<p class="foot">ContentGuard Headless API · v__VER__ · status: <a href="/health">/health</a></p>
</div></body></html>
"""


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    home_url = os.environ.get("PUBLIC_BASE_URL", str(request.base_url).rstrip("/"))
    return (HOME_HTML.replace("__HOME__", home_url).replace("__VER__", VERSION))


@app.get("/health")
def health():
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "status": "ok",
        "service": "contentguard",
        "version": VERSION,
        "time": now.isoformat(),
        "uptime_seconds": round(time.time() - START_TS, 1),
    }


@app.get("/v1/usage")
def usage(request: Request, api_key: str = Depends(require_api_key)):
    return {
        "api_key": api_key[:6] + "..." + api_key[-3:],
        "calls_today": get_usage_for(api_key),
        "daily_limit": PLAN_LIMITS[api_key],
        "day_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "request_id": request.state.request_id,
    }


@app.post("/v1/check")
def check(req: CheckRequest, request: Request, api_key: str = Depends(require_api_key)):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=422, detail="text must not be empty")

    analysis = analyze_content(
        req.text,
        content_type=req.content_type,
        is_ai_generated=req.is_ai_generated,
        subject=req.subject or "",
    )

    used = increment_usage(api_key)
    limit = PLAN_LIMITS[api_key]

    result = {
        "compliance_score": analysis["compliance_score"],
        "is_compliant": analysis["is_compliant"],
        "summary": analysis["summary"],
        "counts": analysis["counts"],
        "violations": analysis["violations"],
        "request_id": request.state.request_id,
    }

    if req.return_fix:
        result["auto_fix"] = auto_fix(
            req.text, analysis,
            is_ai_generated=req.is_ai_generated,
            content_type=req.content_type,
        )

    # 用量信息也通过响应头暴露，方便集成方不增请求即可读取配额
    return JSONResponse(result, headers={
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(0, limit - used)),
        "X-RateLimit-Day": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    })
