# Laboratorio 11 - API CRUD con Lambda Authorizer

Autore: Riccardo Gouthier. Regione `us-east-1`, settembre 2026.

## Scenario

API REST per gestire utenti (CRUD su DynamoDB) con un Lambda authorizer che protegge le operazioni di scrittura tramite token.

## Flusso

```
Client --(Authorization: Bearer ...)--> API Gateway (crud-api) --> Lambda simple-authorizer (Allow/Deny)
                                              |
                                              +--> Lambda crud-users --> DynamoDB lab11-users
```

## Step 1 - Tabella DynamoDB

- Tabella: `lab11-users`
- Partition key: `user_id` (String)
- Modalita capacita: On-demand

## Step 2 - Funzione CRUD `crud-users`

| Operazione | Comportamento | Risposta |
|---|---|---|
| `list_users` | `scan` con `Limit=50` | 200 `{users: [...]}` |
| `create_user(body)` | Richiede `name` (altrimenti 400 `name is required`); `user_id` = `str(uuid.uuid4())[:8]`; `email` opzionale (default `''`); `put_item` | 201 con l'item creato |
| `delete_user(user_id)` | `delete_item` con chiave `user_id` | 200 `User {user_id} deleted` |
| `response(status_code, body)` | Costruisce la risposta con `HEADERS` e `json.dumps(body)` | - |

## Step 3 - Lambda authorizer `simple-authorizer`

```python
def lambda_handler(event, context):
    token = event.get('authorizationToken', '')
    method_arn = event.get('methodArn', '')

    if token == 'Bearer my-secret-token-2025':
        effect = 'Allow'
    else:
        effect = 'Deny'

    return {
        'principalId': 'user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': method_arn
            }]
        }
    }
```

Nota: il token e un valore di prova del laboratorio, non una credenziale reale.

## Step 4 - API Gateway `crud-api`

| Risorsa | Metodi |
|---|---|
| `/users` | `GET`, `POST` |
| `/users/{id}` | `GET`, `DELETE` |

Integrazione: Lambda proxy verso `crud-users`. API ID `ox5hmvvvu4`, stage `dev`.

## Step 5 - Configurazione authorizer

| Parametro | Valore |
|---|---|
| Nome | `token-auth` (ID `cvnrgz`) |
| Lambda function | `simple-authorizer` (us-east-1) |
| Lambda event payload | Token |
| Token source | `Authorization` |
| Token validation | None |
| Authorization caching | 300 secondi |

Authorizer `token-auth` assegnato ai metodi `POST /users` e `DELETE /users/{id}`; API ridistribuita (deploy) dopo la modifica.

## Step opzionale - Prova negativa

Chiamate `POST` / `DELETE` senza header `Authorization: Bearer my-secret-token-2025` restituiscono **401/403**.

## Test finale

`POST` da Postman con token e body `{"name": "Alice"}`:

```
request 'https://ox5hmvvvu4.execute-api.us-east-1.amazonaws.com/dev/users' \
  --header 'Authorization: Bearer my-secret-token-2025' \
  --header 'Content-Type: application/json' \
  --body '{"name": "Alice"}'
```

Poi `GET /users`: **200 OK**, 165 ms, 424 B:

```json
{
  "users": [
    { "email": "", "name": "Alice", "user_id": "a4d0f299" }
  ]
}
```

## Prove

| # | Prova | Tipo | Esito atteso |
|---|---|---|---|
| 1 | `POST /users` con token valido | Positiva | 201, utente creato |
| 2 | `GET /users` dopo il POST | Positiva | 200, elenco con Alice |
| 3 | `POST` / `DELETE` senza token | Negativa | 401/403 |

## Conclusioni

1. L'authorizer protegge solo le operazioni di scrittura; le letture restano pubbliche.
2. Il risultato dell'authorizer viene messo in cache 300 s: una modifica del token puo non essere immediata.
3. Un token statico nel codice va bene solo per il laboratorio; in produzione servono JWT/Cognito e segreti gestiti.
