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
REPORT ... Duration: 2.16 ms  Billed Duration: 94 ms  Memory Size: 128 MB  Max Memory Used: 37 MB  Init Duration: (cold start)
```

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

Trigger: regola EventBridge `every-5-min-rule` (ogni 5 minuti).

### Step 6 - Verifica nei log CloudWatch

- Esecuzioni osservate alle 16:36:01 e 16:41:01 (UTC+02:00), cioe a distanza di 5 minuti.
- Evento ricevuto: `detail-type` = `Scheduled Event`, `source` = `aws.events`, `region` = `us-east-1`, `resources` = ARN della regola `every-5-min-rule`.
- REPORT tipico: Duration 1,71 ms, Billed Duration 67 ms, Memory Size 128 MB, Max Memory Used 37 MB.

## Prove

| # | Prova | Tipo | Esito |
|---|---|---|---|
| 1 | Upload di un file nel bucket | Trigger S3 | Lambda invocata, log con chiave e dimensione corrette |
| 2 | Nome file con spazio | Decodifica chiave | Chiave letta correttamente grazie a `unquote_plus` |
| 3 | Attesa di piu intervalli da 5 min | Trigger EventBridge | Esecuzioni periodiche visibili nei log |

## Conclusioni

1. Lo stesso modello a eventi serve sia per eventi di dati (S3) sia per eventi temporali (EventBridge).
2. Il payload dell'evento cambia per sorgente: `Records[]` per S3, `Scheduled Event` per EventBridge.
3. I cold start (Init Duration) compaiono nella prima esecuzione dopo il deploy; le successive sono warm.
