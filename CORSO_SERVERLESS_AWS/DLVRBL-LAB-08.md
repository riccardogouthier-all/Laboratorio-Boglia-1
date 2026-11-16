# Laboratorio 08 - Risorse Lambda e Monitoraggio

Autore: Riccardo Gouthier (Gruppo 2). Corrisponde alla Parte A del "Lab 08-09".

## Scenario

Analizzare come la memoria configurata influenza durata e costo di una Lambda CPU-bound, limitare la concorrenza e monitorare la funzione con allarmi e Logs Insights.

## Step 1 - Funzione `resource-test`

```python
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
```

## Step 2 - Test con memoria crescente

Costo stimato (MB-s) = memoria (MB) x durata (s).

| Memoria | Durata (ms) | Costo stimato (MB-s) |
|---|---|---|
| 128 MB | 158,11 | 20,2 |
| 256 MB | 66,07 | 16,9 |
| 512 MB | 33,42 | 17,1 |
| 1024 MB | 12,83 | 13,1 |

I valori MB-s sono calcolati con la formula sopra a partire dalle durate misurate.

Osservazioni:

1. La durata scende al crescere della memoria: in Lambda la CPU e proporzionale alla memoria allocata.
2. Il costo stimato in MB-s non cresce: piu memoria non vuol dire piu spesa, perche la durata cala quasi in proporzione.
3. Con memoria 1024 MB la stima e la piu bassa e la funzione e la piu veloce.

## Step 3 - Concorrenza riservata

- Configuration -> Concurrency: **Reserved concurrency = 5**.
- Effetto: la funzione non supera 5 esecuzioni simultanee e quella quota viene sottratta al pool dell'account.

## Step 4 - Allarme CloudWatch

- Allarme: `resource-test-errors`
- Condizione: metrica `Errors` della funzione, soglia > 0,1 per 1 datapoint nel periodo configurato.
- Stato iniziale: `Insufficient data` (nessuna invocazione in errore), nessuna azione associata.

## Step 5 - Logs Insights

Query eseguita sui log group (ultima settimana):

```
SOURCE logGroups(namePrefix: [], class: "STANDARD") START=-1w END=0s |
filter @type = "REPORT"
| stats avg(@duration) as avgDuration, max(@duration) as maxDuration, min(@memorySize) as memorySize
| sort avgDuration desc
```

Risultato: grafico a barre con `avgDuration`, `maxDuration` e `memorySize` (valore in byte, ~128 M) sulle righe `REPORT` raccolte (30 record scansionati).

## Conclusioni

1. Aumentare la memoria riduce la durata di un carico CPU-bound senza aumentare il costo in MB-s.
2. La concorrenza riservata protegge le altre funzioni dell'account e limita i costi di una funzione fuori controllo.
3. Allarmi (`Errors`) e Logs Insights sono il minimo per osservare la funzione.

Procedura di esecuzione in CLI Cloudshell:

```bash
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
```

### Cleanup

```bash
aws lambda delete-function-concurrency --function-name resource-test
aws cloudwatch delete-alarms --alarm-names resource-test-errors
aws lambda delete-function --function-name resource-test
aws logs delete-log-group --log-group-name /aws/lambda/resource-test
```
