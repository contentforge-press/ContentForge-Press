# ContentGuard — Headless-Compliance-API

**Online:** https://contentguard-api-bjex.onrender.com · **Interaktive Dokumentation:** [/docs](https://contentguard-api-bjex.onrender.com/docs)

Prüfen Sie Marketing-Inhalte (E-Mail / Anzeige / Social Media / Webseite) gegen:
**US-FTC · EU-KI-Gesetz · CAN-SPAM · DSGVO** – in einem einzigen Aufruf.

## Welches Problem gelöst wird
Die meisten Marketing-E-Mails werden heute mit KI geschrieben. Die Vorschriften verlangen eine **Offenlegung des KI-Einsatzes**, verbieten **garantierte Einkommensversprechen / absolute Aussagen** und schreiben **Abmeldemöglichkeit + echte Postanschrift** vor. ContentGuard prüft all das über einen einzigen Endpunkt und liefert eine sichere korrigierte Fassung – ohne eigene Oberfläche und ohne selbst Regeln zu pflegen.

## Authentifizierung
Alle `/v1/*`-Endpunkte benötigen den Header `X-API-Key`.
- Kostenloser Schlüssel: `demo-key-1000` (1.000 Aufrufe/Tag)
- Kostenpflichtige Schlüssel: Umgebungsvariable `CONTENTGUARD_API_KEYS=schluessel:limit,schluessel:limit`
- Nutzung abfragen: `GET /v1/usage`

## Schnellstart
```bash
curl -X POST https://contentguard-api-bjex.onrender.com/v1/check \
  -H "X-API-Key: demo-key-1000" \
  -H "Content-Type: application/json" \
  -d '{"text":"Guarantee you earn $3000/week, risk free. Buy now.","content_type":"email","return_fix":true}'
```

## Was zurückgegeben wird
- `compliance_score`: 0 (riskant) bis 100 (sauber)
- `violations[]`: Regel, Schweregrad, gefundener Text, Stelle, Rechtsgrundlage, Korrekturvorschlag
- `counts` / `summary`: schnelle Einordnung
- `auto_fix`: sichere korrigierte Fassung (bei `return_fix=true`)

## Endpunkte
- `GET /` Startseite
- `GET /health` Gesundheitscheck (Version und Betriebszeit)
- `GET /v1/usage` Nutzung des aktuellen Schlüssels
- `POST /v1/check` Prüfung durchführen

## Fehler
Einheitliches Format: `{"error": {"code", "message", "request_id"}}`

| HTTP | code | Wann |
|---|---|---|
| 401 | `unauthorized` | Schlüssel fehlt oder ist ungültig |
| 422 | `validation_error` | Ungültige Anfrage (z. B. leerer `text`) |
| 429 | `rate_limited` | Tageslimit erreicht |
| 500 | `server_error` | Dienstfehler |

## MCP (KI-Agenten)
`mcp_server.py` stellt die Prüfung als MCP-Tools bereit; Agenten (Claude Desktop, Cursor usw.) können sie direkt aufrufen. Lokaler Start: `python mcp_server.py`.
