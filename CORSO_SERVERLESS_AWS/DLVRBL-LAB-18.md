# Laboratorio 18 - AWS SAM, CloudFormation e monitoraggio CloudWatch

Autore: Riccardo Gouthier. Regione `us-east-1`, 13 novembre 2026.

## Scenario

Parte A: API serverless di gestione ordini definita come codice con AWS SAM (API Gateway + Lambda + DynamoDB). Parte B: seconda applicazione SAM deployata via CloudFormation e monitorata con CloudWatch (Logs Insights, allarme, dashboard).

## Parte A - Introduzione a SAM

### Flusso

```
Client --HTTP--> API Gateway (Prod) --> Lambda CreateOrderFunction / GetOrderFunction --> DynamoDB sam-lab18-orders
```

### Step 1 - Inizializzare il progetto

Da CloudShell: `sam init --runtime python3.12 --name order-api --app-template hello-world --package-type Zip --dependency-manager pip --no-tracing --no-application-insights --no-interactive`. Il progetto contiene `events`, `hello_world`, `README.md`, `samconfig.toml`, `template.yaml`, `tests`. Versione SAM CLI installata: 1.166.2.

### Step 2 - Template SAM

`template.yaml` (`Transform: AWS::Serverless-2016-10-31`) con:

| Risorsa | Tipo | Dettaglio |
|---|---|---|
| `CreateOrderFunction` | `AWS::Serverless::Function` | Handler `app.create_order`, evento Api `POST /orders` |
| `GetOrderFunction` | `AWS::Serverless::Function` | Handler `app.get_order`, evento Api `GET /orders/{order_id}` |
| `OrdersTable` | `AWS::DynamoDB::Table` | `sam-lab18-orders`, partition key `order_id` (String), on-demand |

- `Globals`: runtime `python3.12`, timeout 10 s, memoria 128 MB, variabile `TABLE_NAME: !Ref OrdersTable`
- Ruolo di esecuzione: `LabRole` (`!Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:role/LabRole`) perche il Learner Lab non permette di creare ruoli IAM
- Output `ApiUrl`: `https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/`

Codice in `src/app.py`: `create_order` genera un `order_id` di 8 caratteri (`uuid4`), salva `customer`, `total`, `status: created` e risponde 200; `get_order` legge per `order_id` e risponde 200 oppure 404 `Order not found`; errori inattesi -> 500.

### Step 3 - Validazione e build

- `sam validate --region us-east-1`: `template.yaml is a valid SAM Template`
- `sam build`: `Build Succeeded` (nessun `requirements.txt`: build senza dipendenze), artefatti in `.aws-sam/build`

### Step 4 - Deploy

`sam deploy --stack-name order-api-lab18 --region us-east-1 --capabilities CAPABILITY_IAM --resolve-s3 --no-disable-rollback --confirm-changeset --save-params`

- Bucket S3 di appoggio creato automaticamente (`aws-sam-cli-managed-default-samclisourcebucket-...`)
- Changeset: aggiunti `CreateOrderFunction`, `GetOrderFunction`, i permessi Lambda, `OrdersTable`, `ServerlessRestApi`, il deployment e lo stage `Prod`
- Prima conferma con `y` minuscola respinta ("invalid input"), accettata la seconda con `Y`
- Esito: `CREATE_COMPLETE`; output `ApiUrl` con endpoint `https://r0dwlkwasj.execute-api.us-east-1.amazonaws.com/Prod/`

### Step 5 - Test dell'API live

`POST /orders` con `{"customer": "Bob", "total": 150}`. Scan di `sam-lab18-orders` (1 item, 2 RCU):

| order_id | customer | status | total |
|---|---|---|---|
| `72ec3f53` | Bob | created | 150 |

L'ordine creato via API risulta persistito in DynamoDB. Le chiamate `GET /orders/{id}` e `GET /orders/nonexistent` (atteso 404) sono nello script ma il loro output non e riportato negli screenshot del PDF: non verificate qui.

## Parte B - CloudFormation, deploy automatizzato e monitoraggio

### Step 6 - Deploy dell'applicazione monitorata

Progetto `monitored-api`: funzione `ProcessFunction` (handler `app.handler`, `POST /process`, `LabRole`). L'azione nel body decide il comportamento: `fast` risponde subito, `slow` attende 3 s, `error` solleva `ValueError`, `random` fallisce circa 30% delle volte.

Stack `monitored-api-lab18`: `CREATE_COMPLETE`, creato il 13 novembre 2026, 12:04:19 (UTC+01:00); descrizione `Monitored API - Lab 18`; drift `NOT_CHECKED`; protezione dalla terminazione disattivata.

### Step 7 - Generare traffico

Chiamate parallele a `POST /process`:

| Azione | Chiamate | Risposta osservata |
|---|---|---|
| `fast` | 10 | `{"status": "ok", "action": "fast"}` |
| `slow` | 3 | `{"status": "ok", "action": "slow"}` |
| `error` | 5 | errore Lambda (500 da API Gateway) |

### Step 8 - Stack CloudFormation

Risorse dello stack (da `describe-stack-resources`): `ProcessFunction`, `ProcessFunctionProcessPermissionProd`, `ServerlessRestApi`, `ServerlessRestApiDeployment...`, `ServerlessRestApiProdStage`. Gli eventi mostrano la sequenza `CREATE_IN_PROGRESS` -> `CREATE_COMPLETE` fino allo stack, dalle 11:04:34 alle 11:04:40 UTC.

### Step 9 - Logs Insights

Nello script e definita la funzione `q()` (query CloudWatch Logs Insights con `jq`) per tre analisi: righe `REPORT` ordinate per durata, conteggio di invocazioni lente e cold start, ultimi messaggi `ERROR`.

Esito: tutte e tre le chiamate hanno restituito `jq: error ... Cannot index string with string value "value"`. Il filtro `jq` non era compatibile con il formato dei risultati; i dati delle query non sono quindi stati letti. Correzione possibile: leggere `.[] | map(.field + "=" + .value)` solo dopo aver verificato lo stato `Complete` della query, oppure usare `--output text`.

### Step 10 - Allarme CloudWatch

Allarme `lab18-lambda-errors`: namespace `AWS/Lambda`, metrica `Errors` per la funzione, statistica `Sum`, periodo 300 s, 1 periodo di valutazione, soglia `> 2`, dati mancanti `notBreaching`. Stato al momento della verifica: `INSUFFICIENT_DATA` (soglia 2.0), perche l'allarme era appena stato creato.

### Step 11 - Dashboard

Dashboard `lab18-serverless` creata con `put-dashboard` (`DashboardValidationMessages: []`) con tre widget: Invocations (somma, 60 s), Errors (somma, 60 s), Duration media (valore singolo, 300 s). Presente nell'elenco `list-dashboards`.

## Prove

| # | Prova | Tipo | Esito |
|---|---|---|---|
| 1 | `sam validate` e `sam build` | Positiva | Template valido, build riuscita |
| 2 | `sam deploy` order-api | Positiva | Stack `CREATE_COMPLETE`, `ApiUrl` ottenuto |
| 3 | `POST /orders` | Positiva | Item `72ec3f53` presente in DynamoDB |
| 4 | Traffico `fast`/`slow`/`error` su `monitored-api` | Positiva | Risposte `ok`; 5 invocazioni in errore generate |
| 5 | Query Logs Insights | Fallita | Errore `jq`, risultati non letti |
| 6 | Allarme errori | Parziale | Creato, stato `INSUFFICIENT_DATA` |

## Conclusioni

1. SAM riduce la definizione serverless a poche righe e crea API Gateway, Lambda, permessi e tabella in un solo stack CloudFormation.
2. `sam deploy` con `--confirm-changeset` mostra le risorse che verranno create prima dell'esecuzione.
3. Logs, allarmi e dashboard di CloudWatch coprono invocazioni, errori e durata; l'allarme richiede qualche periodo di dati per uscire da `INSUFFICIENT_DATA`.
4. Limite: l'analisi con Logs Insights non e stata completata per l'errore nel filtro `jq`; le metriche mostrate nell'allarme e nella dashboard non sono state verificate con valori reali.

Procedura di esecuzione in CLI Cloudshell:

Lo script usa SAM CLI (preinstallato in CloudShell) e `LabRole` come ruolo di esecuzione.

```bash
export AWS_DEFAULT_REGION=us-east-1
ACC=$(aws sts get-caller-identity --query Account --output text)
sam --version
aws iam get-role --role-name LabRole --query Role.Arn --output text

cd ~
sam init --runtime python3.12 --name order-api --app-template hello-world --package-type Zip --dependency-manager pip --no-tracing --no-application-insights --no-interactive
cd order-api && ls

cat > template.yaml <<'EOF'
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Order API - SAM Lab 18

Globals:
  Function:
    Runtime: python3.12
    Timeout: 10
    MemorySize: 128
    Environment:
      Variables:
        TABLE_NAME: !Ref OrdersTable

Resources:
  CreateOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.create_order
      CodeUri: src/
      Role: !Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:role/LabRole
      Events:
        CreateOrder:
          Type: Api
          Properties:
            Path: /orders
            Method: post

  GetOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.get_order
      CodeUri: src/
      Role: !Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:role/LabRole
      Events:
        GetOrder:
          Type: Api
          Properties:
            Path: /orders/{order_id}
            Method: get

  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: sam-lab18-orders
      AttributeDefinitions:
        - AttributeName: order_id
          AttributeType: S
      KeySchema:
        - AttributeName: order_id
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST

Outputs:
  ApiUrl:
    Description: API endpoint URL
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
EOF

mkdir -p src
cat > src/app.py <<'EOF'
import json
import os
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def create_order(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = str(uuid.uuid4())[:8]

        item = {
            'order_id': order_id,
            'customer': body.get('customer', 'unknown'),
            'total': str(body.get('total', 0)),
            'status': 'created'
        }

        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Order created', 'order': item})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_order(event, context):
    try:
        order_id = event['pathParameters']['order_id']

        response = table.get_item(Key={'order_id': order_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Order not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'order': item})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
EOF

sam validate --region us-east-1
sam build

sam deploy --stack-name order-api-lab18 --region us-east-1 --capabilities CAPABILITY_IAM --resolve-s3 --no-disable-rollback --confirm-changeset --save-params

aws cloudformation describe-stacks --stack-name order-api-lab18 --query "Stacks[0].StackStatus" --output text
API_URL=$(aws cloudformation describe-stacks --stack-name order-api-lab18 --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
echo $API_URL

RES=$(curl -s -X POST ${API_URL}orders -H "Content-Type: application/json" -d '{"customer": "Bob", "total": 150}')
echo $RES
OID=$(echo $RES | jq -r .order.order_id)
curl -s ${API_URL}orders/$OID
curl -s -o /dev/null -w "%{http_code}\n" ${API_URL}orders/nonexistent

cd ~
sam init --runtime python3.12 --name monitored-api --app-template hello-world --package-type Zip --dependency-manager pip --no-tracing --no-application-insights --no-interactive
cd monitored-api

cat > template.yaml <<'EOF'
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Monitored API - Lab 18

Resources:
  ProcessFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler
      CodeUri: src/
      Runtime: python3.12
      Timeout: 10
      MemorySize: 128
      Role: !Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:role/LabRole
      Events:
        Process:
          Type: Api
          Properties:
            Path: /process
            Method: post

Outputs:
  ApiUrl:
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
EOF

mkdir -p src
cat > src/app.py <<'EOF'
import json
import time
import random

def handler(event, context):
    body = json.loads(event.get('body', '{}'))
    action = body.get('action', 'fast')

    if action == 'error':
        raise ValueError("Simulated error for monitoring test")
    elif action == 'slow':
        time.sleep(3)
    elif action == 'random':
        if random.random() < 0.3:
            raise RuntimeError("Random failure")

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'ok', 'action': action})
    }
EOF

sam build
sam deploy --stack-name monitored-api-lab18 --region us-east-1 --capabilities CAPABILITY_IAM --resolve-s3 --no-disable-rollback --confirm-changeset --save-params

API2=$(aws cloudformation describe-stacks --stack-name monitored-api-lab18 --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
FN=$(aws cloudformation describe-stack-resource --stack-name monitored-api-lab18 --logical-resource-id ProcessFunction --query StackResourceDetail.PhysicalResourceId --output text)
LG=/aws/lambda/$FN
echo $API2 $FN

for i in {1..10}; do curl -s -X POST "${API2}process" -H "Content-Type: application/json" -d '{"action": "fast"}' & done; wait
for i in {1..3};  do curl -s -X POST "${API2}process" -H "Content-Type: application/json" -d '{"action": "slow"}' & done; wait
for i in {1..5};  do curl -s -X POST "${API2}process" -H "Content-Type: application/json" -d '{"action": "error"}' & done; wait

aws cloudformation describe-stack-resources --stack-name monitored-api-lab18 --query "StackResources[].[LogicalResourceId,ResourceType,ResourceStatus]" --output table
aws cloudformation describe-stack-events --stack-name monitored-api-lab18 --query "reverse(StackEvents)[].[Timestamp,LogicalResourceId,ResourceStatus]" --output table

q() {
  local QID=$(aws logs start-query --log-group-name "$LG" --start-time $(date -d '-1 hour' +%s) --end-time $(date +%s) --query-string "$1" --query queryId --output text)
  sleep 5
  aws logs get-query-results --query-id $QID --query "results[]" --output json | jq -r '.[] | map(.field + "=" + .value) | join(" | ")'
}

q 'filter @type = "REPORT" | sort @duration desc | limit 10'
q 'filter @type = "REPORT" | stats count() as total, sum(@duration > 1000) as slow, count(@initDuration) as coldStarts'
q 'filter @message like /ERROR/ | fields @timestamp, @message | sort @timestamp desc | limit 10'

aws cloudwatch put-metric-alarm --alarm-name lab18-lambda-errors --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value=$FN --statistic Sum --period 300 --evaluation-periods 1 --threshold 2 --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching
aws cloudwatch describe-alarms --alarm-names lab18-lambda-errors --query "MetricAlarms[].[AlarmName,StateValue,Threshold]" --output table

cat > dash.json <<EOF
{
  "widgets": [
    {"type":"metric","x":0,"y":0,"width":12,"height":6,
     "properties":{"title":"Invocations","view":"timeSeries","region":"us-east-1","stat":"Sum","period":60,
       "metrics":[["AWS/Lambda","Invocations","FunctionName","$FN"]]}},
    {"type":"metric","x":12,"y":0,"width":12,"height":6,
     "properties":{"title":"Errors","view":"timeSeries","region":"us-east-1","stat":"Sum","period":60,
       "metrics":[["AWS/Lambda","Errors","FunctionName","$FN"]]}},
    {"type":"metric","x":0,"y":6,"width":12,"height":4,
     "properties":{"title":"Duration (Average)","view":"singleValue","region":"us-east-1","stat":"Average","period":300,
       "metrics":[["AWS/Lambda","Duration","FunctionName","$FN"]]}}
  ]
}
EOF

aws cloudwatch put-dashboard --dashboard-name lab18-serverless --dashboard-body file://dash.json
aws cloudwatch list-dashboards --query "DashboardEntries[].DashboardName" --output text
```

### Cleanup

```bash
aws cloudwatch delete-dashboards --dashboard-names lab18-serverless
aws cloudwatch delete-alarms --alarm-names lab18-lambda-errors
aws cloudformation delete-stack --stack-name monitored-api-lab18
aws cloudformation delete-stack --stack-name order-api-lab18
aws cloudformation wait stack-delete-complete --stack-name monitored-api-lab18
aws cloudformation wait stack-delete-complete --stack-name order-api-lab18
```
