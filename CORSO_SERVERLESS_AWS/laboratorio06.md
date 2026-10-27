# Laboratorio 06 - Prima Funzione Lambda

Autore: Riccardo Gouthier (Gruppo 2).

## Scenario

Prima funzione Lambda `hello-serverless` (runtime Python 3.12). Restituisce un JSON con messaggio `Hello, Mario!`, nome funzione, memoria configurata e tempo di esecuzione. Confronto cold start vs warm start a 128 MB e 256 MB leggendo le righe `REPORT` in CloudWatch Logs.

## Misure

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

## Osservazioni

1. Nel **cold start** la Billed Duration e uguale a Init Duration + Duration, arrotondata per eccesso al ms (128 MB: 88,10 + 4,27 = 92,37, fatturati 93 ms; 256 MB: 99,93 + 2,23 = 102,16, fatturati 103 ms).
2. Nel **warm start** non c'e Init Duration: la Billed Duration e la sola Duration (arrotondata).
3. "Max Memory Used" resta ~36 MB indipendentemente dalla memoria configurata: la funzione e troppo leggera per sfruttare piu memoria.

## Prove (evidenze)

| # | Prova | Esito |
|---|---|---|
| 1 | Invocazione a freddo con 128 MB | Riga `REPORT` con Init Duration 88,10 ms |
| 2 | Invocazione a caldo con 128 MB | Billed Duration 14 ms, senza Init Duration |
| 3 | Invocazione a freddo con 256 MB | Riga `REPORT` con Init Duration 99,93 ms |
| 4 | Invocazione a caldo con 256 MB | Billed Duration 2 ms, senza Init Duration |
