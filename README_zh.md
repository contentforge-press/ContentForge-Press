# ContentGuard — 无头合规 API

**线上地址：** https://contentguard-api-bjex.onrender.com · **交互文档：** [/docs](https://contentguard-api-bjex.onrender.com/docs)

一次 API 调用，即可校验营销内容（邮件 / 广告 / 社媒 / 网页）是否符合：
**美国 FTC · 欧盟 AI Act · CAN-SPAM · GDPR**。

## 它解决什么问题
现在大部分营销邮件由 AI 撰写。法规要求**披露 AI 使用**、禁止**收益保证 / 绝对化用语**，并强制**退订方式 + 真实邮政地址**。ContentGuard 用一个接口全部检查，并返回一个安全的修复版本——你不用做界面，也不用维护规则。

## 鉴权
所有 `/v1/*` 接口都要带 `X-API-Key` 请求头。
- 免费 key：`demo-key-1000`（每天 1,000 次）
- 付费 key：设置环境变量 `CONTENTGUARD_API_KEYS=key:limit,key:limit`
- 查用量：`GET /v1/usage`

## 快速上手
```bash
curl -X POST https://contentguard-api-bjex.onrender.com/v1/check \
  -H "X-API-Key: demo-key-1000" \
  -H "Content-Type: application/json" \
  -d '{"text":"Guarantee you earn $3000/week, risk free. Buy now.","content_type":"email","return_fix":true}'
```

## 返回什么
- `compliance_score`：0（高危）到 100（干净）
- `violations[]`：每条违规的规则、严重度、命中原文、位置、法规依据、修改建议
- `counts` / `summary`：快速判断
- `auto_fix`：安全修复版（当 `return_fix=true`）

## 接口
- `GET /` 落地页
- `GET /health` 健康检查（含版本号与运行时长）
- `GET /v1/usage` 当前 key 用量
- `POST /v1/check` 执行合规检查

## 错误码
错误统一格式：`{"error": {"code", "message", "request_id"}}`

| HTTP | code | 触发情况 |
|---|---|---|
| 401 | `unauthorized` | 缺少或错误的 API key |
| 422 | `validation_error` | 请求不合法（如 text 为空） |
| 429 | `rate_limited` | 超过每日限额 |
| 500 | `server_error` | 服务异常 |

## MCP（AI Agent）
`mcp_server.py` 把检测能力暴露为 MCP 工具，Agent（Claude Desktop、Cursor 等）可直接调用。本地运行：`python mcp_server.py`。
