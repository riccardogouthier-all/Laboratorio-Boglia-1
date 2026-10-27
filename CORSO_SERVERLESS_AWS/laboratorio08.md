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
