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

Procedura di esecuzione in CLI Cloudshell:

Il laboratorio e di analisi (nessuna risorsa AWS da creare). Il calcolo dei consumi si riproduce in CloudShell con `awk`.

```bash
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
```

Output atteso: cloud 447.920 kWh (-48%), cloud + smart working 399.920 kWh (-54%), CO2 evitata 105,1 / 12,0 / 117,1 t/anno.

Lo schema della smart grid (IoT Core -> Kinesis -> Lambda -> S3 -> SageMaker -> QuickSight) e un diagramma di progetto: non viene deployato.
