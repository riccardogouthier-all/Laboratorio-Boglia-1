# Laboratorio 01 - Green IT: Smart Working e Smart Grid

Lavoro di gruppo (Gruppo 2: Matteo Ninotti / Riccardo Gouthier / Ivan Cioffi).

## Scenario

FictaCorp: 200 dipendenti, 10 rack server, ufficio 80.000 kWh/anno. Obiettivo: confrontare consumo on-premise, cloud AWS e cloud + smart working; progettare uno schema AWS per una smart grid.

## Step 1 - Consumo attuale data center

Consumi energetici, confronto annuale.

| Scenario | Data center (kWh) | Ufficio (kWh) | Totale (kWh) | Risparmio vs baseline | Stato |
|---|---|---|---|---|---|
| On-premise attuale (PUE 1,8, nessuno SW) | 788.400 | 80.000 | 868.400 | - | Baseline |
| Cloud AWS (PUE 1,2, right-sizing -30%, nessuno SW) | 367.920 | 80.000 | 447.920 | 420.480 kWh | -48% |
| Cloud + Smart Working 60% (PUE 1,2, right-sizing -30%, ufficio -40%) | 367.920 | 32.000 | 399.920 | 468.480 kWh | -54% |

## Step 2 - Stima consumo equivalente su AWS

Confronto trimestrale (valori = annuale / 4, trimestre tipo di 90,25 giorni medi).

| Scenario | Data center (kWh) | Ufficio (kWh) | Totale (kWh) | Risparmio trimestrale | Stato |
|---|---|---|---|---|---|
| On-premise attuale | 197.100 | 20.000 | 217.100 | - | Baseline |
| Cloud AWS | 91.980 | 20.000 | 111.980 | 105.120 kWh | -48% |
| Cloud + Smart Working 60% | 91.980 | 8.000 | 99.980 | 117.120 kWh | -54% |

## Step 3 - Impatto dello smart working (risparmio CO2)

| Transizione | kWh risparmiati/anno | kWh risparmiati/trim. | CO2 evitata/anno (t) | CO2 evitata/trim. (t) |
|---|---|---|---|---|
| On-premise -> Cloud | 420.480 | 105.120 | 105,1 | 26,3 |
| Solo Smart Working (ufficio) | 48.000 | 12.000 | 12,0 | 3,0 |
| On-premise -> Cloud + SW | 468.480 | 117.120 | 117,1 | 29,3 |

## Schema AWS smart grid

### Flusso dati

```
Smart meter --(MQTT/HTTP)--> IoT Core --> Kinesis Data Streams --> Lambda --> S3 (data lake)
                                                                                  |
                                                         SageMaker <--------------+
                                                             |
                                                        QuickSight (dashboard)
```

### Layer e servizi

| Layer | Servizio AWS | Protocollo / tipo | Ruolo nella smart grid | Input / Output principali |
|---|---|---|---|---|
| Campo | Smart meter (dispositivo IoT) | MQTT / HTTP | Misura i consumi in tempo reale presso utenze, rack server e impianti; letture ogni 15 min o meno | IN: alimentazione elettrica; OUT: kWh, tensione, corrente -> IoT Core |
| Ingestione | AWS IoT Core | Managed broker, MQTT / WebSocket | Riceve i messaggi dai sensori, autentica i dispositivi, smista i dati verso Kinesis o Lambda tramite regole | IN: messaggi MQTT; OUT: topic -> Kinesis Data Streams |
| Ingestione | Amazon Kinesis Data Streams | Stream real-time | Processa lo streaming continuo a bassa latenza; rileva picchi di carico e variazioni di tensione prima dell'archiviazione | IN: stream da IoT Core; OUT: record -> S3, Lambda |
| Processing | AWS Lambda | Serverless function, event-driven | Normalizzazione dati, alert su soglie di consumo, chiamate agli endpoint SageMaker per inferenza | IN: eventi da Kinesis / IoT Core; OUT: alert, dati normalizzati -> S3, SNS |
| Storage | Amazon S3 | Object storage, REST / S3 API | Serie storica completa delle letture (Parquet o CSV); data lake per training ML, audit e compliance | IN: record da Kinesis; OUT: dataset -> SageMaker, QuickSight |
| Analytics | Amazon SageMaker | ML platform, REST endpoint | Addestra modelli di previsione dei carichi (DeepAR, LSTNet) sui dati storici; rileva anomalie (RandomCutForest) | IN: dataset storico da S3; OUT: forecast kWh, anomaly score -> QuickSight, Lambda |
| Analytics | Amazon QuickSight | BI dashboard, HTTPS / embed | Dashboard interattive di consumi in tempo reale, previsioni SageMaker e KPI di sostenibilita (kWh risparmiati, CO2 evitata) | IN: dati da S3, SageMaker; OUT: dashboard -> utenti finali |

## Conclusioni

1. Migrare dall'on-premise ad AWS riduce il consumo del 48% (420.480 kWh/anno).
2. Aggiungendo smart working al 60% (ufficio -40%) il risparmio sale al 54% (468.480 kWh/anno, 117,1 t CO2 evitate/anno).
3. Lo smart working da solo vale 48.000 kWh/anno (12,0 t CO2).
4. Pipeline smart grid interamente su servizi gestiti: IoT Core -> Kinesis -> Lambda -> S3 -> SageMaker -> QuickSight.