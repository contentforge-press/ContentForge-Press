# ContentGuard — API de cumplimiento sin interfaz

**En línea:** https://contentguard-api-bjex.onrender.com · **Documentación interactiva:** [/docs](https://contentguard-api-bjex.onrender.com/docs)

Verifica contenido de marketing (correo / anuncio / redes / página web) frente a:
**FTC (EE. UU.) · Ley de IA de la UE · CAN-SPAM · GDPR**, en una sola llamada.

## Qué resuelve
La mayoría de los correos de marketing ya se escriben con IA. Las normativas exigen **revelar el uso de IA**, prohíben **promesas de ingresos garantizados / afirmaciones absolutas** y obligan a incluir **método de cancelación + dirección postal real**. ContentGuard lo revisa todo en un endpoint y devuelve una versión corregida y segura, sin que usted construya una interfaz ni mantenga reglas.

## Autenticación
Todos los endpoints `/v1/*` requieren la cabecera `X-API-Key`.
- Clave gratuita: `demo-key-1000` (1.000 llamadas/día)
- Claves de pago: variable de entorno `CONTENTGUARD_API_KEYS=clave:limite,clave:limite`
- Consultar consumo: `GET /v1/usage`

## Inicio rápido
```bash
curl -X POST https://contentguard-api-bjex.onrender.com/v1/check \
  -H "X-API-Key: demo-key-1000" \
  -H "Content-Type: application/json" \
  -d '{"text":"Guarantee you earn $3000/week, risk free. Buy now.","content_type":"email","return_fix":true}'
```

## Qué devuelve
- `compliance_score`: 0 (riesgoso) a 100 (limpio)
- `violations[]`: regla, gravedad, texto detectado, ubicación, base legal y corrección sugerida
- `counts` / `summary`: evaluación rápida
- `auto_fix`: versión corregida segura (con `return_fix=true`)

## Endpoints
- `GET /` página de inicio
- `GET /health` estado (versión y tiempo activo)
- `GET /v1/usage` consumo de la clave actual
- `POST /v1/check` ejecutar la verificación

## Errores
Formato único: `{"error": {"code", "message", "request_id"}}`

| HTTP | code | Cuándo |
|---|---|---|
| 401 | `unauthorized` | Falta la clave o es incorrecta |
| 422 | `validation_error` | Petición no válida (p. ej. `text` vacío) |
| 429 | `rate_limited` | Límite diario alcanzado |
| 500 | `server_error` | Fallo del servicio |

## MCP (agentes de IA)
`mcp_server.py` expone el verificador como herramientas MCP; los agentes (Claude Desktop, Cursor, etc.) pueden llamarlo directamente. Ejecución local: `python mcp_server.py`.
