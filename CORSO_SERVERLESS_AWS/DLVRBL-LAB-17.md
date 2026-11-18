# Laboratorio 17 - Step Functions: gestione errori e integrazioni dirette

Autore: Riccardo Gouthier. Regione `us-east-1`, 13 novembre 2026.

## Scenario

Due workflow: (1) elaborazione ordini con `Retry` e `Catch` per errori transienti e definitivi; (2) workflow con integrazioni SDK dirette (DynamoDB e S3) senza funzioni Lambda intermedie.

## Parte 1 - Gestione degli errori

### Flusso

```
ValidateOrder --> ProcessPayment --> OrderConfirmed (Succeed)
      | Catch            | Retry (RuntimeError) poi Catch
      +--------> HandleFailure --> OrderFailed (Fail)
```

### Step 1 - Funzioni Lambda

Runtime Python 3.12, ruolo `LabRole`:

| Funzione | Comportamento |
|---|---|
| `validate-order-v2` | `ValueError` se `total <= 0`, altrimenti `status: validated` |
| `process-payment` | Se `simulate_error` e vero, con probabilita 50% solleva `RuntimeError` ("Payment service temporarily unavailable"); altrimenti restituisce `payment_id` `PAY-{order_id}` e `status: paid` |
| `handle-failure` | Registra l'errore nei log e restituisce `status: failed`, `error_handled: true` |

### Step 2 - State machine `order-processor-v2`

Tipo Standard, stato `Active`, creata il 13 novembre 2026, 11:32:40 (UTC+01:00).

| Stato | Configurazione errori |
|---|---|
| `ValidateOrder` | `Catch` su `States.ALL`, `ResultPath: $.error`, -> `HandleFailure` |
| `ProcessPayment` | `Retry` su `RuntimeError`: intervallo 2 s, massimo 3 tentativi, `BackoffRate` 2.0 (attese 2 s, 4 s, 8 s); poi `Catch` su `States.ALL` -> `HandleFailure` |
| `HandleFailure` | Task Lambda -> `OrderFailed` |
| `OrderFailed` | `Fail`, `Error: OrderProcessingFailed`, `Cause: The order could not be processed after all retry attempts` |

### Step 3 - Ordine valido senza errori

`exec-ord-100`, input `{"order_id":"ORD-100","total":150,"simulate_error":false}`: `Succeeded`, 0,772 s, 5 transizioni. Percorso `ValidateOrder` -> `ProcessPayment` -> `OrderConfirmed`; `HandleFailure` e `OrderFailed` non eseguiti.

### Step 4 - Errori transienti e analisi dei retry

`exec-ord-200` (`total` 200, `simulate_error: true`): `Succeeded` in 0,401 s. Output: `payment_id` `PAY-ORD-200`, `status` `paid`. Il pagamento non ha fallito al primo tentativo (probabilità 50%), quindi non si e attivato nessun retry.

Per osservare i retry sono state lanciate 5 esecuzioni `exec-retry-1..5` con `simulate_error: true`:

| Esecuzione | Esito | Durata | Lettura |
|---|---|---|---|
| `exec-retry-1` | Succeeded | 2,478 s | 1 retry (attesa iniziale di 2 s) |
| `exec-retry-2` | Succeeded | 0,297 s | nessun errore |
| `exec-retry-3` | Succeeded | 0,319 s | nessun errore |
| `exec-retry-4` | Succeeded | 0,315 s | nessun errore |
| `exec-retry-5` | Succeeded | 2,511 s | 1 retry (attesa iniziale di 2 s) |

La durata di circa 2,5 s indica un retry dopo `IntervalSeconds: 2`. La lettura per `retry-1` e `retry-5` e dedotta dalla durata; la cronologia degli eventi `TaskFailed`/`TaskScheduled` non è riportata in questo documento. Per leggerla: `aws stepfunctions get-execution-history --execution-arn ARN --query "events[?type=='TaskFailed' || type=='TaskScheduled'].[timestamp,type]"`: due `TaskScheduled` separati da un `TaskFailed` confermano il retry.

### Step 5 - Ordine non valido

`exec-ord-300`, input `{"order_id":"ORD-300","total":-50}`: `Failed` in 0,543 s.

- Errore: `OrderProcessingFailed` nello stato `OrderFailed`, causa `The order could not be processed after all retry attempts`. Il testo della causa è fuorviante per questo caso: l'ordine con `total` negativo è stato respinto subito dalla validazione (`ValueError` in `ValidateOrder`, durata 0,543 s) e non ha mai provato i retry, che riguardano solo `ProcessPayment` e `RuntimeError`
- `ValidateOrder` risulta "Caught error" (arancione): l'errore `ValueError` è stato intercettato dal `Catch`
- `ProcessPayment` non eseguito; `HandleFailure` eseguito con `error_handled: true` e messaggio `Order ORD-300 failed and has been logged for review`

Elenco esecuzioni della macchina (8 in tutto): `exec-ord-100`, `exec-ord-200`, `exec-retry-1..5` Succeeded; `exec-ord-300` Failed.

## Parte 2 - Integrazioni SDK dirette

### Step 6 - Risorse e state machine `direct-integration-demo`

- Tabella DynamoDB `lab17-orders` (partition key `order_id`, on-demand)
- Bucket S3 `lab17-receipts-riccardogouthier`
- Log group CloudWatch `step-functions-lab17`, livello di log `ALL` con dati di esecuzione inclusi

| Stato | Integrazione | Azione |
|---|---|---|
| `SaveOrder` | `arn:aws:states:::dynamodb:putItem` | Scrive `order_id`, `customer`, `total`, `status: confirmed` |
| `SaveReceipt` | `arn:aws:states:::aws-sdk:s3:putObject` | Scrive `receipts/{order_id}.json` |
| `OrderComplete` | Succeed | fine |

Nessuna funzione Lambda: Step Functions chiama direttamente DynamoDB e S3.

### Step 7 - Esecuzione e verifica

`exec-ord-500`, input `{"order_id":"ORD-500","customer":"Alice","total":199.99}`: `Succeeded` in 0,357 s, 5 transizioni. Secondo ordine `exec-ord-501` (`Bob`, `49.99`).

Scan di `lab17-orders` (2 item, 2 RCU):

| order_id | customer | status | total |
|---|---|---|---|
| `ORD-501` | Bob | confirmed | 49.99 |
| `ORD-500` | Alice | confirmed | 199.99 |

Cartella `receipts/` del bucket:

| Oggetto | Tipo | Dimensione | Ultima modifica |
|---|---|---|---|
| `ORD-500.json` | json | 77 B | 13 novembre 2026, 11:34:49 |
| `ORD-501.json` | json | 74 B | 13 novembre 2026, 11:34:59 |

### Step 8 - Log e metriche

Sequenza degli eventi per `exec-ord-501` letta dal log group (`filter-log-events`):

```
ExecutionStarted
TaskStateEntered SaveOrder -> TaskScheduled -> TaskStarted -> TaskSucceeded -> TaskStateExited SaveOrder
TaskStateEntered SaveReceipt -> TaskScheduled -> TaskStarted -> TaskSucceeded -> TaskStateExited SaveReceipt
SucceedStateEntered OrderComplete -> SucceedStateExited OrderComplete
ExecutionSucceeded
```

Nel log gli eventi mostrano `resource: putItem` (`dynamodb`) e `resource: putObject` (`aws-sdk:s3`). In CloudWatch Metrics (namespace Step Functions, Execution Metrics) per `direct-integration-demo` sono disponibili 8 metriche: `ExecutionsStarted`, `ExecutionsSucceeded`, `ExecutionsFailed`, `ExecutionsAborted`, `ExecutionThrottled`, `ExecutionsTimedOut`, `ExecutionTime`, `OpenExecutionCount`. Nessun allarme configurato.

## Prove

| # | Prova | Tipo | Esito |
|---|---|---|---|
| 1 | Ordine valido senza errori | Positiva | Percorso diretto, 5 transizioni |
| 2 | Ordini con `simulate_error: true` | Positiva (retry) | Tutti `Succeeded`; 2 su 5 con durata ~2,5 s (retry) |
| 3 | Ordine con `total` negativo | Negativa | `Catch` -> `HandleFailure` -> `OrderFailed` |
| 4 | Workflow con integrazioni dirette | Positiva | Item in DynamoDB e ricevuta in S3 per ogni ordine |

## Conclusioni

1. `Retry` con `BackoffRate` gestisce errori transienti senza codice aggiuntivo; `Catch` incanala i fallimenti definitivi verso un handler e uno stato `Fail` esplicito.
2. `ResultPath: $.error` conserva l'input originale e aggiunge l'errore, così `handle-failure` conosce l'ordine e la causa.
3. Le integrazioni SDK dirette eliminano le Lambda di collegamento: meno codice e meno costi per operazioni semplici su DynamoDB e S3.
4. Il logging `ALL` con dati di esecuzione permette di ricostruire il percorso, ma può registrare dati sensibili: da valutare in produzione.
5. Limite delle prove: nelle 5 esecuzioni si è visto al massimo 1 retry (durata ~2,5 s); non è stato osservato il caso con 2 o 3 retry (attese 2 s, 4 s, 8 s) né l'esaurimento di tutti i tentativi con passaggio al `Catch` su `HandleFailure`. Con probabilità di errore 50% per tentativo, l'esaurimento di 3 tentativi avviene in circa 1 esecuzione su 8: serve lanciare più esecuzioni per osservarlo.

Procedura di esecuzione in CLI Cloudshell:

Il parametro `sleep 25` lascia il tempo ai retry (2 s, 4 s, 8 s). I risultati dei retry variano perché l'errore è casuale (50%).

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
echo $ROLE_ARN $ACC

mkdir -p lab17 && cd lab17

cat > validate.py <<'EOF'
import json

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)
    simulate_error = event.get('simulate_error', False)

    if total <= 0:
        raise ValueError(f"Invalid total: {total}")

    return {
        'order_id': order_id,
        'total': total,
        'status': 'validated',
        'simulate_error': simulate_error
    }
EOF

cat > payment.py <<'EOF'
import json
import random

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)
    simulate_error = event.get('simulate_error', False)

    # Simulate transient failure (50% chance if simulate_error is True)
    if simulate_error and random.random() < 0.5:
        raise RuntimeError(f"Payment service temporarily unavailable for order {order_id}")

    return {
        'order_id': order_id,
        'total': total,
        'payment_id': f'PAY-{order_id}',
        'status': 'paid'
    }
EOF

cat > failure.py <<'EOF'
import json

def lambda_handler(event, context):
    error = event.get('error', {})
    order_id = event.get('order_id', 'unknown')

    print(f"FAILURE HANDLER: Order {order_id}")
    print(f"Error: {json.dumps(error)}")

    return {
        'order_id': order_id,
        'status': 'failed',
        'error_handled': True,
        'message': f'Order {order_id} failed and has been logged for review'
    }
EOF

for p in "validate validate-order-v2" "payment process-payment" "failure handle-failure"; do
  set -- $p
  cp $1.py lambda_function.py
  zip -q $1.zip lambda_function.py
  aws lambda create-function --function-name $2 --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://$1.zip --query "[FunctionName,Runtime]" --output text
  aws lambda wait function-active-v2 --function-name $2
done
cd ..
aws lambda list-functions --query "Functions[?FunctionName=='validate-order-v2'||FunctionName=='process-payment'||FunctionName=='handle-failure'].[FunctionName,Runtime]" --output table

cat > order-v2.asl.json <<'EOF'
{
  "Comment": "Order processing with error handling",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:validate-order-v2",
      "Catch": [
        {"ErrorEquals": ["States.ALL"], "ResultPath": "$.error", "Next": "HandleFailure"}
      ],
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:process-payment",
      "Retry": [
        {"ErrorEquals": ["RuntimeError"], "IntervalSeconds": 2, "MaxAttempts": 3, "BackoffRate": 2.0}
      ],
      "Catch": [
        {"ErrorEquals": ["States.ALL"], "ResultPath": "$.error", "Next": "HandleFailure"}
      ],
      "Next": "OrderConfirmed"
    },
    "OrderConfirmed": {"Type": "Succeed"},
    "HandleFailure": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:handle-failure",
      "Next": "OrderFailed"
    },
    "OrderFailed": {
      "Type": "Fail",
      "Error": "OrderProcessingFailed",
      "Cause": "The order could not be processed after all retry attempts"
    }
  }
}
EOF
sed -i "s/ACCOUNT_ID/$ACC/g" order-v2.asl.json

SM2=$(aws stepfunctions create-state-machine --name order-processor-v2 --definition file://order-v2.asl.json --role-arn $ROLE_ARN --type STANDARD --query stateMachineArn --output text)
echo $SM2
aws stepfunctions describe-state-machine --state-machine-arn $SM2 --query "[name,status,type]" --output text

EX1=$(aws stepfunctions start-execution --state-machine-arn $SM2 --name exec-ord-100 --input '{"order_id":"ORD-100","total":150,"simulate_error":false}' --query executionArn --output text)
sleep 6
aws stepfunctions describe-execution --execution-arn $EX1 --query "[status,output]" --output text

EX2=$(aws stepfunctions start-execution --state-machine-arn $SM2 --name exec-ord-200 --input '{"order_id":"ORD-200","total":200,"simulate_error":true}' --query executionArn --output text)
sleep 25
aws stepfunctions describe-execution --execution-arn $EX2 --query "[status,error]" --output text

for i in 1 2 3 4 5; do
  aws stepfunctions start-execution --state-machine-arn $SM2 --name exec-retry-$i --input "{\"order_id\":\"ORD-2$i\",\"total\":200,\"simulate_error\":true}" --query executionArn --output text
done
sleep 25
aws stepfunctions list-executions --state-machine-arn $SM2 --query "executions[].[name,status]" --output table

EX3=$(aws stepfunctions start-execution --state-machine-arn $SM2 --name exec-ord-300 --input '{"order_id":"ORD-300","total":-50}' --query executionArn --output text)
sleep 6
aws stepfunctions describe-execution --execution-arn $EX3 --query "[status,error,cause]" --output text
aws stepfunctions get-execution-history --execution-arn $EX3 --query "events[?type=='TaskStateEntered'||type=='FailStateEntered'].[id,type,stateEnteredEventDetails.name]" --output table

EXR=$(aws stepfunctions list-executions --state-machine-arn $SM2 --query "executions[0].executionArn" --output text)
aws stepfunctions get-execution-history --execution-arn $EXR --query "events[?type=='TaskScheduled'||type=='TaskFailed'||type=='TaskSucceeded'].[id,timestamp,type]" --output table

NOME=riccardogouthier
BUCKET=lab17-receipts-$NOME

aws dynamodb create-table --table-name lab17-orders --attribute-definitions AttributeName=order_id,AttributeType=S --key-schema AttributeName=order_id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab17-orders
aws s3api create-bucket --bucket $BUCKET
aws dynamodb describe-table --table-name lab17-orders --query "Table.TableStatus" --output text
aws s3 ls | grep lab17

cat > direct.asl.json <<'EOF'
{
  "Comment": "Direct SDK integration workflow",
  "StartAt": "SaveOrder",
  "States": {
    "SaveOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:putItem",
      "Parameters": {
        "TableName": "lab17-orders",
        "Item": {
          "order_id": { "S.$": "$.order_id" },
          "customer": { "S.$": "$.customer" },
          "total": { "N.$": "States.Format('{}', $.total)" },
          "status": { "S": "confirmed" }
        }
      },
      "ResultPath": "$.dynamoResult",
      "Next": "SaveReceipt"
    },
    "SaveReceipt": {
      "Type": "Task",
      "Resource": "arn:aws:states:::aws-sdk:s3:putObject",
      "Parameters": {
        "Bucket": "BUCKET_NAME",
        "Key.$": "States.Format('receipts/{}.json', $.order_id)",
        "Body": {
          "order_id.$": "$.order_id",
          "customer.$": "$.customer",
          "total.$": "$.total",
          "status": "confirmed"
        }
      },
      "ResultPath": "$.s3Result",
      "Next": "OrderComplete"
    },
    "OrderComplete": {"Type": "Succeed"}
  }
}
EOF
sed -i "s/BUCKET_NAME/$BUCKET/" direct.asl.json

aws logs create-log-group --log-group-name step-functions-lab17
LOG_ARN=$(aws logs describe-log-groups --log-group-name-prefix step-functions-lab17 --query "logGroups[0].arn" --output text)
echo $LOG_ARN

SM3=$(aws stepfunctions create-state-machine --name direct-integration-demo --definition file://direct.asl.json --role-arn $ROLE_ARN --type STANDARD --logging-configuration "{\"level\":\"ALL\",\"includeExecutionData\":true,\"destinations\":[{\"cloudWatchLogsLogGroup\":{\"logGroupArn\":\"$LOG_ARN\"}}]}" --query stateMachineArn --output text)
echo $SM3
aws stepfunctions describe-state-machine --state-machine-arn $SM3 --query "[name,status,loggingConfiguration.level]" --output text

EX4=$(aws stepfunctions start-execution --state-machine-arn $SM3 --name exec-ord-500 --input '{"order_id":"ORD-500","customer":"Alice","total":199.99}' --query executionArn --output text)
sleep 6
aws stepfunctions describe-execution --execution-arn $EX4 --query "[status,error,cause]" --output text

aws dynamodb get-item --table-name lab17-orders --key '{"order_id":{"S":"ORD-500"}}'
aws s3 ls s3://$BUCKET/receipts/
aws s3 cp s3://$BUCKET/receipts/ORD-500.json -

EX5=$(aws stepfunctions start-execution --state-machine-arn $SM3 --name exec-ord-501 --input '{"order_id":"ORD-501","customer":"Bob","total":49.99}' --query executionArn --output text)
sleep 6
aws stepfunctions describe-execution --execution-arn $EX5 --query "status" --output text
aws dynamodb scan --table-name lab17-orders --query "Items[].[order_id.S,customer.S,total.N]" --output table
aws s3 ls s3://$BUCKET/receipts/

aws logs filter-log-events --log-group-name step-functions-lab17 --max-items 30 --output json | jq -r '.events[].message | fromjson | [.type, (.details.name // "")] | @tsv'
```

### Cleanup

```bash
aws stepfunctions delete-state-machine --state-machine-arn $SM2
aws stepfunctions delete-state-machine --state-machine-arn $SM3
for f in validate-order-v2 process-payment handle-failure; do aws lambda delete-function --function-name $f; done
aws dynamodb delete-table --table-name lab17-orders
aws s3 rm s3://$BUCKET --recursive && aws s3api delete-bucket --bucket $BUCKET
aws logs delete-log-group --log-group-name step-functions-lab17
```
