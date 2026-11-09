# Laboratorio 12 - Versioni, Stage, Caching e Monitoraggio API

Autore: Riccardo Gouthier. Regione `us-east-1`, 19 ottobre 2026.

## Parte A - Versioni, Stage e Monitoraggio API

### Step 1 - Funzione Lambda `stage-demo`

```python
import json
import os

def lambda_handler(event, context):
    stage = event.get('requestContext', {}).get('stage', 'unknown')

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Hello from {stage} stage!',
            'stage': stage,
            'function_version': context.function_version
        })
    }
```

### Step 2 - API con stage multipli

- API: `multi-stage-api` (ID `rq0xcn5br4`), risorsa `/status`, metodo `GET`.
- Stage creati: `dev` e `prod`.
- Dev: cache cluster provisioned, default method-level caching **Active**. Prod (dallo screenshot): cache cluster e default method-level caching **Inactive**.
- Limiti stage: rate 10000, burst 5000.
- Deployment attivi: `dev` = `v5191a` (14:22), `prod` = `eviq4m` (14:23).

### Step 3 - Stage variables

| Stage | Nome | Valore |
|---|---|---|
| `prod` | `environment` | `production` |
| `dev` | `environment` | (impostata anche per `dev`) |

### Step 4 - Log di accesso

1. Ruolo CloudWatch: in API Gateway -> Settings, CloudWatch log role ARN impostato su `LabRole`.
2. Log group creato: `api-access-logs-dev`.
3. Stage `dev`: logging level "Error and info logs", access logging **Active** verso `api-access-logs-dev`.

Formato dei log di accesso:

```json
{"requestId":"$context.requestId","ip":"$context.identity.sourceIp","method":"$context.httpMethod","status":"$context.status","latency":"$context.responseLatency"}
```

### Step 5 - Test e traffico

| URL | Risposta |
|---|---|
| `https://rq0xcn5br4.execute-api.us-east-1.amazonaws.com/dev/status` | `{"message": "Hello from dev stage!", "stage": "dev", "function_version": "$LATEST"}` |
| `https://rq0xcn5br4.execute-api.us-east-1.amazonaws.com/prod/status` | `{"message": "Hello from prod stage!", "stage": "prod", "function_version": "$LATEST"}` |

### Step 6 - Analisi dei log (Logs Insights)

Query sul log group `api-access-logs-dev` (ultimi 30 minuti):

```
fields @timestamp, @message
| parse @message '"status":"*"' as status
| stats count() by status
```

| status | count |
|---|---|
| 200 | 5 |
| 403 | 1 |

## Parte B - Caching, Monitoraggio Avanzato e Revisione

### Step 7 - Infrastruttura per il caching

- API: `cache-test-api` (ID `vhpizbfc2c`), risorsa `/products`, metodo `GET` (integrazione Lambda, nessuna autorizzazione, API key non richiesta).
- Funzione Lambda `cache-demo`: Python 3.12, 128 MB, timeout 3 s, ruolo `LabRole`.
- Deploy sullo stage `dev` (deployment `plqdj8`, 14:54).

### Step 8 - Abilitare il caching

- Stage `dev`: cache cluster **Provisioned**, default method-level caching **Active**.
- URL: `https://vhpizbfc2c.execute-api.us-east-1.amazonaws.com/dev`

### Step 9 - Logging e X-Ray su API Gateway

- Log group per `cache-test-api`: `cache-test-api-log-group`.
- Stage `dev` -> Edit logs and tracing: logging "Errors and info logs", **Detailed metrics** attivo, **X-Ray tracing** attivo, **Access logging** attivo verso `cache-test-api-log-group`.

### Step 10 - X-Ray sulla funzione Lambda

```
aws lambda update-function-configuration --function-name cache-demo --tracing-config Mode=Active --region us-east-1
aws lambda get-function-configuration --function-name cache-demo --region us-east-1 --query TracingConfig
```

Risultato: `"TracingConfig": { "Mode": "Active" }`.

### Step 11 - Ping alla Lambda

Sei richieste con query string diversa (ogni valore genera una chiave di cache diversa, quindi una cache miss):

```
for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w "miss$i: %{http_code} %{time_total}s\n" "https://vhpizbfc2c.execute-api.us-east-1.amazonaws.com/dev/products?category=xray$i"; done
```

| Richiesta | Status | Tempo |
|---|---|---|
| miss1 | 200 | 0,775138 s |
| miss2 | 200 | 0,542250 s |
| miss3 | 200 | 0,552028 s |
| miss4 | 200 | 0,556631 s |
| miss5 | 200 | 0,537894 s |
| miss6 | 200 | 0,540394 s |

## Conclusioni

1. Gli stage permettono di servire lo stesso backend con configurazioni diverse (stage variables, caching, logging).
2. I log di accesso in formato JSON si interrogano con Logs Insights (es. conteggio per status code: 5 x 200, 1 x 403).
3. La prima richiesta e piu lenta (0,775 s) delle successive (~0,54 s); ogni richiesta con query string diversa e una cache miss e raggiunge la Lambda.
4. X-Ray va attivato sia sullo stage API Gateway sia sulla funzione Lambda per tracciare l'intera catena.
