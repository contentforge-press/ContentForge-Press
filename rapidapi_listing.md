# RapidAPI Listing Kit — ContentGuard

上架前的全部文案/配置都在这里。登录 [rapidapi.com](https://rapidapi.com) → 提供者后台（My APIs → Add a New API）逐项粘贴即可。

> 注意：RapidAPI 需要一个账号（可 Google 登录）并做一次提供者邮箱验证，这一步必须人工接管；约 10 分钟。上架后免费引流，不产生费用。

## 1. Identity
- **API name:** ContentGuard — AI Marketing Compliance
- **Short name / slug:** contentguard
- **Category:** Email, Marketing, Artificial Intelligence
- **Website:** https://contentguard-api-bjex.onrender.com
- **Logo:** 深色底 + 🛡️，见 `docs/`（上架时可先用 emoji/盾牌图标）

## 2. Tagline & Description
**Short description (≤120 chars):**
Validate AI marketing copy against FTC, EU AI Act, CAN-SPAM & GDPR. Score, violations and auto-fix in one call.

**Full description:**
ContentGuard is a headless compliance API for any AI writing or email product. Send English marketing copy (email, ad, social, webpage) and get back a 0–100 compliance score, every violation with its location and legal basis, and an auto-fixed version.

It checks:
- EU AI Act / FTC — AI-generated content disclosure
- FTC Act §5 — guaranteed-earnings, absolute "100%", risk-free and get-rich-quick claims
- CAN-SPAM — unsubscribe mechanism, physical postal address, non-misleading subject
- GDPR — data-rights / privacy references for EU recipients

Deterministic rule engine, sub-second, no training data stored, MCP-compatible. Built for software and AI agents.

## 3. Endpoints (define in the dashboard)
Base URL: `https://contentguard-api-bjex.onrender.com`

| Name | Method | Path | Auth |
|---|---|---|---|
| Check content | POST | `/v1/check` | RapidAPI proxy header |
| Get usage | GET | `/v1/usage` | RapidAPI proxy header |
| Health | GET | `/health` | none |

Example body for `/v1/check`:
```json
{"text":"Earn $10,000/week guaranteed, risk free!","content_type":"email","is_ai_generated":true,"subject":"Hello","return_fix":true}
```

> Integration tip: RapidAPI terminates its own auth at the gateway and forwards requests. If the gateway cannot inject our `X-API-Key`, point the listed backend at a dedicated provisioned key (create one with `provision_key.py create --company RapidAPI --plan enterprise`, then set it on the Render service) so proxied calls are accepted.

## 4. Pricing plans (RapidAPI quota)
| Plan | Price | Quota/month | Hard limit | Overage |
|---|---|---|---|---|
| Basic | $0 | 1,000 | 1,000 | — |
| Pro | $29 | 50,000 | 50,000 | $0.001/call |
| Scale | $99 | 250,000 | 250,000 | $0.0006/call |
| Enterprise | custom | custom | — | contact |

Set **Rate limiting** to the matching quota; return `X-RateLimit-*` headers already provided by the API.

## 5. Docs / quickstart to paste
Use the multilingual intros in `docs/` (zh/es/fr/de/ja) and the curl + Python snippets from the root `README.md`. Add the RapidAPI generated code-snippet headers (`X-RapidAPI-Key`, `X-RapidAPI-Host`).

## 6. Launch checklist
- [ ] Account verified as provider
- [ ] Base URL + 3 endpoints added, `/health` returns 200
- [ ] Auth mode selected (proxy forwards a valid key)
- [ ] `/v1/check` returns score for the example body
- [ ] 4 pricing tiers entered
- [ ] Description + category + logo
- [ ] Publish (Public) → submit to marketplace index
