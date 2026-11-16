# Laboratorio 10 - API Gateway REST con Lambda

Autore: Riccardo Gouthier. Regione `us-east-1`, data 18 settembre 2026.

## Scenario

Esporre una Lambda tramite una REST API di API Gateway (risorsa `/hello`, metodo GET), testarla dalla console e dal browser, verificare le intestazioni CORS.

## Flusso

```
Client --GET /hello?name=...--> API Gateway (student-api) --proxy--> Lambda api-hello
```

## Step 1 - Creazione Lambda

- Funzione: `api-hello`
- Runtime: Python 3.14, package Zip

## Step 2 - Creazione API

| Parametro | Valore |
|---|---|
| Nome | `student-api` |
| Descrizione | api di prova per il lab 10 Java Serverless |
| ID | `ja4wdab3x9` |
| Protocollo | REST |
| Endpoint type | Regional |
| Security policy | TLS_1_0 |
| Creata | 2026-09-18 |

## Step 3 - Risorsa e metodo

- Risorsa: `/hello`
- Metodo: `GET`, integrazione Lambda proxy (verso `api-hello`)
- Authorization: NONE; API key required: False

## Step 4 - Test in console

Richiesta `/hello?name=Riccardo`:

| Campo | Valore |
|---|---|
| Status | 200 |
| Latenza | 269 ms |
| Body | `{"message": "Hello, Riccardo!", "method": "GET", "path": "/hello"}` |
| Header risposta | `Access-Control-Allow-Origin: *`, `Content-Type: application/json` |

## Step 5 - Deploy API

- Stage: `Lab-10-Serverless`
- URL: `https://ja4wdab3x9.execute-api.us-east-1.amazonaws.com/Lab-10-Serverless/hello?name=Student`
- Risposta dal browser: `{"message": "Hello, Student!", "method": "GET", "path": "/hello"}`

## Step 6 - CORS

Verifica da DevTools (Network) su `hello?name=Riccardo`:

| Campo | Valore |
|---|---|
| Request method | GET |
| Status | 200 OK |
| `Access-Control-Allow-Origin` | `*` |
| `Content-Type` | `application/json` |
| `Content-Length` | 66 |

## Conclusioni

1. Con l'integrazione proxy la Lambda controlla status, header e body della risposta.
2. L'header `Access-Control-Allow-Origin: *` presente nella risposta consente le chiamate cross-origin dal browser.
3. Le modifiche a metodi e risorse diventano attive solo dopo il deploy su uno stage.

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
mkdir -p lab10 && cd lab10

# Step 1 - Funzione api-hello (il lab usa Python 3.12; nel deliverable e stata usata una versione piu recente)
cat > lambda_function.py <<'EOF'
import json

def lambda_handler(event, context):
    params = event.get('queryStringParameters') or {}
    name = params.get('name', 'World')

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Hello, {name}!',
            'method': event.get('httpMethod'),
            'path': event.get('path')
        })
    }
EOF
zip -q function.zip lambda_function.py
aws lambda create-function --function-name api-hello --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip
aws lambda wait function-active-v2 --function-name api-hello
FN_ARN=$(aws lambda get-function --function-name api-hello --query Configuration.FunctionArn --output text)

# Step 2 - REST API regionale student-api
API_ID=$(aws apigateway create-rest-api --name student-api --description "api di prova per il lab 10" --endpoint-configuration types=REGIONAL --query id --output text)
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/'].id" --output text)

# Step 3 - Risorsa /hello e metodo GET con Lambda proxy
RES_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part hello --query id --output text)
aws apigateway put-method --rest-api-id $API_ID --resource-id $RES_ID --http-method GET --authorization-type NONE
aws apigateway put-integration --rest-api-id $API_ID --resource-id $RES_ID --http-method GET --type AWS_PROXY --integration-http-method POST --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$FN_ARN/invocations
aws lambda add-permission --function-name api-hello --statement-id apigw-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:$ACC:$API_ID/*/GET/hello"

# Step 4 - Test del metodo (equivale al Test della console)
aws apigateway test-invoke-method --rest-api-id $API_ID --resource-id $RES_ID --http-method GET --path-with-query-string "/hello?name=Riccardo" --query "[status,body]" --output text

# Step 5 - Deploy sullo stage Lab-10-Serverless e chiamata dal client
aws apigateway create-deployment --rest-api-id $API_ID --stage-name Lab-10-Serverless
URL=https://$API_ID.execute-api.us-east-1.amazonaws.com/Lab-10-Serverless/hello
curl -s "$URL?name=Student"; echo

# Step 6 - Header CORS nella risposta (Access-Control-Allow-Origin: *)
curl -si "$URL?name=Riccardo" | grep -iE "^(HTTP|access-control|content-type|content-length)"
cd ..
```

### Cleanup

```bash
aws apigateway delete-rest-api --rest-api-id $API_ID
aws lambda delete-function --function-name api-hello
aws logs delete-log-group --log-group-name /aws/lambda/api-hello
```
