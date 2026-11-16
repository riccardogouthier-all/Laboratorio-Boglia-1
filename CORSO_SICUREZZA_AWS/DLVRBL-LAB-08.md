# Consegna Lab 08 - CloudWatch e AWS Config

## CloudWatch
- Metrica custom: namespace `Sicurezza08`, metrica `ErroriAccesso`, dimensione `Studente=rg`
- Pubblicata con CLI: valore 5 alle 19:14 UTC, poi 0 alle 19:16 UTC
- Allarme `sicurezza08-rg` (creato con Terraform): statistica `Sum`, periodo 1 minuto, soglia `> 3`, nessuna azione/notifica

| Valore pubblicato | Stato allarme |
|---|---|
| 5 | `ALARM` (screenshot) |
| 0 (periodo successivo) | `OK` atteso (non osservato) |

## AWS Config
Nella console AWS Config risulta non attivo in `us-east-1` (nessun recorder, schermata di benvenuto). Non sono stati creati recorder ne canali di consegna.

### Progetto locale della regola `ENCRYPTED_VOLUMES`
- Prerequisiti: recorder, service-linked role, delivery channel S3
- Scope: `AWS::EC2::Volume`

| Caso | Volume | Valutazione |
|---|---|---|
| A | cifrato e collegato | conforme |
| B | non cifrato e collegato | non conforme |
| C | non collegato | non applicabile |
| D | non registrato | non valutabile |

## Limite
Un allarme `OK` non prova la conformita dei volumi: monitoraggio e conformita sono controlli diversi.

## Checkpoint
- [x] Metrica custom pubblicata, allarme in `ALARM` con valore 5
- [x] Ritorno a `OK` dichiarato come atteso, non osservato
- [x] Config non attivo: nessuna risorsa creata, regola solo progettata
- [x] Quattro casi di valutazione motivati
- [x] Allarme rimosso nel cleanup finale (Lab 6-10); le metriche restano secondo la retention AWS

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
SUF=rg

# Steps 1-2 - Metrica custom: valore 5
aws cloudwatch put-metric-data --namespace Sicurezza08 --metric-name ErroriAccesso --dimensions Studente=$SUF --value 5 --unit Count --region us-east-1

# Steps 3-10 - Allarme: Sum, periodo 1 minuto, soglia > 3, nessuna azione/notifica
aws cloudwatch put-metric-alarm --alarm-name sicurezza08-$SUF --namespace Sicurezza08 --metric-name ErroriAccesso --dimensions Name=Studente,Value=$SUF --statistic Sum --period 60 --evaluation-periods 1 --threshold 3 --comparison-operator GreaterThanThreshold --treat-missing-data missing --no-actions-enabled --region us-east-1

# Step 11 - Stato dell'allarme (atteso ALARM dopo la valutazione) e cronologia
sleep 90
aws cloudwatch describe-alarms --alarm-names sicurezza08-$SUF --query "MetricAlarms[].[AlarmName,StateValue,Threshold]" --output table
aws cloudwatch describe-alarm-history --alarm-name sicurezza08-$SUF --max-items 5 --query "AlarmHistoryItems[].[Timestamp,HistorySummary]" --output table

# Step 12 - Valore 0 in un periodo successivo: ritorno atteso a OK
aws cloudwatch put-metric-data --namespace Sicurezza08 --metric-name ErroriAccesso --dimensions Studente=$SUF --value 0 --unit Count --region us-east-1
sleep 120
aws cloudwatch describe-alarms --alarm-names sicurezza08-$SUF --query "MetricAlarms[].[AlarmName,StateValue]" --output table

# Steps 13-16 - AWS Config: verifica dello stato (sola lettura)
aws configservice describe-configuration-recorders --region us-east-1        # lista vuota = Config non attivo
aws configservice describe-config-rules --region us-east-1 --query "ConfigRules[].ConfigRuleName" 2>/dev/null
```

Steps 17-19 (regola `ENCRYPTED_VOLUMES`): se Config non e attivo, nessun recorder ne delivery channel viene creato; la regola e un progetto con scope `AWS::EC2::Volume` e quattro valutazioni (A conforme, B non conforme, C non applicabile, D non valutabile). Un allarme `OK` non prova la conformita dei volumi.

### Cleanup

```bash
aws cloudwatch delete-alarms --alarm-names sicurezza08-$SUF --region us-east-1
aws cloudwatch describe-alarms --alarm-names sicurezza08-$SUF --query "MetricAlarms" --output text    # atteso: vuoto
```

Le metriche gia pubblicate in `Sicurezza08` non si cancellano manualmente e restano secondo la retention AWS.
