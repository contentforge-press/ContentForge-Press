# ContentGuard — Pricing & Fulfillment

## Plans (direct, self-serve)
| Plan | Price | Calls/day | Calls/mo (≈) | For |
|---|---|---|---|---|
| Starter | $49/mo | 10,000 | 300k | Small AI writing tools |
| Pro | $199/mo | 100,000 | 3M | Email/sales platforms |
| Enterprise | custom | 1,000,000+ | — | High-volume / embedded OEMS |

Annual: 2 months free. One-off pilots / 30-day trials: free via a time-boxed provisioned key.

Also offered for direct partnerships:
- **Embedded / revenue share** — integrated inside a partner product; negotiated monthly floor + per-call.
- **Pay-per-call (future)** — x402 so autonomous agents pay micro-fees automatically.

## Fulfillment (no manual infra work)
1. Customer agrees → `python provision_key.py create --company X --email Y --plan pro`
2. `python provision_key.py render-env` → copy value
3. Render → Environment → `CONTENTGUARD_API_KEYS` → save (auto-deploy, ~1 min)
4. Send the customer their key + docs link. They self-serve `/docs`.
5. Monitor usage with `GET /v1/usage` (and response headers `X-RateLimit-*`).
6. Non-payment / churn → `provision_key.py revoke`, re-run `render-env`, update Render.

## Payments
- Receive via **Payoneer** (same collection rails as project 1; the *brand & ledger stay separate*).
- Invoice terms: monthly prepaid; enterprise net-15.

## Separation rule (project 1 vs project 2)
Different brand (ContentGuard), identity (Sam Carter), mailbox (contentguard@coze.email), repo, ledger and customers. Only the cash-out vehicle (Payoneer) is shared, tracked in separate columns/records.
