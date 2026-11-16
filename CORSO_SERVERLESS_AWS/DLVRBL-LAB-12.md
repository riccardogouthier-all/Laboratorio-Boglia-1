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

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
mkdir -p lab12 && cd lab12

# ---------- Parte A - Versioni, stage e monitoraggio ----------

# Step 1 - Funzione stage-demo
cat > lambda_function.py <<'EOF'
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
EOF
zip -q stage.zip lambda_function.py
aws lambda create-function --function-name stage-demo --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://stage.zip
aws lambda wait function-active-v2 --function-name stage-demo
SD_ARN=$(aws lambda get-function --function-name stage-demo --query Configuration.FunctionArn --output text)

# Step 2 - API multi-stage-api con /status (GET) e stage dev e prod
API_ID=$(aws apigateway create-rest-api --name multi-stage-api --endpoint-configuration types=REGIONAL --query id --output text)
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/'].id" --output text)
RES_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part status --query id --output text)
aws apigateway put-method --rest-api-id $API_ID --resource-id $RES_ID --http-method GET --authorization-type NONE
aws apigateway put-integration --rest-api-id $API_ID --resource-id $RES_ID --http-method GET --type AWS_PROXY --integration-http-method POST --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$SD_ARN/invocations
aws lambda add-permission --function-name stage-demo --statement-id apigw-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:$ACC:$API_ID/*/GET/status"

# Step 3 - Stage variables (environment) al deploy
aws apigateway create-deployment --rest-api-id $API_ID --stage-name dev  --variables environment=development
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod --variables environment=production

# Step 4 - Log di accesso sullo stage dev
aws logs create-log-group --log-group-name api-access-logs-dev
LOG_ARN=$(aws logs describe-log-groups --log-group-name-prefix api-access-logs-dev --query "logGroups[0].arn" --output text | sed 's/:\*$//')
aws apigateway update-account --patch-operations op=replace,path=/cloudwatchRoleArn,value=$ROLE_ARN
aws apigateway update-stage --rest-api-id $API_ID --stage-name dev --patch-operations \
  op=replace,path=/accessLogSettings/destinationArn,value=$LOG_ARN \
  'op=replace,path=/accessLogSettings/format,value={"requestId":"$context.requestId","ip":"$context.identity.sourceIp","method":"$context.httpMethod","status":"$context.status","latency":"$context.responseLatency"}'

# Step 5 - Traffico di test (5 richieste valide + 1 percorso inesistente che produce 403)
for i in 1 2 3 4 5; do curl -s https://$API_ID.execute-api.us-east-1.amazonaws.com/dev/status; echo; done
curl -s https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/status; echo
curl -s -o /dev/null -w "percorso inesistente: %{http_code}\n" https://$API_ID.execute-api.us-east-1.amazonaws.com/dev/nonesiste

# Step 6 - Logs Insights: conteggio per status
sleep 20
QID=$(aws logs start-query --log-group-name api-access-logs-dev --start-time $(date -d '-30 minutes' +%s) --end-time $(date +%s) --query-string 'fields @timestamp, @message | parse @message '"'"'"status":"*"'"'"' as status | stats count() by status' --query queryId --output text)
sleep 8
aws logs get-query-results --query-id $QID --query "results" --output json

# ---------- Parte B - Caching, monitoraggio avanzato e X-Ray ----------

# Step 7 - Funzione cache-demo e API cache-test-api con /products (GET)
cat > lambda_function.py <<'EOF'
import json
import time

def lambda_handler(event, context):
    category = (event.get('queryStringParameters') or {}).get('category', 'all')
    time.sleep(0.5)   # simula un backend lento: la cache lo rende visibile
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'category': category, 'generated_at': time.time()})
    }
EOF
zip -q cache.zip lambda_function.py
aws lambda create-function --function-name cache-demo --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://cache.zip --memory-size 128 --timeout 3
aws lambda wait function-active-v2 --function-name cache-demo
CD_ARN=$(aws lambda get-function --function-name cache-demo --query Configuration.FunctionArn --output text)

API2=$(aws apigateway create-rest-api --name cache-test-api --endpoint-configuration types=REGIONAL --query id --output text)
ROOT2=$(aws apigateway get-resources --rest-api-id $API2 --query "items[?path=='/'].id" --output text)
PROD_ID=$(aws apigateway create-resource --rest-api-id $API2 --parent-id $ROOT2 --path-part products --query id --output text)
aws apigateway put-method --rest-api-id $API2 --resource-id $PROD_ID --http-method GET --authorization-type NONE --request-parameters method.request.querystring.category=false
aws apigateway put-integration --rest-api-id $API2 --resource-id $PROD_ID --http-method GET --type AWS_PROXY --integration-http-method POST --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$CD_ARN/invocations --cache-key-parameters method.request.querystring.category
aws lambda add-permission --function-name cache-demo --statement-id apigw-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:$ACC:$API2/*/GET/products"

# Step 8 - Stage dev con cache cluster, log, metriche dettagliate e X-Ray
aws apigateway create-deployment --rest-api-id $API2 --stage-name dev --cache-cluster-enabled --cache-cluster-size 0.5
aws logs create-log-group --log-group-name cache-test-api-log-group
LOG2=$(aws logs describe-log-groups --log-group-name-prefix cache-test-api-log-group --query "logGroups[0].arn" --output text | sed 's/:\*$//')
aws apigateway update-stage --rest-api-id $API2 --stage-name dev --patch-operations \
  op=replace,path=/*/*/logging/loglevel,value=INFO \
  op=replace,path=/*/*/metrics/enabled,value=true \
  op=replace,path=/*/*/caching/enabled,value=true \
  op=replace,path=/tracingEnabled,value=true \
  op=replace,path=/accessLogSettings/destinationArn,value=$LOG2 \
  'op=replace,path=/accessLogSettings/format,value={"requestId":"$context.requestId","status":"$context.status","latency":"$context.responseLatency"}'

# Step 10 - X-Ray sulla funzione Lambda
aws lambda update-function-configuration --function-name cache-demo --tracing-config Mode=Active --region us-east-1
aws lambda get-function-configuration --function-name cache-demo --region us-east-1 --query TracingConfig

# Step 11 - Sei richieste con query string diverse (cache miss) e cache hit ripetendo la stessa
for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w "miss$i: %{http_code} %{time_total}s\n" "https://$API2.execute-api.us-east-1.amazonaws.com/dev/products?category=xray$i"; done
for i in 1 2 3; do curl -s -o /dev/null -w "hit$i: %{http_code} %{time_total}s\n" "https://$API2.execute-api.us-east-1.amazonaws.com/dev/products?category=xray1"; done
cd ..
```

Il cache cluster di API Gateway e a pagamento orario: eliminare lo stage a fine lab.

### Cleanup

```bash
aws apigateway delete-stage --rest-api-id $API2 --stage-name dev    # ferma il cache cluster
aws apigateway delete-rest-api --rest-api-id $API2
aws apigateway delete-rest-api --rest-api-id $API_ID
aws lambda delete-function --function-name cache-demo
aws lambda delete-function --function-name stage-demo
aws logs delete-log-group --log-group-name api-access-logs-dev
aws logs delete-log-group --log-group-name cache-test-api-log-group
aws logs delete-log-group --log-group-name /aws/lambda/cache-demo
aws logs delete-log-group --log-group-name /aws/lambda/stage-demo
```
