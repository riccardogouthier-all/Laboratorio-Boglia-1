#!/bin/bash
# Serverless AWS - procedura completa dei laboratori 1-18 da eseguire in AWS CloudShell (us-east-1).
# I blocchi di cleanup sono commentati: i laboratori successivi riusano le risorse. Decommentarli solo a fine corso.
# Lo script e pensato per essere eseguito per sezioni (lab per lab) leggendo l'output, non come unico lancio cieco.


#==============================================================================
# LABORATORIO 1 - Laboratorio 01 - Green IT: Smart Working e Smart Grid
#==============================================================================
cd "$HOME"
# Ipotesi FictaCorp
DC_ONPREM=788400      # kWh/anno data center on-premise (PUE 1,8)
UFFICIO=80000         # kWh/anno ufficio
PUE_ONPREM=1.8; PUE_CLOUD=1.2; RIGHTSIZING=0.30; SW_UFFICIO=0.40
CO2_KG_KWH=0.25       # fattore usato nel deliverable: 105,1 t / 420.480 kWh

awk -v dc=$DC_ONPREM -v of=$UFFICIO -v p0=$PUE_ONPREM -v p1=$PUE_CLOUD -v rs=$RIGHTSIZING -v sw=$SW_UFFICIO -v co2=$CO2_KG_KWH 'BEGIN {
  dc_cloud = dc * (p1/p0) * (1 - rs)
  of_sw    = of * (1 - sw)
  base     = dc + of
  cloud    = dc_cloud + of
  cloud_sw = dc_cloud + of_sw
  printf "Step 1 - annuale (kWh)\n"
  printf "  On-premise            DC %9.0f  Uff %7.0f  Tot %9.0f\n", dc, of, base
  printf "  Cloud AWS             DC %9.0f  Uff %7.0f  Tot %9.0f  risparmio %7.0f (%.0f%%)\n", dc_cloud, of, cloud, base-cloud, (base-cloud)/base*100
  printf "  Cloud + Smart Working DC %9.0f  Uff %7.0f  Tot %9.0f  risparmio %7.0f (%.0f%%)\n", dc_cloud, of_sw, cloud_sw, base-cloud_sw, (base-cloud_sw)/base*100
  printf "Step 2 - trimestrale (annuale/4)\n"
  printf "  On-premise %.0f | Cloud %.0f | Cloud+SW %.0f\n", base/4, cloud/4, cloud_sw/4
  printf "Step 3 - CO2 evitata (t/anno)\n"
  printf "  On-premise -> Cloud    %.1f t\n", (base-cloud)*co2/1000
  printf "  Solo Smart Working     %.1f t\n", (of-of_sw)*co2/1000
  printf "  On-premise -> Cloud+SW %.1f t\n", (base-cloud_sw)*co2/1000
}'

#==============================================================================
# LABORATORIO 2 - Laboratorio 02 - Green IT, Economia Circolare e Intro Serverless
#==============================================================================
cd "$HOME"

# --- Step 2 - POC pipeline CSV ---
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
BUCKET=lab02-csv-riccardogouthier

# Risorse: bucket, tabella, topic SNS
aws s3api create-bucket --bucket $BUCKET
aws dynamodb create-table --table-name lab02-records --attribute-definitions AttributeName=id,AttributeType=S --key-schema AttributeName=id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab02-records
TOPIC_ARN=$(aws sns create-topic --name lab02-csv-done --query TopicArn --output text)

# Lambda: parsing CSV, write su DynamoDB, publish su SNS
mkdir -p lab02 && cd lab02
cat > lambda_function.py <<'EOF'
import csv, io, os, urllib.parse
import boto3

s3 = boto3.client('s3')
table = boto3.resource('dynamodb').Table('lab02-records')
sns = boto3.client('sns')

def lambda_handler(event, context):
    total = 0
    for rec in event['Records']:
        bucket = rec['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(rec['s3']['object']['key'])
        body = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
        with table.batch_writer() as batch:
            for row in csv.DictReader(io.StringIO(body)):
                batch.put_item(Item={'id': row['id'], 'name': row['name'].strip().title()})
                total += 1
        sns.publish(TopicArn=os.environ['TOPIC_ARN'], Subject='CSV elaborato', Message=f'{key}: {total} righe')
    return {'statusCode': 200, 'body': f'Processed {total} rows'}
EOF
zip -q function.zip lambda_function.py
aws lambda create-function --function-name csv-poc --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip --environment "Variables={TOPIC_ARN=$TOPIC_ARN}"
aws lambda wait function-active-v2 --function-name csv-poc

# Trigger S3 ObjectCreated
aws lambda add-permission --function-name csv-poc --statement-id s3-invoke --action lambda:InvokeFunction --principal s3.amazonaws.com --source-arn arn:aws:s3:::$BUCKET --source-account $ACC
FN_ARN=$(aws lambda get-function --function-name csv-poc --query Configuration.FunctionArn --output text)
aws s3api put-bucket-notification-configuration --bucket $BUCKET --notification-configuration "{\"LambdaFunctionConfigurations\":[{\"LambdaFunctionArn\":\"$FN_ARN\",\"Events\":[\"s3:ObjectCreated:*\"]}]}"

# Test: upload del CSV e verifica
printf 'id,name\n1,mario rossi\n2,anna verdi\n' > clienti.csv
aws s3 cp clienti.csv s3://$BUCKET/clienti.csv
sleep 10
aws dynamodb scan --table-name lab02-records --query "Items[].[id.S,name.S]" --output table
aws logs tail /aws/lambda/csv-poc --since 5m
cd ..

# --- Step 3 - Confronto costi EC2 vs Lambda ---
awk 'BEGIN {
  ec2_h = 0.0416; ec2_mese = ec2_h*24*365/12; ec2_anno = ec2_h*24*365
  gbs = 100000 * 0.5 * 0.25                  # 12.500 GB-s/mese
  lam_mese = 0.21                            # valore del deliverable (richieste + compute)
  printf "EC2 t3.medium: %.2f $/mese, %.2f $/anno\n", ec2_mese, ec2_anno
  printf "Lambda: %d GB-s/mese, %.2f $/mese, %.2f $/anno\n", gbs, lam_mese, lam_mese*12
  printf "Risparmio annuo: %.2f $ (%.1f%%)\n", ec2_anno-lam_mese*12, (ec2_anno-lam_mese*12)/ec2_anno*100
}'

# --- Cleanup ---
# (cleanup, commentato)
# aws s3 rm s3://$BUCKET --recursive && aws s3api delete-bucket --bucket $BUCKET
# aws lambda delete-function --function-name csv-poc
# aws dynamodb delete-table --table-name lab02-records
# aws sns delete-topic --topic-arn $TOPIC_ARN
# aws logs delete-log-group --log-group-name /aws/lambda/csv-poc

#==============================================================================
# LABORATORIO 3 - Laboratorio 03 - Fondamenti Serverless e Confronto Architetturale
#==============================================================================
cd "$HOME"
awk 'BEGIN {
  # Richieste mensili per servizio (256 MB, 200 ms)
  utenti=5000; catalogo=30000; ordini=15000; pagamenti=15000
  req = utenti + catalogo + ordini + pagamenti
  gbs = req * 0.2 * 0.25
  free_gbs = 400000; free_req = 1000000
  printf "Richieste Lambda/mese: %d (free tier %d)\n", req, free_req
  printf "GB-s/mese: %.0f (free tier %d) -> compute a pagamento: %.0f GB-s\n", gbs, free_gbs, (gbs>free_gbs)?gbs-free_gbs:0
  api = 0.02                                  # stima Calculator del deliverable
  printf "API Gateway: ~%.2f $/mese (stima Calculator)\n", api

  # Cifre dal Pricing Calculator (stime del deliverable)
  mono=181; micro=124; sless=0
  printf "Monolitica %d $ | Microservizi %d $ | Serverless ~%d $\n", mono, micro, sless
  printf "Risparmio serverless vs monolite: ~%d $/mese\n", mono - sless
}'

#==============================================================================
# LABORATORIO 4 - Laboratorio 04 - Casi d'Uso Serverless e Analisi Economica
#==============================================================================
cd "$HOME"
# Scenario A - blog (900.000 richieste/mese), cifre Calculator
awk 'BEGIN {
  ec2 = 8.23 + 15.44                          # EC2 t3.micro + RDS db.t3.micro
  sl  = 0.00 + 0.37 + 0.90                    # Lambda + DynamoDB + HTTP API
  printf "A) EC2 %.2f $/mese (%.2f/anno) | Serverless %.2f $/mese (%.2f/anno) | risparmio %.0f%%\n", ec2, ec2*12, sl, sl*12, (ec2-sl)/ec2*100
}'

# Scenario B - e-commerce 720M richieste/mese
awk 'BEGIN {
  ec2 = 626.90 + 22.27                        # 10x c5.large + ALB
  sl  = 1337.14 + 678.00                      # Lambda + HTTP API
  printf "B) EC2 %.2f | Serverless %.2f | serverless = %.1fx\n", ec2, sl, sl/ec2
}'

# Scenario C - stagionale: 4 mesi estate, 8 mesi inverno
awk 'BEGIN {
  ec2 = 270.47 * 12
  sl  = 96.33*4 + 0.36*8
  printf "C) EC2 %.0f $/anno | Serverless %.0f $/anno | risparmio %.0f%%\n", ec2, sl, (ec2-sl)/ec2*100
}'

# Break-even Lambda (200 ms, 256 MB) vs EC2 t3.medium 24/7 (~33 $/mese)
awk 'BEGIN {
  ec2 = 33
  for (n = 1000000; n <= 40000000; n += 500000) {
    req  = (n-1000000) * 0.23/1000000          # richieste oltre il free tier
    gbs  = n * 0.2 * 0.25; extra = (gbs>400000) ? gbs-400000 : 0
    comp = extra * 0.0000195172
    api  = n/1000000 * 1.00                    # HTTP API: 1 $ per milione
    tot  = req + comp + api
    if (tot >= ec2) { printf "Break-even ~%.1f M richieste/mese (serverless %.2f $ vs EC2 %d $)\n", n/1000000, tot, ec2; break }
  }
}'

#==============================================================================
# LABORATORIO 5 - Laboratorio 05 - Limitazioni Serverless e Best Practice
#==============================================================================
cd "$HOME"
mkdir -p lab05 && cd lab05

# 1) Codice originale (con i difetti)
cat > lambda_bad.py <<'EOF'
import boto3, json, os
import pandas as pd
import numpy as np

DB_PASSWORD = "SuperSecret123!"

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('orders')
    body = json.loads(event['body'])
    order_id = body['order_id']
    amount = body['amount']
    table.put_item(Item={'order_id': order_id, 'amount': amount, 'db_password': DB_PASSWORD})
    import pymysql
    conn = pymysql.connect(host=os.environ['DB_HOST'], user='admin', password=DB_PASSWORD, database='shop')
    cur = conn.cursor()
    cur.execute(f"INSERT INTO orders VALUES ('{order_id}', {amount})")
    conn.commit()
    return {'statusCode': 200, 'body': 'OK'}
EOF

# 2) Audit dei problemi
grep -nE 'PASSWORD|password' lambda_bad.py          # credenziali hardcoded / salvate nei dati
grep -nE '^import (pandas|numpy)' lambda_bad.py     # librerie inutilizzate
grep -nE 'execute\(f"' lambda_bad.py                # SQL con f-string (injection)
grep -nE '^\s+import ' lambda_bad.py                # import dentro l'handler
grep -c 'try:' lambda_bad.py                        # 0 = nessuna gestione errori
grep -c 'logging' lambda_bad.py                     # 0 = nessun log

# 3) Versione corretta
cat > lambda_good.py <<'EOF'
import json, logging, os
import boto3
import pymysql

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Init fuori dall'handler: riusati tra le invocazioni
table = boto3.resource('dynamodb').Table('orders')
secrets = boto3.client('secretsmanager')

def get_db_password():
    return json.loads(secrets.get_secret_value(SecretId=os.environ['DB_SECRET'])['SecretString'])['password']

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body') or '{}')
        order_id = str(body.get('order_id', ''))
        amount = body.get('amount')
        if not order_id.isalnum() or not isinstance(amount, (int, float)):
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid input'})}

        table.put_item(Item={'order_id': order_id, 'amount': str(amount)})   # nessuna credenziale nei dati

        conn = pymysql.connect(host=os.environ['DB_HOST'], user=os.environ['DB_USER'],
                               password=get_db_password(), database='shop')
        with conn.cursor() as cur:
            cur.execute("INSERT INTO orders VALUES (%s, %s)", (order_id, amount))   # query parametrizzata
        conn.commit()
        logger.info("Order %s saved", order_id)
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    except Exception:
        logger.exception("Order processing failed")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}
EOF

python3 -m py_compile lambda_good.py && echo "sintassi OK"
cd ..

#==============================================================================
# LABORATORIO 6 - Laboratorio 06 - Prima Funzione Lambda
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
mkdir -p lab06 && cd lab06

# Step 1-2 - Funzione hello-serverless (Python 3.12, LabRole)
cat > lambda_function.py <<'EOF'
import json
import time

def lambda_handler(event, context):
    start = time.time()
    name = event.get('name', 'World')

    response = {
        'message': f'Hello, {name}!',
        'function_name': context.function_name,
        'memory_limit_mb': context.memory_limit_in_mb,
        'remaining_time_ms': context.get_remaining_time_in_millis(),
        'execution_time_ms': round((time.time() - start) * 1000, 2)
    }

    print(f"Processed request for: {name}")
    print(f"Response: {json.dumps(response)}")

    return {'statusCode': 200, 'body': json.dumps(response)}
EOF
zip -q function.zip lambda_function.py
aws lambda create-function --function-name hello-serverless --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip
aws lambda wait function-active-v2 --function-name hello-serverless

# Step 3-4 - Primo invoke (cold start) e secondo invoke (warm start)
aws lambda invoke --function-name hello-serverless --cli-binary-format raw-in-base64-out --payload '{"name":"Mario"}' out.json && cat out.json
aws lambda invoke --function-name hello-serverless --cli-binary-format raw-in-base64-out --payload '{"name":"Mario"}' out.json && cat out.json

# Righe REPORT: Init Duration compare solo nel cold start
sleep 10
aws logs filter-log-events --log-group-name /aws/lambda/hello-serverless --filter-pattern REPORT --query "events[].message" --output text

# Step 5 - Memoria a 256 MB (la modifica forza un nuovo cold start), poi warm
aws lambda update-function-configuration --function-name hello-serverless --memory-size 256
aws lambda wait function-updated-v2 --function-name hello-serverless
aws lambda invoke --function-name hello-serverless --cli-binary-format raw-in-base64-out --payload '{"name":"Mario"}' out.json
aws lambda invoke --function-name hello-serverless --cli-binary-format raw-in-base64-out --payload '{"name":"Mario"}' out.json
sleep 10
aws logs filter-log-events --log-group-name /aws/lambda/hello-serverless --filter-pattern REPORT --query "events[].message" --output text
cd ..

# --- Cleanup ---
# (cleanup, commentato)
# aws lambda delete-function --function-name hello-serverless
# aws logs delete-log-group --log-group-name /aws/lambda/hello-serverless

#==============================================================================
# LABORATORIO 7 - Laboratorio 07 - Trigger Lambda e Linguaggi
#==============================================================================
cd "$HOME"
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

# --- Cleanup ---
# (cleanup, commentato)
# aws events remove-targets --rule every-5-min-rule --ids scheduled-task
# aws events delete-rule --name every-5-min-rule
# aws lambda delete-function --function-name process-s3-upload
# aws lambda delete-function --function-name scheduled-task
# aws s3 rm s3://$BUCKET --recursive && aws s3api delete-bucket --bucket $BUCKET
# aws logs delete-log-group --log-group-name /aws/lambda/process-s3-upload
# aws logs delete-log-group --log-group-name /aws/lambda/scheduled-task

#==============================================================================
# LABORATORIO 8 - Laboratorio 08 - Risorse Lambda e Monitoraggio
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
mkdir -p lab08 && cd lab08

# Step 1 - Funzione resource-test
cat > lambda_function.py <<'EOF'
import json
import math
import time

def lambda_handler(event, context):
    iterations = int(event.get('iterations', 100000))
    start = time.time()
    result = sum(math.sqrt(i) for i in range(iterations))
    duration = round((time.time() - start) * 1000, 2)

    memory_used = context.memory_limit_in_mb
    remaining = context.get_remaining_time_in_millis()

    print(json.dumps({
        'iterations': iterations,
        'duration_ms': duration,
        'memory_mb': memory_used,
        'remaining_ms': remaining
    }))

    return {
        'statusCode': 200,
        'body': json.dumps({
            'duration_ms': duration,
            'memory_mb': memory_used,
            'result': result
        })
    }
EOF
zip -q function.zip lambda_function.py
aws lambda create-function --function-name resource-test --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip --timeout 30
aws lambda wait function-active-v2 --function-name resource-test

# Step 2 - Test con memoria crescente (128, 256, 512, 1024 MB)
for MEM in 128 256 512 1024; do
  aws lambda update-function-configuration --function-name resource-test --memory-size $MEM > /dev/null
  aws lambda wait function-updated-v2 --function-name resource-test
  aws lambda invoke --function-name resource-test --cli-binary-format raw-in-base64-out --payload '{"iterations":1000000}' out.json > /dev/null
  DUR=$(jq -r '.body | fromjson | .duration_ms' out.json)
  echo "$MEM MB: durata ${DUR} ms, costo stimato (MB-s) = $(awk -v m=$MEM -v d=$DUR 'BEGIN{printf "%.1f", m*d/1000}')"
done

# Step 3 - Reserved concurrency = 5
aws lambda put-function-concurrency --function-name resource-test --reserved-concurrent-executions 5
aws lambda get-function-concurrency --function-name resource-test

# Step 4 - Allarme CloudWatch su Errors (nessuna azione associata)
aws cloudwatch put-metric-alarm --alarm-name resource-test-errors --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value=resource-test --statistic Sum --period 60 --evaluation-periods 1 --threshold 0 --comparison-operator GreaterThanThreshold --treat-missing-data missing
aws cloudwatch describe-alarms --alarm-names resource-test-errors --query "MetricAlarms[].[AlarmName,StateValue,Threshold]" --output table

# Step 5 - Logs Insights sulle righe REPORT
QID=$(aws logs start-query --log-group-name /aws/lambda/resource-test --start-time $(date -d '-1 week' +%s) --end-time $(date +%s) --query-string 'filter @type = "REPORT" | stats avg(@duration) as avgDuration, max(@duration) as maxDuration, min(@memorySize) as memorySize | sort avgDuration desc' --query queryId --output text)
sleep 8
aws logs get-query-results --query-id $QID --query "[status,results]" --output json
cd ..

# --- Cleanup ---
# (cleanup, commentato)
# aws lambda delete-function-concurrency --function-name resource-test
# aws cloudwatch delete-alarms --alarm-names resource-test-errors
# aws lambda delete-function --function-name resource-test
# aws logs delete-log-group --log-group-name /aws/lambda/resource-test

#==============================================================================
# LABORATORIO 9 - Laboratorio 09 - Sicurezza IAM con DynamoDB e Secrets Manager
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
mkdir -p lab09 && cd lab09

# Step 6 - Tabella lab09-users
aws dynamodb create-table --table-name lab09-users --attribute-definitions AttributeName=user_id,AttributeType=S --key-schema AttributeName=user_id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab09-users

# Step 7 - Dati di test
aws dynamodb put-item --table-name lab09-users --item '{"user_id":{"S":"u001"},"name":{"S":"Alice"},"email":{"S":"alice@example.com"}}'
aws dynamodb put-item --table-name lab09-users --item '{"user_id":{"S":"u002"},"name":{"S":"Bob"},"email":{"S":"bob@example.com"}}'

# Step 10 - Segreto in Secrets Manager
aws secretsmanager create-secret --name lab09/app-config --secret-string '{"demo_token":"token-123"}'

# Step 8 - Funzione secure-reader
cat > lambda_function.py <<'EOF'
import json
import os
import boto3

TABLE_NAME = os.environ.get('TABLE_NAME', 'lab09-users')
REGION = os.environ.get('AWS_REGION', 'us-east-1')
APP_SECRET_NAME = os.environ.get('APP_SECRET_NAME', 'lab09/app-config')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)
secrets_client = boto3.client('secretsmanager', region_name=REGION)

def get_app_secret():
    response = secrets_client.get_secret_value(SecretId=APP_SECRET_NAME)
    return json.loads(response['SecretString'])

def lambda_handler(event, context):
    user_id = event.get('user_id')

    if not user_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'user_id is required'})}

    # Input validation: solo alfanumerici e trattini
    if not all(c.isalnum() or c == '-' for c in user_id):
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid user_id format'})}

    try:
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item')

        if not item:
            return {'statusCode': 404, 'body': json.dumps({'error': 'User not found'})}

        secret = get_app_secret()

        print(json.dumps({'action': 'get_user', 'user_id': user_id, 'status': 'success', 'secret_loaded': True}))

        return {
            'statusCode': 200,
            'body': json.dumps({
                'user': item,
                'secret_loaded': True,
                'secret_key_present': 'demo_token' in secret
            })
        }
    except Exception as e:
        print(json.dumps({'action': 'get_user', 'user_id': user_id, 'status': 'error', 'error': str(e)}))
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}
EOF
zip -q function.zip lambda_function.py
aws lambda create-function --function-name secure-reader --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip
aws lambda wait function-active-v2 --function-name secure-reader

# Step 9 - Variabili d'ambiente
aws lambda update-function-configuration --function-name secure-reader --environment "Variables={TABLE_NAME=lab09-users,APP_SECRET_NAME=lab09/app-config}"
aws lambda wait function-updated-v2 --function-name secure-reader

# Step 11 - Test: positivo, inesistente, senza user_id, injection
aws lambda invoke --function-name secure-reader --cli-binary-format raw-in-base64-out --payload '{"user_id":"u001"}' out.json && cat out.json; echo
aws lambda invoke --function-name secure-reader --cli-binary-format raw-in-base64-out --payload '{"user_id":"999"}' out.json && cat out.json; echo
aws lambda invoke --function-name secure-reader --cli-binary-format raw-in-base64-out --payload '{}' out.json && cat out.json; echo
aws lambda invoke --function-name secure-reader --cli-binary-format raw-in-base64-out --payload "{\"user_id\":\"'; DROP TABLE users;--\"}" out.json && cat out.json; echo

# Step 12 - Policy least-privilege (documentale: nel Learner Lab si usa LabRole)
ACC=$(aws sts get-caller-identity --query Account --output text)
cat > least-privilege.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": "dynamodb:GetItem", "Resource": "arn:aws:dynamodb:us-east-1:$ACC:table/lab09-users"},
    {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": "arn:aws:secretsmanager:us-east-1:$ACC:secret:lab09/app-config-*"},
    {"Effect": "Allow", "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], "Resource": "arn:aws:logs:us-east-1:$ACC:log-group:/aws/lambda/secure-reader:*"}
  ]
}
EOF
cat least-privilege.json
cd ..

# --- Cleanup ---
# (cleanup, commentato)
# aws lambda delete-function --function-name secure-reader
# aws dynamodb delete-table --table-name lab09-users
# aws secretsmanager delete-secret --secret-id lab09/app-config --recovery-window-in-days 7
# aws logs delete-log-group --log-group-name /aws/lambda/secure-reader

#==============================================================================
# LABORATORIO 10 - Laboratorio 10 - API Gateway REST con Lambda
#==============================================================================
cd "$HOME"
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

# --- Cleanup ---
# (cleanup, commentato)
# aws apigateway delete-rest-api --rest-api-id $API_ID
# aws lambda delete-function --function-name api-hello
# aws logs delete-log-group --log-group-name /aws/lambda/api-hello

#==============================================================================
# LABORATORIO 11 - Laboratorio 11 - API CRUD con Lambda Authorizer
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
mkdir -p lab11 && cd lab11

# Step 1 - Tabella lab11-users
aws dynamodb create-table --table-name lab11-users --attribute-definitions AttributeName=user_id,AttributeType=S --key-schema AttributeName=user_id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab11-users

# Step 2 - Funzione crud-users
cat > lambda_function.py <<'EOF'
import json
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('lab11-users')

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
}

def lambda_handler(event, context):
    method = event['httpMethod']
    path_params = event.get('pathParameters') or {}

    try:
        if method == 'GET' and 'id' in path_params:
            return get_user(path_params['id'])
        elif method == 'GET':
            return list_users()
        elif method == 'POST':
            body = json.loads(event.get('body', '{}'))
            return create_user(body)
        elif method == 'DELETE' and 'id' in path_params:
            return delete_user(path_params['id'])
        else:
            return response(405, {'error': 'Method not allowed'})
    except Exception as e:
        return response(500, {'error': str(e)})

def get_user(user_id):
    result = table.get_item(Key={'user_id': user_id})
    item = result.get('Item')
    if not item:
        return response(404, {'error': 'User not found'})
    return response(200, item)

def list_users():
    result = table.scan(Limit=50)
    return response(200, {'users': result.get('Items', [])})

def create_user(body):
    if 'name' not in body:
        return response(400, {'error': 'name is required'})
    item = {
        'user_id': str(uuid.uuid4())[:8],
        'name': body['name'],
        'email': body.get('email', '')
    }
    table.put_item(Item=item)
    return response(201, item)

def delete_user(user_id):
    table.delete_item(Key={'user_id': user_id})
    return response(200, {'message': f'User {user_id} deleted'})

def response(status_code, body):
    return {'statusCode': status_code, 'headers': HEADERS, 'body': json.dumps(body)}
EOF
zip -q crud.zip lambda_function.py
aws lambda create-function --function-name crud-users --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://crud.zip
aws lambda wait function-active-v2 --function-name crud-users

# Step 3 - Lambda authorizer simple-authorizer (token di prova del laboratorio)
cat > lambda_function.py <<'EOF'
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
EOF
zip -q auth.zip lambda_function.py
aws lambda create-function --function-name simple-authorizer --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://auth.zip
aws lambda wait function-active-v2 --function-name simple-authorizer
CRUD_ARN=$(aws lambda get-function --function-name crud-users --query Configuration.FunctionArn --output text)
AUTH_ARN=$(aws lambda get-function --function-name simple-authorizer --query Configuration.FunctionArn --output text)

# Step 4 - API crud-api: /users (GET, POST) e /users/{id} (GET, DELETE)
API_ID=$(aws apigateway create-rest-api --name crud-api --endpoint-configuration types=REGIONAL --query id --output text)
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/'].id" --output text)
USERS_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part users --query id --output text)
ID_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $USERS_ID --path-part '{id}' --query id --output text)

# Step 5 - Authorizer token-auth (header Authorization, cache 300 s)
aws lambda add-permission --function-name simple-authorizer --statement-id apigw-authorizer --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:$ACC:$API_ID/authorizers/*"
AUTHZ_ID=$(aws apigateway create-authorizer --rest-api-id $API_ID --name token-auth --type TOKEN --authorizer-uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$AUTH_ARN/invocations --identity-source method.request.header.Authorization --authorizer-result-ttl-in-seconds 300 --query id --output text)

URI=arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$CRUD_ARN/invocations
# GET /users e GET /users/{id}: pubblici
aws apigateway put-method --rest-api-id $API_ID --resource-id $USERS_ID --http-method GET --authorization-type NONE
aws apigateway put-method --rest-api-id $API_ID --resource-id $ID_ID --http-method GET --authorization-type NONE --request-parameters method.request.path.id=true
# POST /users e DELETE /users/{id}: protetti dall'authorizer
aws apigateway put-method --rest-api-id $API_ID --resource-id $USERS_ID --http-method POST --authorization-type CUSTOM --authorizer-id $AUTHZ_ID
aws apigateway put-method --rest-api-id $API_ID --resource-id $ID_ID --http-method DELETE --authorization-type CUSTOM --authorizer-id $AUTHZ_ID --request-parameters method.request.path.id=true
for M in "$USERS_ID GET" "$USERS_ID POST" "$ID_ID GET" "$ID_ID DELETE"; do
  set -- $M
  aws apigateway put-integration --rest-api-id $API_ID --resource-id $1 --http-method $2 --type AWS_PROXY --integration-http-method POST --uri $URI
done
aws lambda add-permission --function-name crud-users --statement-id apigw-crud --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:$ACC:$API_ID/*/*/users*"

# Step 6 - Deploy stage dev e test
aws apigateway create-deployment --rest-api-id $API_ID --stage-name dev
BASE=https://$API_ID.execute-api.us-east-1.amazonaws.com/dev
curl -s $BASE/users; echo                                                       # lista vuota
curl -s -o /dev/null -w "senza token: %{http_code}\n" -X POST $BASE/users -d '{"name":"Alice"}'   # 401/403
curl -s -X POST $BASE/users -H "Authorization: Bearer my-secret-token-2025" -H "Content-Type: application/json" -d '{"name":"Alice"}'; echo
curl -s $BASE/users; echo                                                       # lista con Alice
cd ..

# --- Cleanup ---
# (cleanup, commentato)
# aws apigateway delete-rest-api --rest-api-id $API_ID
# aws lambda delete-function --function-name crud-users
# aws lambda delete-function --function-name simple-authorizer
# aws dynamodb delete-table --table-name lab11-users
# aws logs delete-log-group --log-group-name /aws/lambda/crud-users
# aws logs delete-log-group --log-group-name /aws/lambda/simple-authorizer

#==============================================================================
# LABORATORIO 12 - Laboratorio 12 - Versioni, Stage, Caching e Monitoraggio API
#==============================================================================
cd "$HOME"
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

# --- Cleanup ---
# (cleanup, commentato)
# aws apigateway delete-stage --rest-api-id $API2 --stage-name dev    # ferma il cache cluster
# aws apigateway delete-rest-api --rest-api-id $API2
# aws apigateway delete-rest-api --rest-api-id $API_ID
# aws lambda delete-function --function-name cache-demo
# aws lambda delete-function --function-name stage-demo
# aws logs delete-log-group --log-group-name api-access-logs-dev
# aws logs delete-log-group --log-group-name cache-test-api-log-group
# aws logs delete-log-group --log-group-name /aws/lambda/cache-demo
# aws logs delete-log-group --log-group-name /aws/lambda/stage-demo

#==============================================================================
# LABORATORIO 13 - Laboratorio 13 - DynamoDB: Lambda CRUD su ordini
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
mkdir -p lab13 && cd lab13

# Step 1 - Tabella con chiave composta (cliente + data)
aws dynamodb create-table --table-name lab13-orders \
  --attribute-definitions AttributeName=customer_id,AttributeType=S AttributeName=order_date,AttributeType=S \
  --key-schema AttributeName=customer_id,KeyType=HASH AttributeName=order_date,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab13-orders

# Step 2 - Dati di test
put() { aws dynamodb put-item --table-name lab13-orders --item "{\"customer_id\":{\"S\":\"$1\"},\"order_date\":{\"S\":\"$2\"},\"product\":{\"S\":\"$3\"},\"quantity\":{\"N\":\"$4\"},\"total\":{\"N\":\"$5\"}}"; }
put C001 2025-01-15 Laptop   1 999.99
put C001 2025-02-20 Mouse    2 49.98
put C001 2025-03-10 Keyboard 1 79.99
put C002 2025-01-22 Monitor  1 349.99
put C002 2025-03-05 Webcam   1 89.99
aws dynamodb scan --table-name lab13-orders --select COUNT          # atteso: 5

# Step 3 - Funzione orders-crud (con Decimal per i numeri, correzione dello Step 5)
cat > lambda_function.py <<'EOF'
import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb').Table('lab13-orders')

def lambda_handler(event, context):
    action = event.get('action')
    if action == 'get':
        return get_order(event['customer_id'], event['order_date'])
    if action == 'query':
        return query_orders(event['customer_id'], event.get('date_prefix'))
    if action == 'create':
        return create_order(event)
    if action == 'scan':
        return scan_orders()
    return response(400, {'error': 'unknown action'})

def get_order(customer_id, order_date):
    item = table.get_item(Key={'customer_id': customer_id, 'order_date': order_date}).get('Item')
    return response(200, item) if item else response(404, {'error': 'Order not found'})

def query_orders(customer_id, prefix=None):
    cond = Key('customer_id').eq(customer_id)
    if prefix:
        cond = cond & Key('order_date').begins_with(prefix)
    items = table.query(KeyConditionExpression=cond)['Items']
    return response(200, {'orders': items, 'count': len(items)})

def create_order(event):
    item = json.loads(json.dumps(event['item']), parse_float=Decimal)
    table.put_item(Item=item)
    return response(201, {'message': 'Order created', 'item': item})

def scan_orders():
    items = table.scan(Limit=50)['Items']
    return response(200, {'orders': items, 'count': len(items)})

def response(status_code, body):
    return {'statusCode': status_code, 'body': json.dumps(body, default=str)}
EOF
zip -q function.zip lambda_function.py
aws lambda create-function --function-name orders-crud --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip
aws lambda wait function-active-v2 --function-name orders-crud

# Step 4 - Test delle operazioni
inv() { aws lambda invoke --function-name orders-crud --cli-binary-format raw-in-base64-out --payload "$1" out.json > /dev/null; cat out.json; echo; }
inv '{"action":"get","customer_id":"C001","order_date":"2025-01-15"}'
inv '{"action":"query","customer_id":"C001","date_prefix":"2025-01"}'
inv '{"action":"query","customer_id":"C001"}'
inv '{"action":"scan"}'

# Step 5 - Nuovo ordine con totale decimale
inv '{"action":"create","item":{"customer_id":"C003","order_date":"2025-04-01","product":"Headphones","quantity":1,"total":59.99}}'
aws dynamodb get-item --table-name lab13-orders --key '{"customer_id":{"S":"C003"},"order_date":{"S":"2025-04-01"}}'

# Righe REPORT (Duration, Billed Duration, Init Duration)
aws logs filter-log-events --log-group-name /aws/lambda/orders-crud --filter-pattern REPORT --query "events[].message" --output text
cd ..

# --- Cleanup ---
# (cleanup, commentato)
# aws lambda delete-function --function-name orders-crud
# aws dynamodb delete-table --table-name lab13-orders
# aws logs delete-log-group --log-group-name /aws/lambda/orders-crud

#==============================================================================
# LABORATORIO 14 - Laboratorio 14 - Pipeline S3 -> Lambda -> DynamoDB
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
mkdir -p lab14 && cd lab14

# ================= Parte 1 - Metadati dei file (S3 -> Lambda -> DynamoDB) =================

# Step 1 - Tabella lab14-file-metadata
aws dynamodb create-table --table-name lab14-file-metadata --attribute-definitions AttributeName=file_key,AttributeType=S --key-schema AttributeName=file_key,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab14-file-metadata

# Step 2 - Bucket
aws s3api create-bucket --bucket lab14-uploads-gouthier

# Step 3 - Funzione process-upload-metadata
cat > lambda_function.py <<'EOF'
import json
import urllib.parse
from datetime import datetime, timezone
import boto3

s3 = boto3.client('s3')
table = boto3.resource('dynamodb').Table('lab14-file-metadata')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']
        uploaded_at = record['eventTime']

        head = s3.head_object(Bucket=bucket, Key=key)
        content_type = head.get('ContentType', 'unknown')

        table.put_item(Item={
            'file_key': key,
            'bucket': bucket,
            'size_bytes': size,
            'content_type': content_type,
            'uploaded_at': uploaded_at,
            'processed_at': datetime.now(timezone.utc).isoformat()
        })
        print(f"Saved metadata for: {key} ({size} bytes, {content_type})")

    return {'statusCode': 200, 'body': f'Processed {len(event["Records"])} files'}
EOF
zip -q meta.zip lambda_function.py
aws lambda create-function --function-name process-upload-metadata --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://meta.zip
aws lambda wait function-active-v2 --function-name process-upload-metadata

# Step 4 - Trigger S3 (All object create events)
aws lambda add-permission --function-name process-upload-metadata --statement-id s3-invoke --action lambda:InvokeFunction --principal s3.amazonaws.com --source-arn arn:aws:s3:::lab14-uploads-gouthier --source-account $ACC
FN1=$(aws lambda get-function --function-name process-upload-metadata --query Configuration.FunctionArn --output text)
aws s3api put-bucket-notification-configuration --bucket lab14-uploads-gouthier --notification-configuration "{\"LambdaFunctionConfigurations\":[{\"Id\":\"upload-metadata-trigger\",\"LambdaFunctionArn\":\"$FN1\",\"Events\":[\"s3:ObjectCreated:*\"]}]}"

# Step 5 - Upload di 3 file (json, csv, txt)
echo '{"nome":"test","valore":1}' > data.json
printf 'id,nome\n1,uno\n2,due\n' > list.csv
echo "file di prova" > test.txt
aws s3 cp data.json s3://lab14-uploads-gouthier/
aws s3 cp list.csv  s3://lab14-uploads-gouthier/
aws s3 cp test.txt  s3://lab14-uploads-gouthier/

# Step 6-7 - Verifica nella tabella e nei log
sleep 10
aws dynamodb scan --table-name lab14-file-metadata --query "Items[].[file_key.S,content_type.S,size_bytes.N,uploaded_at.S,processed_at.S]" --output table
aws logs tail /aws/lambda/process-upload-metadata --since 5m

# ================= Parte 2 - Import CSV con GSI =================

# Step 8 - Tabella lab14-products con GSI category-price-index (category + price, proiezione ALL)
aws dynamodb create-table --table-name lab14-products \
  --attribute-definitions AttributeName=product_id,AttributeType=S AttributeName=category,AttributeType=S AttributeName=price,AttributeType=N \
  --key-schema AttributeName=product_id,KeyType=HASH \
  --global-secondary-indexes 'IndexName=category-price-index,KeySchema=[{AttributeName=category,KeyType=HASH},{AttributeName=price,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
  --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab14-products

# Step 9 - Bucket e cartella imports/
aws s3api create-bucket --bucket lab14-csv-import-gouthier
aws s3api put-object --bucket lab14-csv-import-gouthier --key imports/

# Step 10 - Funzione csv-importer
cat > lambda_function.py <<'EOF'
import csv
import io
import urllib.parse
from decimal import Decimal
import boto3

s3 = boto3.client('s3')
table = boto3.resource('dynamodb').Table('lab14-products')

def lambda_handler(event, context):
    count = 0
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        content = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')

        with table.batch_writer() as batch:
            for row in csv.DictReader(io.StringIO(content)):
                batch.put_item(Item={
                    'product_id': row['product_id'],
                    'category': row['category'],
                    'name': row['name'],
                    'price': Decimal(row['price']),
                    'stock': int(row['stock'])
                })
                count += 1
    print(f"Imported {count} products")
    return {'statusCode': 200, 'body': f'Imported {count} products'}
EOF
zip -q csv.zip lambda_function.py
aws lambda create-function --function-name csv-importer --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://csv.zip --timeout 30
aws lambda wait function-active-v2 --function-name csv-importer

# Step 11 - Trigger con filtro prefisso imports/ e suffisso .csv
aws lambda add-permission --function-name csv-importer --statement-id s3-invoke --action lambda:InvokeFunction --principal s3.amazonaws.com --source-arn arn:aws:s3:::lab14-csv-import-gouthier --source-account $ACC
FN2=$(aws lambda get-function --function-name csv-importer --query Configuration.FunctionArn --output text)
aws s3api put-bucket-notification-configuration --bucket lab14-csv-import-gouthier --notification-configuration "{\"LambdaFunctionConfigurations\":[{\"Id\":\"csv-import-trigger\",\"LambdaFunctionArn\":\"$FN2\",\"Events\":[\"s3:ObjectCreated:*\"],\"Filter\":{\"Key\":{\"FilterRules\":[{\"Name\":\"prefix\",\"Value\":\"imports/\"},{\"Name\":\"suffix\",\"Value\":\".csv\"}]}}}]}"

# Step 12 - Upload di products.csv in imports/ e scan
cat > products.csv <<'EOF'
product_id,category,name,price,stock
P001,Electronics,Laptop,999.99,50
P002,Electronics,Mouse,29.99,200
P003,Books,Python Cookbook,45.00,100
P004,Electronics,Keyboard,79.99,150
P005,Books,AWS in Action,55.00,75
P006,Clothing,T-Shirt,19.99,300
EOF
aws s3 cp products.csv s3://lab14-csv-import-gouthier/imports/products.csv
sleep 10
aws dynamodb scan --table-name lab14-products --query "Items[].[product_id.S,category.S,name.S,price.N,stock.N]" --output table

# Step 13 - Query sul GSI (ordinata per prezzo)
aws dynamodb query --table-name lab14-products --index-name category-price-index --key-condition-expression "category = :c" --expression-attribute-values '{":c":{"S":"Electronics"}}' --return-consumed-capacity INDEXES --query "[Items[].[name.S,price.N],ConsumedCapacity]" --output json
aws dynamodb query --table-name lab14-products --index-name category-price-index --key-condition-expression "category = :c" --expression-attribute-values '{":c":{"S":"Books"}}' --query "Items[].[product_id.S,price.N]" --output table
cd ..

# --- Cleanup ---
# (cleanup, commentato)
# aws s3 rm s3://lab14-uploads-gouthier --recursive && aws s3api delete-bucket --bucket lab14-uploads-gouthier
# aws s3 rm s3://lab14-csv-import-gouthier --recursive && aws s3api delete-bucket --bucket lab14-csv-import-gouthier
# aws lambda delete-function --function-name process-upload-metadata
# aws lambda delete-function --function-name csv-importer
# aws dynamodb delete-table --table-name lab14-file-metadata
# aws dynamodb delete-table --table-name lab14-products
# aws logs delete-log-group --log-group-name /aws/lambda/process-upload-metadata
# aws logs delete-log-group --log-group-name /aws/lambda/csv-importer

#==============================================================================
# LABORATORIO 15 - Laboratorio 15 - DynamoDB TTL, backup e lifecycle S3
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1

aws dynamodb create-table --table-name lab15-sessions --attribute-definitions AttributeName=session_id,AttributeType=S --key-schema AttributeName=session_id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab15-sessions
aws dynamodb describe-table --table-name lab15-sessions --query "Table.[TableName,TableStatus,KeySchema]" --output json

aws dynamodb update-time-to-live --table-name lab15-sessions --time-to-live-specification Enabled=true,AttributeName=expires_at
aws dynamodb describe-time-to-live --table-name lab15-sessions

cat > lambda_function.py <<'EOF'
import json
import time
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('lab15-sessions')

def lambda_handler(event, context):
    now = int(time.time())

    sessions = [
        {'session_id': 'sess-001', 'user_id': 'alice', 'created_at': now, 'expires_at': now + 60},
        {'session_id': 'sess-002', 'user_id': 'bob', 'created_at': now, 'expires_at': now + 3600},
        {'session_id': 'sess-003', 'user_id': 'charlie', 'created_at': now, 'expires_at': now + 86400}
    ]

    for session in sessions:
        table.put_item(Item=session)
        print(f"Created session {session['session_id']}, expires in {session['expires_at'] - now}s")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Created {len(sessions)} sessions',
            'current_epoch': now
        })
    }
EOF
zip function.zip lambda_function.py

ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
aws lambda create-function --function-name insert-sessions --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip
aws lambda wait function-active-v2 --function-name insert-sessions

aws lambda invoke --function-name insert-sessions out.json
cat out.json

date +%s
aws dynamodb scan --table-name lab15-sessions --query "Items[].[session_id.S,user_id.S,expires_at.N]" --output table

date +%s
aws dynamodb scan --table-name lab15-sessions --query "Items[].[session_id.S,expires_at.N]" --output table

BK_ARN=$(aws dynamodb create-backup --table-name lab15-sessions --backup-name sessions-backup-test --query BackupDetails.BackupArn --output text)
echo $BK_ARN
aws dynamodb describe-backup --backup-arn $BK_ARN --query "BackupDescription.BackupDetails.[BackupName,BackupStatus,BackupType]" --output text

aws dynamodb update-continuous-backups --table-name lab15-sessions --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
aws dynamodb describe-continuous-backups --table-name lab15-sessions --query "ContinuousBackupsDescription.PointInTimeRecoveryDescription"

NOME=riccardogouthier
BUCKET=lab15-lifecycle-$NOME
aws s3api create-bucket --bucket $BUCKET
echo "file di test 1" > test1.txt; echo "file di test 2" > test2.txt
aws s3 cp test1.txt s3://$BUCKET/
aws s3 cp test2.txt s3://$BUCKET/
aws s3 ls s3://$BUCKET/

cat > lifecycle.json <<'EOF'
{
  "Rules": [
    {
      "ID": "archive-old-files",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"}
      ],
      "Expiration": {"Days": 365}
    }
  ]
}
EOF
aws s3api put-bucket-lifecycle-configuration --bucket $BUCKET --lifecycle-configuration file://lifecycle.json
aws s3api get-bucket-lifecycle-configuration --bucket $BUCKET

# --- Cleanup ---
# (cleanup, commentato)
# aws dynamodb delete-backup --backup-arn $BK_ARN
# aws dynamodb update-continuous-backups --table-name lab15-sessions --point-in-time-recovery-specification PointInTimeRecoveryEnabled=false
# aws dynamodb delete-table --table-name lab15-sessions
# aws lambda delete-function --function-name insert-sessions
# aws s3 rm s3://$BUCKET --recursive && aws s3api delete-bucket --bucket $BUCKET
# aws logs delete-log-group --log-group-name /aws/lambda/insert-sessions

#==============================================================================
# LABORATORIO 16 - Laboratorio 16 - Step Functions: workflow di elaborazione ordini
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
echo $ROLE_ARN

mkdir -p lab16 && cd lab16

cat > validate.py <<'EOF'
import json

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)

    if total <= 0:
        raise ValueError(f"Invalid order total: {total}")

    return {
        'order_id': order_id,
        'total': total,
        'status': 'validated'
    }
EOF

cat > discount.py <<'EOF'
import json

def lambda_handler(event, context):
    total = event['total']
    discount = total * 0.1  # 10% discount
    new_total = round(total - discount, 2)

    return {
        'order_id': event['order_id'],
        'original_total': total,
        'discount': round(discount, 2),
        'total': new_total,
        'status': 'discounted'
    }
EOF

cat > confirm.py <<'EOF'
import json

def lambda_handler(event, context):
    return {
        'order_id': event['order_id'],
        'total': event['total'],
        'status': 'confirmed',
        'message': f"Order {event['order_id']} confirmed. Total: {event['total']} EUR"
    }
EOF

for p in "validate validate-order" "discount apply-discount" "confirm confirm-order"; do
  set -- $p
  cp $1.py lambda_function.py
  zip -q $1.zip lambda_function.py
  aws lambda create-function --function-name $2 --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://$1.zip --query "[FunctionName,Runtime,State]" --output text
  aws lambda wait function-active-v2 --function-name $2
done
cd ..
aws lambda list-functions --query "Functions[?starts_with(FunctionName,'validate-')||starts_with(FunctionName,'apply-')||starts_with(FunctionName,'confirm-')].[FunctionName,Runtime]" --output table

REGION=us-east-1
ACC=$(aws sts get-caller-identity --query Account --output text)
VAL=arn:aws:lambda:$REGION:$ACC:function:validate-order
DIS=arn:aws:lambda:$REGION:$ACC:function:apply-discount
CON=arn:aws:lambda:$REGION:$ACC:function:confirm-order

cat > order-processor.asl.json <<EOF
{
  "Comment": "Order processor",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$VAL", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "CheckAmount"
    },
    "CheckAmount": {
      "Type": "Choice",
      "Choices": [
        {"Variable": "\$.total", "NumericGreaterThan": 100, "Next": "ApplyDiscount"}
      ],
      "Default": "ConfirmOrder"
    },
    "ApplyDiscount": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$DIS", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "ConfirmOrder"
    },
    "ConfirmOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$CON", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "Success"
    },
    "Success": {"Type": "Succeed"}
  }
}
EOF

SM_ARN=$(aws stepfunctions create-state-machine --name order-processor --definition file://order-processor.asl.json --role-arn $ROLE_ARN --type STANDARD --query stateMachineArn --output text)
echo $SM_ARN
aws stepfunctions describe-state-machine --state-machine-arn $SM_ARN --query "[name,status,type]" --output text

EX1=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-001 --input '{"order_id":"ORD-001","total":50}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX1 --query "[status,output]" --output text

aws stepfunctions get-execution-history --execution-arn $EX1 --query "events[?type=='TaskStateEntered'||type=='ChoiceStateEntered'].[id,type,stateEnteredEventDetails.name]" --output table

EX2=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-002 --input '{"order_id":"ORD-002","total":200}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX2 --query "[status,output]" --output text
aws stepfunctions get-execution-history --execution-arn $EX2 --query "events[?type=='TaskStateEntered'||type=='ChoiceStateEntered'].[id,type,stateEnteredEventDetails.name]" --output table

EX3=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-003 --input '{"order_id":"ORD-003","total":-10}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX3 --query "[status,error,cause]" --output text

# --- Cleanup ---
# (cleanup, commentato)
# aws stepfunctions delete-state-machine --state-machine-arn $SM_ARN
# for f in validate-order apply-discount confirm-order; do aws lambda delete-function --function-name $f; done

#==============================================================================
# LABORATORIO 17 - Laboratorio 17 - Step Functions: gestione errori e integrazioni dirette
#==============================================================================
cd "$HOME"
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

# --- Cleanup ---
# (cleanup, commentato)
# aws stepfunctions delete-state-machine --state-machine-arn $SM2
# aws stepfunctions delete-state-machine --state-machine-arn $SM3
# for f in validate-order-v2 process-payment handle-failure; do aws lambda delete-function --function-name $f; done
# aws dynamodb delete-table --table-name lab17-orders
# aws s3 rm s3://$BUCKET --recursive && aws s3api delete-bucket --bucket $BUCKET
# aws logs delete-log-group --log-group-name step-functions-lab17

#==============================================================================
# LABORATORIO 18 - Laboratorio 18 - AWS SAM, CloudFormation e monitoraggio CloudWatch
#==============================================================================
cd "$HOME"
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

# --- Cleanup ---
# (cleanup, commentato)
# aws cloudwatch delete-dashboards --dashboard-names lab18-serverless
# aws cloudwatch delete-alarms --alarm-names lab18-lambda-errors
# aws cloudformation delete-stack --stack-name monitored-api-lab18
# aws cloudformation delete-stack --stack-name order-api-lab18
# aws cloudformation wait stack-delete-complete --stack-name monitored-api-lab18
# aws cloudformation wait stack-delete-complete --stack-name order-api-lab18
