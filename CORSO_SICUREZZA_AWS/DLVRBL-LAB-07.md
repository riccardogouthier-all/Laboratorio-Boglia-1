# Consegna Lab 07 - Connettivita sicura e CloudTrail

## Confronto
| Opzione | Caratteristica |
|---|---|
| Site-to-Site VPN | tunnel IPsec, protegge la comunicazione su Internet |
| Direct Connect | connettivita dedicata; la cifratura va progettata separatamente |

## Configurazione
- Log group `/sicurezza07/rg` in `us-east-1`, creato con Terraform il 16 novembre 2026 alle 16:32:14 UTC

## Evento CloudTrail
In CloudTrail Event history, filtro `Event name = CreateLogGroup`:

| Campo | Valore |
|---|---|
| `eventTime` | `2026-11-16T16:32:14Z` |
| `eventName` | `CreateLogGroup` |
| `eventSource` | `logs.amazonaws.com` |
| `userIdentity.type` | `AssumedRole` (ruolo `voclabs`) |
| `requestParameters.logGroupName` | `/sicurezza07/rg` |
| `errorCode` | assente (operazione riuscita) |

## Tre fatti
1. `CreateLogGroup` e un evento di gestione, non traffico applicativo.
2. L'identita e un ruolo assunto, distinta dalla persona.
3. Nessun `errorCode`: l'operazione e riuscita.

## Limiti
- L'evento non prova l'uso di VPN ne di Direct Connect.
- Per attribuire l'azione a una persona servono altri dati di sessione.

## Checkpoint
- [x] Confronto VPN / Direct Connect
- [x] Evento CloudTrail trovato con filtro e campi riportati
- [x] Tre fatti e limiti dichiarati
- [x] Log group rimosso nel cleanup finale (Lab 6-10)

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
SUF=rg

# Steps 2-6 - Log group /sicurezza07/SUFFISSO e ora UTC della creazione
aws logs create-log-group --log-group-name /sicurezza07/$SUF --region us-east-1
date -u +"%Y-%m-%dT%H:%M:%SZ"

# Steps 7-12 - Evento CloudTrail CreateLogGroup (puo richiedere alcuni minuti per comparire)
sleep 60
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateLogGroup --region us-east-1 --max-results 5 \
  --query "Events[].[EventTime,EventName,EventSource,Username]" --output table

# Dettaglio dell'evento del proprio gruppo: eventTime, eventName, eventSource, userIdentity.type, requestParameters.logGroupName, errorCode
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateLogGroup --region us-east-1 --max-results 5 \
  --query "Events[].CloudTrailEvent" --output text | jq -c 'select(.requestParameters.logGroupName=="/sicurezza07/'$SUF'") | {eventTime,eventName,eventSource,identity:.userIdentity.type,logGroup:.requestParameters.logGroupName,errorCode}'
```

Controllo finale: l'evento mostra `CreateLogGroup` da `logs.amazonaws.com`; assenza di `errorCode` = operazione riuscita. E una chiamata di gestione AWS, non traffico applicativo ne prova di uso di VPN. Se l'evento non compare entro 15 minuti, usare il caso sintetico dichiarando la simulazione.

### Cleanup

```bash
aws logs delete-log-group --log-group-name /sicurezza07/$SUF --region us-east-1
aws logs describe-log-groups --log-group-name-prefix /sicurezza07 --query "logGroups[].logGroupName"   # atteso: vuoto
```

L'evento di gestione storico resta nell'account (CloudTrail Event history).
