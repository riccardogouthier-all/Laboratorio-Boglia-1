# Laboratorio 06 - Prima Funzione Lambda

Autore: Riccardo Gouthier (Gruppo 2).

## Scenario

Prima funzione Lambda `hello-serverless` (runtime Python 3.12). Restituisce un JSON con messaggio `Hello, Mario!`, nome funzione, memoria configurata e tempo di esecuzione. Confronto cold start vs warm start a 128 MB e 256 MB leggendo le righe `REPORT` in CloudWatch Logs.

## Misure (rilevamento studente)

### Lambda 128 MB

| Tipo | Duration | Billed Duration | Memory Size | Max Memory Used | Init Duration |
|---|---|---|---|---|---|
| cold | 4,27 ms | 93 ms | 128 MB | 36 MB | 88,10 ms |
| warm | 13,61 ms | 14 ms | 128 MB | 36 MB | - |

### Lambda 256 MB

| Tipo | Duration | Billed Duration | Memory Size | Max Memory Used | Init Duration |
|---|---|---|---|---|---|
| cold | 2,23 ms | 103 ms | 256 MB | 36 MB | 99,93 ms |
| warm | 1,82 ms | 2 ms | 256 MB | 36 MB | - |

## Confronto cold start

| Dimensione memoria | Billed Duration (ms) | Init Duration (ms) |
|---|---|---|
| 128 MB | 93 | 88,10 |
| 256 MB | 103 | 99,93 |

## Rilevamento di verifica

Stessa procedura CLI rieseguita il 17/11/2026 su un altro account Learner Lab (us-east-1, Python 3.12). Una sola misura per tipo, come nel rilevamento dello studente.

| Memoria | Tipo | Duration | Billed Duration | Max Memory Used | Init Duration |
|---|---|---|---|---|---|
| 128 MB | cold | 1,75 ms | 78 ms | 32 MB | 75,38 ms |
| 128 MB | warm (a caldo) | 1,63 ms | 2 ms | 32 MB | - |
| 256 MB | cold | 1,98 ms | 97 ms | 32 MB | 94,79 ms |
| 256 MB | warm (a caldo) | 1,55 ms | 2 ms | 32 MB | - |

Le relazioni delle osservazioni 1-3 si confermano (cold: 75,38 + 1,75 = 77,13 arrotondati a 78 ms; 94,79 + 1,98 = 96,77 arrotondati a 97 ms). I valori assoluti differiscono: a caldo a 128 MB la verifica dà 1,63 ms contro 13,61 ms dello studente, quindi la differenza a caldo tra 128 e 256 MB non è riproducibile in modo netto (1,63 contro 1,55 ms): per una funzione così breve conta più la variabilità della singola misura che la CPU assegnata.

## Osservazioni

1. Nel **cold start** la Billed Duration è uguale a Init Duration + Duration, arrotondata per eccesso al ms: la fase di Init è fatturata anche per le funzioni con runtime gestito (128 MB: 88,10 + 4,27 = 92,37, fatturati 93 ms; 256 MB: 99,93 + 2,23 = 102,16, fatturati 103 ms).
2. Nel **warm start** non c'è Init Duration: la Billed Duration è la sola Duration (arrotondata).
3. "Max Memory Used" resta ~36 MB indipendentemente dalla memoria configurata: la funzione è troppo leggera per sfruttare più memoria.
4. **128 MB contro 256 MB.** A caldo la funzione passa da 13,61 ms a 1,82 ms: con più memoria Lambda assegna più CPU, quindi il codice gira più veloce. Il caldo a 128 MB (13,61 ms) è più lento del cold Duration (4,27 ms) perché la misura singola è influenzata da altri fattori (la prima esecuzione a 128 MB si è comportata in modo anomalo): una sola misura per tipo non basta per confrontare i valori assoluti. A freddo la Init Duration è invece leggermente più alta a 256 MB (99,93 ms contro 88,10 ms): il tempo di avvio del runtime non dipende dalla memoria, la differenza sta nella variabilità della misura. Per concludere con sicurezza servirebbero più invocazioni per ogni memoria.
5. **Output della funzione.** Con evento `{"name": "Mario"}` la risposta contiene `"message": "Hello, Mario!"`, il nome della funzione, la memoria configurata e il tempo di esecuzione.
6. Un'invocazione ripetuta dopo circa 15 minuti di inattività torna a essere a freddo: Lambda ha rimosso l'ambiente di esecuzione. Il tempo esatto non è garantito da AWS.

## Prove (evidenze)

| # | Prova | Esito |
|---|---|---|
| 1 | Invocazione a freddo con 128 MB | Riga `REPORT` con Init Duration 88,10 ms |
| 2 | Invocazione a caldo con 128 MB | Billed Duration 14 ms, senza Init Duration |
| 3 | Invocazione a freddo con 256 MB | Riga `REPORT` con Init Duration 99,93 ms |
| 4 | Invocazione a caldo con 256 MB | Billed Duration 2 ms, senza Init Duration |

Procedura di esecuzione in CLI Cloudshell:

```bash
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
```

Lettura dei risultati: confrontare `Duration`, `Billed Duration`, `Memory Size`, `Max Memory Used` e `Init Duration` (solo nei cold start) tra le righe a 128 MB e a 256 MB.

### Cleanup

```bash
aws lambda delete-function --function-name hello-serverless
aws logs delete-log-group --log-group-name /aws/lambda/hello-serverless
```
