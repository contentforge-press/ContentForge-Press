"""
🔑 API Key 鉴权 + 用量计量
- 通过 X-API-Key 请求头校验
- demo key 每日有限额；正式 key（环境变量配置）可设更高额度
- 用量记录在 usage.json（首版够用；规模化后换 Redis/数据库）
"""
import os
import json
import datetime
from pathlib import Path
from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader

USAGE_FILE = Path(__file__).parent / "usage.json"

# key -> 每日配额。demo 用于 RapidAPI/免费试用引流。
PLAN_LIMITS = {
    "demo-key-1000": 1000,   # 免费试用
    "test-key": 100000,      # 我们自己测试
}

# 正式付费 key 通过环境变量 CONTENTGUARD_API_KEYS 配置，格式 key:limit,key:limit
# 例:  abc123:50000,xyz789:100000
for pair in os.environ.get("CONTENTGUARD_API_KEYS", "").split(","):
    pair = pair.strip()
    if not pair:
        continue
    if ":" in pair:
        k, lim = pair.split(":", 1)
        PLAN_LIMITS[k.strip()] = int(lim.strip())
    else:
        PLAN_LIMITS[pair] = 100000  # 默认正式 key 高额度

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _today():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def _load_usage():
    if USAGE_FILE.exists():
        try:
            return json.loads(USAGE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_usage(data):
    USAGE_FILE.write_text(json.dumps(data, indent=2))


def get_usage_for(key):
    data = _load_usage()
    return data.get(key, {}).get(_today(), 0)


def increment_usage(key):
    data = _load_usage()
    day = _today()
    data.setdefault(key, {})[day] = data.get(key, {}).get(day, 0) + 1
    _save_usage(data)
    return data[key][day]


async def require_api_key(request: Request, api_key: str = Security(api_key_header)):
    """依赖注入：校验 key 并检查当日配额。"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Pass it via the 'X-API-Key' header. Get a free key at the homepage.",
        )
    if api_key not in PLAN_LIMITS:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    limit = PLAN_LIMITS[api_key]
    used = get_usage_for(api_key)
    if used >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit of {limit} calls reached for this key. Resets at 00:00 UTC.",
        )

    # 把信息挂到 request.state，供端点写响应头 / 计数
    request.state.api_key = api_key
    request.state.limit = limit
    request.state.used = used
    return api_key
