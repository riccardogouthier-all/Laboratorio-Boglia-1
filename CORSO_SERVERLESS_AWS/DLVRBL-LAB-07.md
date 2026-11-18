# Laboratorio 07 - Trigger Lambda e Linguaggi

Autore: Riccardo Gouthier (Gruppo 2).

## Scenario

Due trigger per Lambda Python 3.12: evento S3 (upload di un oggetto) ed evento schedulato (EventBridge, cron ogni 5 minuti). Regione `us-east-1`.

## Parte 1 - Trigger S3 (blob upload event)

### Step 1 - Bucket

- Bucket: `lab07-trigger-gouthier`
- Regione: `us-east-1`
- Creato il 21 settembre 2026, 14:56:37 (UTC+02:00)

### Step 2 - Funzione Lambda `process-s3-upload`

```python
import json
import urllib.parse

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']

        print(f"File uploaded: s3://{bucket}/{key} (size: {size} bytes)")
        print(f"Dimensione: {size} bytes")

    return {'statusCode': 200, 'body': f'Processed {len(event["Records"])} files'}
```

Note: `unquote_plus` decodifica la chiave dell'oggetto (spazi e caratteri speciali arrivano codificati nell'evento).

### Step 3 - Upload di un file di test

- Oggetto: `comando hypervisor.txt`, 290 byte
- Caricato il 21 settembre 2026, 16:29:04 (UTC+02:00)

### Step 4 - Verifica nei log CloudWatch

Log group `/aws/lambda/process-s3-upload`:

```
File uploaded: s3://lab07-trigger-gouthier/comando hypervisor.txt (size: 290 bytes)
Dimensione: 290 bytes
REPORT Duration: 2.16 ms  Billed Duration: 94 ms  Memory Size: 128 MB  Max Memory Used: 37 MB  Init Duration: presente
```

La riga `REPORT` è riportata senza `RequestId` e senza `XRAY TraceId`. `Init Duration` compare perché questa è la prima invocazione (cold start); il suo valore in millisecondi non è stato annotato. La Billed Duration (94 ms) è molto maggiore della Duration (2,16 ms) proprio perché comprende la fase di Init.

## Parte 2 - Trigger schedulato (cron)

### Step 5 - Funzione Lambda `scheduled-task`

```python
import json
from datetime import datetime

def lambda_handler(event, context):
    now = datetime.utcnow().isoformat()
    print(f"Scheduled execution at {now}")
    print(f"Event source: {json.dumps(event)}")
    return {'statusCode': 200, 'body': f'Executed at {now}'}
```

Nota: `datetime.utcnow()` è deprecata da Python 3.12; la forma raccomandata è `datetime.now(timezone.utc)`. Qui resta quella del testo del lab.

Trigger: regola EventBridge `every-5-min-rule` (ogni 5 minuti).

### Step 6 - Verifica nei log CloudWatch

- Esecuzioni osservate alle 16:36:01 e 16:41:01 (UTC+02:00), cioè a distanza di 5 minuti.
- Evento ricevuto: `detail-type` = `Scheduled Event`, `source` = `aws.events`, `region` = `us-east-1`, `resources` = ARN della regola `every-5-min-rule`.
- REPORT tipico: Duration 1,71 ms, Billed Duration 67 ms, Memory Size 128 MB, Max Memory Used 37 MB.

## Prove

| # | Prova | Tipo | Esito |
|---|---|---|---|
| 1 | Upload di un file nel bucket | Trigger S3 | Lambda invocata, log con chiave e dimensione corrette |
| 2 | Nome file con spazio | Decodifica chiave | Chiave letta correttamente grazie a `unquote_plus` |
| 3 | Attesa di più intervalli da 5 min | Trigger EventBridge | Esecuzioni periodiche visibili nei log |

## Conclusioni

1. Lo stesso modello a eventi serve sia per eventi di dati (S3) sia per eventi temporali (EventBridge).
2. Il payload dell'evento cambia per sorgente: `Records[]` per S3, `Scheduled Event` per EventBridge.
3. I cold start (Init Duration) compaiono quando Lambda deve creare un nuovo ambiente di esecuzione: alla prima invocazione dopo il deploy, dopo un periodo di inattività, dopo una modifica del codice o della configurazione e quando serve più concorrenza (scale-out). Le invocazioni che riusano un ambiente già pronto sono warm. Con la regola ogni 5 minuti i riavvii a freddo si osservano solo se l'ambiente è stato rimosso tra un'esecuzione e l'altra.

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
BUCKET=lab07-trigger-gouthier
mkdir -p lab07 && cd lab07

# Step 1 - Bucket
aws s3api create-bucket --bucket $BUCKET

# Step 2 - Funzione process-s3-upload
cat > lambda_function.py <<'EOF'
import json
import urllib.parse

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']

        print(f"File uploaded: s3://{bucket}/{key} (size: {size} bytes)")
        print(f"Dimensione: {size} bytes")

    return {'statusCode': 200, 'body': f'Processed {len(event["Records"])} files'}
EOF
zip -q s3fn.zip lambda_function.py
aws lambda create-function --function-name process-s3-upload --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://s3fn.zip
aws lambda wait function-active-v2 --function-name process-s3-upload

# Step 3 - Trigger S3 (All object create events)
aws lambda add-permission --function-name process-s3-upload --statement-id s3-invoke --action lambda:InvokeFunction --principal s3.amazonaws.com --source-arn arn:aws:s3:::$BUCKET --source-account $ACC
FN1=$(aws lambda get-function --function-name process-s3-upload --query Configuration.FunctionArn --output text)
aws s3api put-bucket-notification-configuration --bucket $BUCKET --notification-configuration "{\"LambdaFunctionConfigurations\":[{\"Id\":\"upload-trigger\",\"LambdaFunctionArn\":\"$FN1\",\"Events\":[\"s3:ObjectCreated:*\"]}]}"

# Step 4 - Test: upload di un file con spazio nel nome e lettura dei log
echo "comando di test per l'hypervisor" > "comando hypervisor.txt"
aws s3 cp "comando hypervisor.txt" s3://$BUCKET/
sleep 10
aws logs tail /aws/lambda/process-s3-upload --since 5m

# Step 5 - Funzione scheduled-task
cat > lambda_function.py <<'EOF'
import json
from datetime import datetime

def lambda_handler(event, context):
    now = datetime.utcnow().isoformat()
    print(f"Scheduled execution at {now}")
    print(f"Event source: {json.dumps(event)}")
    return {'statusCode': 200, 'body': f'Executed at {now}'}
EOF
zip -q schedfn.zip lambda_function.py
aws lambda create-function --function-name scheduled-task --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://schedfn.zip
aws lambda wait function-active-v2 --function-name scheduled-task

# Step 6 - Trigger EventBridge ogni 5 minuti
RULE_ARN=$(aws events put-rule --name every-5-min-rule --schedule-expression "rate(5 minutes)" --state ENABLED --query RuleArn --output text)
aws lambda add-permission --function-name scheduled-task --statement-id eventbridge-invoke --action lambda:InvokeFunction --principal events.amazonaws.com --source-arn $RULE_ARN
FN2=$(aws lambda get-function --function-name scheduled-task --query Configuration.FunctionArn --output text)
aws events put-targets --rule every-5-min-rule --targets "Id=scheduled-task,Arn=$FN2"

# Dopo 5-10 minuti: esecuzioni periodiche nei log
sleep 360
aws logs tail /aws/lambda/scheduled-task --since 15m
cd ..
```

### Cleanup

Il cleanup è necessario: la regola EventBridge continua a invocare `scheduled-task` ogni 5 minuti finché non viene eliminata, e la funzione e il bucket restano nell'account.

```bash
aws events remove-targets --rule every-5-min-rule --ids scheduled-task
aws events delete-rule --name every-5-min-rule
aws lambda delete-function --function-name process-s3-upload
aws lambda delete-function --function-name scheduled-task
aws s3 rm s3://$BUCKET --recursive && aws s3api delete-bucket --bucket $BUCKET
aws logs delete-log-group --log-group-name /aws/lambda/process-s3-upload
aws logs delete-log-group --log-group-name /aws/lambda/scheduled-task
```
