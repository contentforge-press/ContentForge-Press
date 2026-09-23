# ContentGuard — API de conformité sans interface

**En ligne :** https://contentguard-api-bjex.onrender.com · **Documentation interactive :** [/docs](https://contentguard-api-bjex.onrender.com/docs)

Vérifiez un contenu marketing (e-mail / publicité / réseaux / page web) au regard de :
**FTC (États-Unis) · Loi européenne sur l'IA · CAN-SPAM · RGPD**, en un seul appel.

## Le problème résolu
La plupart des e-mails marketing sont désormais rédigés par IA. Les réglementations exigent de **divulguer l'usage de l'IA**, interdisent les **promesses de revenus garantis / affirmations absolues** et imposent un **mécanisme de désabonnement + une adresse postale réelle**. ContentGuard vérifie tout cela via un point de terminaison unique et renvoie une version corrigée et sûre — sans interface à créer ni règles à maintenir.

## Authentification
Tous les endpoints `/v1/*` nécessitent l'en-tête `X-API-Key`.
- Clé gratuite : `demo-key-1000` (1 000 appels/jour)
- Clés payantes : variable d'environnement `CONTENTGUARD_API_KEYS=cle:limite,cle:limite`
- Consulter l'usage : `GET /v1/usage`

## Démarrage rapide
```bash
curl -X POST https://contentguard-api-bjex.onrender.com/v1/check \
  -H "X-API-Key: demo-key-1000" \
  -H "Content-Type: application/json" \
  -d '{"text":"Guarantee you earn $3000/week, risk free. Buy now.","content_type":"email","return_fix":true}'
```

## Résultats renvoyés
- `compliance_score` : de 0 (risqué) à 100 (conforme)
- `violations[]` : règle, gravité, texte détecté, emplacement, base légale, correction suggérée
- `counts` / `summary` : diagnostic rapide
- `auto_fix` : version corrigée sûre (avec `return_fix=true`)

## Endpoints
- `GET /` page d'accueil
- `GET /health` état de santé (version et durée d'activité)
- `GET /v1/usage` usage de la clé actuelle
- `POST /v1/check` lancer la vérification

## Erreurs
Format unique : `{"error": {"code", "message", "request_id"}}`

| HTTP | code | Quand |
|---|---|---|
| 401 | `unauthorized` | Clé manquante ou invalide |
| 422 | `validation_error` | Requête invalide (p. ex. `text` vide) |
| 429 | `rate_limited` | Limite quotidienne atteinte |
| 500 | `server_error` | Erreur du service |

## MCP (agents IA)
`mcp_server.py` expose le vérificateur sous forme d'outils MCP ; les agents (Claude Desktop, Cursor, etc.) peuvent l'appeler directement. Lancement local : `python mcp_server.py`.
