# ContentGuard — ヘッドレス・コンプライアンスAPI

**本番URL:** https://contentguard-api-bjex.onrender.com · **対話型ドキュメント:** [/docs](https://contentguard-api-bjex.onrender.com/docs)

マーケティングコンテンツ（メール / 広告 / SNS / ウェブページ）を1回のAPI呼び出しで以下の観点から検証します：
**米国FTC · EU AI法 · CAN-SPAM · GDPR**。

## 解決する課題
現在、大半のマーケティングメールはAIで作成されています。法規制では**AI利用の開示**が義務付けられ、**収益保証 / 断定的な表現**は禁止され、**配信停止手段と実在の住所**が必要です。ContentGuardは単一のエンドポイントでこれらをすべてチェックし、安全な修正版を返します。UI構築やルールの保守は不要です。

## 認証
すべての `/v1/*` エンドポイントに `X-API-Key` ヘッダーが必要です。
- 無料キー：`demo-key-1000`（1日1,000回）
- 有料キー：環境変数 `CONTENTGUARD_API_KEYS=キー:上限,キー:上限`
- 使用量の確認：`GET /v1/usage`

## クイックスタート
```bash
curl -X POST https://contentguard-api-bjex.onrender.com/v1/check \
  -H "X-API-Key: demo-key-1000" \
  -H "Content-Type: application/json" \
  -d '{"text":"Guarantee you earn $3000/week, risk free. Buy now.","content_type":"email","return_fix":true}'
```

## レスポンス
- `compliance_score`：0（危険）〜100（クリーン）
- `violations[]`：ルール、重大度、一致テキスト、位置、法的根拠、修正案
- `counts` / `summary`：迅速な判定
- `auto_fix`：安全な修正版（`return_fix=true` の場合）

## エンドポイント
- `GET /` ランディングページ
- `GET /health` ヘルスチェック（バージョンと稼働時間）
- `GET /v1/usage` 現在のキーの使用量
- `POST /v1/check` 検証を実行

## エラー
共通フォーマット：`{"error": {"code", "message", "request_id"}}`

| HTTP | code | 発生条件 |
|---|---|---|
| 401 | `unauthorized` | APIキーが未指定または不正 |
| 422 | `validation_error` | リクエスト不正（例：`text`が空） |
| 429 | `rate_limited` | 1日の上限に到達 |
| 500 | `server_error` | サービス障害 |

## MCP（AIエージェント）
`mcp_server.py` が検証機能をMCPツールとして公開し、エージェント（Claude Desktop、Cursorなど）から直接呼び出せます。ローカル実行：`python mcp_server.py`。
