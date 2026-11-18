# Consegna Lab 08 - CloudWatch e AWS Config

## CloudWatch
- Metrica custom: namespace `Sicurezza08`, metrica `ErroriAccesso`, dimensione `Studente=rg`
- Pubblicata con CLI: valore 5 alle 19:14 UTC, poi 0 alle 19:16 UTC
- Allarme `sicurezza08-rg` (creato con Terraform): statistica `Sum`, periodo 1 minuto, soglia `> 3`, nessuna azione/notifica

| Valore pubblicato | Stato allarme |
|---|---|
| 5 | `ALARM` (somma 5 > soglia 3 nel periodo di 1 minuto) |
| 0 (periodo successivo) | `OK` atteso (non osservato) |

## AWS Config
Nella console AWS Config risulta non attivo in `us-east-1` (nessun recorder, schermata di benvenuto). Non sono stati creati recorder né canali di consegna.

### Progetto locale della regola `ENCRYPTED_VOLUMES`
- Prerequisiti: recorder, service-linked role, delivery channel S3
- Scope: `AWS::EC2::Volume`

| Caso | Volume | Valutazione | Motivazione |
|---|---|---|---|
| A | cifrato e collegato | conforme | la regola `ENCRYPTED_VOLUMES` controlla che i volumi collegati a un'istanza siano cifrati: qui lo sono |
| B | non cifrato e collegato | non conforme | il volume è collegato ma non cifrato: viola la regola |
| C | non collegato | non applicabile | `ENCRYPTED_VOLUMES` valuta solo i volumi in stato `in-use`, quindi un volume `available` resta fuori dalla valutazione |
| D | non registrato | non valutabile | Config valuta solo le risorse che il recorder ha registrato; senza recorder (o senza il tipo `AWS::EC2::Volume`) non esiste un elemento di configurazione da valutare |

## Limite
Un allarme `OK` non prova la conformità dei volumi: monitoraggio e conformità sono controlli diversi.

## Screenshot e log
Cartella: `screenshots-sicurezza/lab-08/`

- `cleanup-02.png`
- `log-cleanup-8.txt`
- `log-lab-8.txt`
- `passo-02.png`
- `passo-03.png`
- `passo-04.png`
- `passo-05.png`
- `passo-06.png`

## Checkpoint
- [x] Metrica custom pubblicata, allarme in `ALARM` con valore 5
- [x] Ritorno a `OK` dichiarato come atteso, non osservato
- [x] Config non attivo: nessuna risorsa creata, regola solo progettata
- [x] Quattro casi di valutazione motivati
- [x] Cleanup descritto nel documento (eliminazione dell'allarme); le metriche restano secondo la retention AWS

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

Steps 17-19 (regola `ENCRYPTED_VOLUMES`): se Config non è attivo, nessun recorder né delivery channel viene creato; la regola è un progetto con scope `AWS::EC2::Volume` e quattro valutazioni (A conforme, B non conforme, C non applicabile, D non valutabile). Un allarme `OK` non prova la conformità dei volumi.

### Cleanup

```bash
aws cloudwatch delete-alarms --alarm-names sicurezza08-$SUF --region us-east-1
aws cloudwatch describe-alarms --alarm-names sicurezza08-$SUF --query "MetricAlarms" --output text    # atteso: vuoto
```

Le metriche già pubblicate in `Sicurezza08` non si cancellano manualmente e restano secondo la retention AWS.
