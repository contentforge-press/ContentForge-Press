#!/usr/bin/env python3
"""
🔑 ContentGuard 付费 API Key 开通 / 管理工具（变现闭环）
- 在本地 customers.json 记录客户、套餐、key、状态
- 生成强随机正式 key（前缀 cg_live_）
- 输出要粘贴到 Render 环境变量 CONTENTGUARD_API_KEYS 的完整字符串

用法:
  python provision_key.py create --company "Acme Inc" --email hi@acme.com --plan pro
  python provision_key.py list
  python provision_key.py revoke --key cg_live_xxx
  python provision_key.py render-env
"""
import argparse
import datetime
import json
import secrets
import sys
from pathlib import Path

STORE = Path(__file__).parent / "customers.json"

# 套餐 → 每日调用上限
PLANS = {
    "starter": 10_000,
    "pro": 100_000,
    "enterprise": 1_000_000,
}


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def load():
    if STORE.exists():
        return json.loads(STORE.read_text())
    return []


def save(rows):
    STORE.write_text(json.dumps(rows, indent=2))


def gen_key():
    return "cg_live_" + secrets.token_urlsafe(24)


def create(company, email, plan, limit=None, note=""):
    if plan not in PLANS and not limit:
        sys.exit(f"Unknown plan '{plan}'. Choose from {list(PLANS)} or pass --limit.")
    daily = limit or PLANS[plan]
    rows = load()
    if any(r["email"].lower() == email.lower() and r["status"] == "active" for r in rows):
        sys.exit(f"An active key already exists for {email}. Revoke it first if needed.")
    key = gen_key()
    rows.append({
        "company": company,
        "email": email,
        "plan": plan,
        "daily_limit": daily,
        "api_key": key,
        "status": "active",
        "created": now_utc(),
        "note": note,
    })
    save(rows)
    print("✅ Key created")
    print(f"   Company : {company}")
    print(f"   Email   : {email}")
    print(f"   Plan    : {plan} ({daily:,} calls/day)")
    print(f"   API key : {key}")
    print("\nNext: run `python provision_key.py render-env` and paste the value into")
    print("Render → your service → Environment → CONTENTGUARD_API_KEYS, then save (auto-deploys).")
    return key


def list_keys():
    rows = load()
    if not rows:
        print("No customers yet.")
        return
    for r in rows:
        print(f"[{r['status']:8}] {r['company']:24} {r['plan']:10} "
              f"{r['daily_limit']:>9,}/day  {r['api_key']}")


def revoke(key):
    rows = load()
    for r in rows:
        if r["api_key"] == key and r["status"] == "active":
            r["status"] = "revoked"
            r["revoked"] = now_utc()
            save(rows)
            print(f"🗑️  Revoked key for {r['company']} ({key}).")
            print("Re-run `python provision_key.py render-env` and update Render to remove it.")
            return
    sys.exit(f"No active key found matching {key}.")


def render_env():
    rows = [r for r in load() if r["status"] == "active"]
    pairs = ",".join(f"{r['api_key']}:{r['daily_limit']}" for r in rows)
    print("Environment variable: CONTENTGUARD_API_KEYS")
    print("Value (copy the whole line):\n")
    print(pairs or "(no active paid keys)")
    print()


def main():
    p = argparse.ArgumentParser(description="Manage ContentGuard paid API keys.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create")
    c.add_argument("--company", required=True)
    c.add_argument("--email", required=True)
    c.add_argument("--plan", default="starter", choices=list(PLANS))
    c.add_argument("--limit", type=int, default=0, help="Custom daily limit")
    c.add_argument("--note", default="")

    sub.add_parser("list")

    r = sub.add_parser("revoke")
    r.add_argument("--key", required=True)

    sub.add_parser("render-env")

    args = p.parse_args()
    if args.cmd == "create":
        create(args.company, args.email, args.plan, args.limit or None, args.note)
    elif args.cmd == "list":
        list_keys()
    elif args.cmd == "revoke":
        revoke(args.key)
    elif args.cmd == "render-env":
        render_env()


if __name__ == "__main__":
    main()
