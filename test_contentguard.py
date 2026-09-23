"""
✅ ContentGuard 自动化测试套件
覆盖：合规引擎边界、FastAPI 全端点、鉴权/限流、CORS、统一错误格式。
运行: cd headless_api && pytest -q
"""
import pytest
from fastapi.testclient import TestClient

import auth_metering
import main as main_mod
from compliance_engine import analyze_content


# ── 合规样本 & 违规样本 ──────────────────────────────────────────────
CLEAN_EMAIL = """This message was drafted with AI assistance and reviewed by a human.

We just launched a new reporting feature for marketing teams. It might save your team a few hours a week.

You can unsubscribe at any time.

123 Main Street, Suite 400, New York, NY 10001

Best,
Sam Carter"""

BAD_EMAIL = "Earn $10,000 per week guaranteed! Risk-free! Get rich now!"


@pytest.fixture(autouse=True)
def isolated_usage(tmp_path, monkeypatch):
    """把用量文件重定向到临时目录，避免污染真实 usage.json。"""
    f = tmp_path / "usage.json"
    monkeypatch.setattr(auth_metering, "USAGE_FILE", f)
    yield
    if f.exists():
        f.unlink()


@pytest.fixture
def client():
    return TestClient(main_mod.app)


# ── 1. 引擎：合规邮件 100 分 ────────────────────────────────────────
def test_clean_email_scores_100():
    r = analyze_content(CLEAN_EMAIL, content_type="email",
                        is_ai_generated=True, subject="New feature")
    assert r["compliance_score"] == 100
    assert r["is_compliant"] is True
    assert r["counts"]["high"] == 0


# ── 2. 引擎：违规邮件 0 分、5 个高风险 ─────────────────────────────
def test_bad_email_has_five_high():
    r = analyze_content(BAD_EMAIL, content_type="email",
                        is_ai_generated=True, subject="Hello")
    assert r["compliance_score"] == 0
    assert r["is_compliant"] is False
    assert r["counts"]["high"] == 5


# ── 3. 引擎：非AI内容不要求披露 ────────────────────────────────────
def test_non_ai_skips_disclosure():
    r = analyze_content(CLEAN_EMAIL, is_ai_generated=False)
    rules = [v["rule"] for v in r["violations"]]
    assert "AI_DISCLOSURE_MISSING" not in rules


# ── 4. 引擎：非邮件类型不检查 CAN-SPAM 退订 ────────────────────────
def test_ad_does_not_require_unsubscribe():
    r = analyze_content("Buy our new software today.", content_type="ad",
                        is_ai_generated=False)
    rules = [v["rule"] for v in r["violations"]]
    assert "CANSPAM_UNSUBSCRIBE" not in rules


# ── 5. 引擎：误导性主题被标记 ──────────────────────────────────────
def test_misleading_subject_flagged():
    r = analyze_content(CLEAN_EMAIL, subject="Re: your invoice")
    assert any(v["rule"] == "CANSPAM_SUBJECT" for v in r["violations"])


# ── 6. 引擎：空输入不报错 ─────────────────────────────────────────
def test_empty_text_is_safe():
    r = analyze_content("", content_type="email", is_ai_generated=False)
    assert "compliance_score" in r


# ── 7. API：健康检查 ───────────────────────────────────────────────
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == main_mod.VERSION
    assert "uptime_seconds" in body


# ── 8. API：首页可打开 ─────────────────────────────────────────────
def test_home_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "ContentGuard" in r.text


# ── 9. 鉴权：缺 key → 401 统一格式 ─────────────────────────────────
def test_missing_key_401(client):
    r = client.post("/v1/check", json={"text": "hello"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


# ── 10. 鉴权：错 key → 401 ─────────────────────────────────────────
def test_invalid_key_401(client):
    r = client.post("/v1/check", headers={"X-API-Key": "nope"},
                    json={"text": "hello"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


# ── 11. API：正确 key 检测违规邮件 ─────────────────────────────────
def test_check_bad_email(client):
    r = client.post("/v1/check",
                    headers={"X-API-Key": "demo-key-1000"},
                    json={"text": BAD_EMAIL, "content_type": "email",
                          "return_fix": True})
    assert r.status_code == 200
    body = r.json()
    assert body["compliance_score"] == 0
    assert body["counts"]["high"] == 5
    assert body["request_id"]
    assert "fixed_version" in body["auto_fix"]
    assert body["auto_fix"]["manual_actions_required"]  # 欺骗声明需人工
    # 配额响应头
    assert r.headers["X-RateLimit-Limit"] == "1000"


# ── 12. API：合规邮件 100 分 ───────────────────────────────────────
def test_check_clean_email(client):
    r = client.post("/v1/check",
                    headers={"X-API-Key": "demo-key-1000"},
                    json={"text": CLEAN_EMAIL, "subject": "New feature"})
    assert r.status_code == 200
    assert r.json()["compliance_score"] == 100


# ── 13. 校验：空 text → 422 ────────────────────────────────────────
def test_empty_text_422(client):
    r = client.post("/v1/check",
                    headers={"X-API-Key": "demo-key-1000"},
                    json={"text": ""})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


# ── 14. 用量端点 ──────────────────────────────────────────────────
def test_usage_endpoint(client):
    client.post("/v1/check", headers={"X-API-Key": "demo-key-1000"},
                json={"text": "hi there"})
    r = client.get("/v1/usage", headers={"X-API-Key": "demo-key-1000"})
    assert r.status_code == 200
    assert r.json()["calls_today"] == 1
    assert r.json()["daily_limit"] == 1000


# ── 15. 限流：超量 → 429 ───────────────────────────────────────────
def test_rate_limit_429(client, monkeypatch):
    monkeypatch.setitem(auth_metering.PLAN_LIMITS, "lim-key", 1)
    monkeypatch.setitem(main_mod.PLAN_LIMITS, "lim-key", 1)
    h = {"X-API-Key": "lim-key"}
    assert client.post("/v1/check", headers=h, json={"text": "a"}).status_code == 200
    r = client.post("/v1/check", headers=h, json={"text": "b"})
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limited"


# ── 16. CORS：预检通过 ─────────────────────────────────────────────
def test_cors_preflight(client):
    r = client.options("/v1/check", headers={
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-api-key",
    })
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") in ("*", "https://example.com")


# ── 17. request_id 回写 ─────────────────────────────────────────────
def test_request_id_header(client):
    r = client.get("/health", headers={"X-Request-Id": "fixed-id-123"})
    assert r.headers["X-Request-Id"] == "fixed-id-123"
