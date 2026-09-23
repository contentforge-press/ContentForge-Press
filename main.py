"""
🌐 无头 API — FastAPI 应用
对外暴露合规检测端点，可被任何软件 / AI Agent 通过 HTTP 调用。
本地运行: uvicorn main:app --host 0.0.0.0 --port 8000
鉴权: X-API-Key 请求头（免费 key: demo-key-1000，每日 1000 次）
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal
import datetime

from compliance_engine import analyze_content, auto_fix
from auth_metering import require_api_key, increment_usage, get_usage_for, PLAN_LIMITS

app = FastAPI(
    title="ContentGuard Headless API",
    description="AI content compliance validation for FTC, EU AI Act, CAN-SPAM and GDPR. Built for software and AI agents.",
    version="0.2.0",
)


class CheckRequest(BaseModel):
    text: str = Field(..., description="The marketing content body to validate.", min_length=1)
    content_type: Literal["email", "ad", "social", "webpage"] = "email"
    is_ai_generated: bool = True
    subject: Optional[str] = ""
    return_fix: bool = False


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html><body style="font-family:system-ui;max-width:760px;margin:60px auto;padding:0 20px">
    <h1>🛡️ ContentGuard Headless API</h1>
    <p>Validate marketing content against <b>FTC, EU AI Act, CAN-SPAM and GDPR</b> in one call.</p>
    <p>👉 <a href="/docs">Open interactive API docs</a></p>
    <h3>Get started</h3>
    <p>Send the header <code>X-API-Key: demo-key-1000</code> (free, 1,000 calls/day).</p>
    <pre style="background:#f4f4f4;padding:14px;border-radius:8px">curl -X POST https://YOUR_HOST/v1/check \\
  -H "X-API-Key: demo-key-1000" \\
  -H "Content-Type: application/json" \\
  -d '{"text":"your copy here","content_type":"email"}'</pre>
    <p style="color:#666">v0.2.0</p>
    </body></html>
    """


@app.get("/health")
def health():
    return {"status": "ok", "service": "contentguard", "time": datetime.datetime.utcnow().isoformat() + "Z"}


@app.get("/v1/usage")
def usage(request: Request, api_key: str = Depends(require_api_key)):
    return {
        "api_key": api_key[:6] + "..." + api_key[-3:],
        "calls_today": get_usage_for(api_key),
        "daily_limit": PLAN_LIMITS[api_key],
        "day_utc": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
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
    }

    if req.return_fix:
        result["auto_fix"] = auto_fix(
            req.text, analysis,
            is_ai_generated=req.is_ai_generated,
            content_type=req.content_type,
        )

    return result
