# Consegna Lab 10 - GuardDuty, Inspector e risposta ai finding

## Stato iniziale (dato reale)
In `us-east-1` non esisteva nessun detector GuardDuty (`list-detectors` vuoto). Ne ho creato uno con Terraform per questo lab (detector `1ad0f299de4dad8adcd72b0f1e05ffdc`), da eliminare a fine lab. Contatori a zero appena creato; ho generato 2 finding SAMPLE via CLI (`create-sample-findings`).

## Finding GuardDuty (SAMPLE)
| # | Tipo | Gravita | Risorsa | Attivita |
|---|---|---|---|---|
| G1 | `Backdoor:EC2/DenialOfService.Tcp` | alta 8.0 | Instance `i-99999999` (fittizia) | l'istanza si comporta come sorgente di DoS via TCP |
| G2 | `UnauthorizedAccess:EC2/SSHBruteForce` | bassa 2.0 | Instance `i-99999999`, sorgente `198.51.100.0` (indirizzo di documentazione) | tentativi di brute force SSH |

Evidenza SAMPLE: titolo con prefisso `[SAMPLE]` e id istanza fittizio.

| | G1 | G2 |
|---|---|---|
| Prima verifica (caso reale) | traffico in uscita (VPC Flow Logs) e processi sull'istanza | porta 22 esposta? login riusciti? |
| Contenimento | isolare con Security Group senza regole, snapshot per l'analisi | restringere il Security Group, usare SSM invece di SSH |

Priorita: G1 prima di G2, perche gravita piu alta e comportamento attivo verso terzi.

## Inspector (casi sintetici, nessuna scansione reale)
Inspector non attivato: i casi sono forniti dal laboratorio.

| Ordine | Caso | Gravita / contesto | Azione | Tempo obiettivo |
|--:|---|---|---|---|
| 1 | V1 - EC2 esposta | CRITICAL, exploit noto, patch disponibile | applicare la patch | 24 h |
| 2 | V3 - Lambda pubblica con dati riservati | HIGH, exploit pubblico, nessuna patch | mitigazione temporanea con WAF/limitazione accesso e rimozione della dipendenza; verifica con test negativo | 72 h |
| 3 | V2 - ECR di test non distribuita | HIGH, nessun exploit | correzione al prossimo rilascio | prossimo rilascio |
| - | V4 - agente non connesso | lacuna di copertura | ripristinare SSM Agent/copertura e ripetere il controllo Coverage | 7 giorni |

V4 non e priva di vulnerabilita: e una lacuna di copertura (nessuna scansione eseguita). Per ogni caso: responsabile il team proprietario, prova di chiusura = nuova scansione senza il finding, rischio residuo noto.

## Distinzioni
- G1, G2 e V1-V4 sono SAMPLE/sintetici, non incidenti reali. Il dato reale osservato e solo l'assenza di detector prima del lab.
- Una vulnerabilita non prova uno sfruttamento.
- Zero finding non significa zero vulnerabilita.

## Cleanup finale (Lab 6-10)
Eseguito con `terraform destroy` (36 risorse eliminate): VPC `sicurezza06-rg` con subnet, Security Group e Network ACL, log group `/sicurezza07/rg`, allarme `sicurezza08-rg`, Web ACL `sicurezza09-rg`, detector GuardDuty (creato per il lab) e le risorse del documento VM/Storage.

Verifica via CLI: resta solo la VPC di default; nessun detector GuardDuty, nessuna Web ACL, nessun allarme, nessun log group.

Non ancora rimosso: il segreto `sicurezza09/rg`, in eliminazione pianificata con 7 giorni di recupero (data di cancellazione 2026-11-16 20:38:59 +01:00); non e stata usata l'eliminazione forzata. Le metriche gia pubblicate in `Sicurezza08` restano secondo la retention AWS e l'evento CloudTrail resta nell'account.

## Checkpoint
- [x] Stato iniziale reale dichiarato
- [x] G1 e G2 analizzati con verifica, contenimento e priorita
- [x] V1-V4 ordinati con tempo obiettivo e prova di chiusura
- [x] Dati SAMPLE distinti dal reale
- [x] Cleanup eseguito e verificato; segreto in eliminazione pianificata

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1

# Parte A - Stato iniziale di GuardDuty (sola lettura)
aws guardduty list-detectors --region us-east-1

# Parte B - Creare il detector solo se non esiste (qui non esisteva: creato per il lab, da eliminare a fine lab)
DETECTOR_ID=$(aws guardduty list-detectors --region us-east-1 --query "DetectorIds[0]" --output text)
if [ "$DETECTOR_ID" = "None" ]; then
  DETECTOR_ID=$(aws guardduty create-detector --enable --region us-east-1 --query DetectorId --output text)
  CREATO_DA_ME=1
fi
echo $DETECTOR_ID

# Contatori iniziali (attesi a zero su un detector appena creato)
aws guardduty get-findings-statistics --detector-id $DETECTOR_ID --finding-statistic-types COUNT_BY_SEVERITY --region us-east-1

# Finding SAMPLE: G1 (alta gravita) e G2 (bassa gravita)
aws guardduty create-sample-findings --detector-id $DETECTOR_ID \
  --finding-types Backdoor:EC2/DenialOfService.Tcp UnauthorizedAccess:EC2/SSHBruteForce --region us-east-1

# Elenco e dettaglio dei finding SAMPLE: type, severity, resource, indicatore sample
sleep 15
FIDS=$(aws guardduty list-findings --detector-id $DETECTOR_ID --region us-east-1 --query "FindingIds" --output text)
aws guardduty get-findings --detector-id $DETECTOR_ID --finding-ids $FIDS --region us-east-1 \
  --query "Findings[].[Title,Type,Severity,Resource.ResourceType,Region,Service.AdditionalInfo.sample]" --output table
```

Parte C (Inspector): i casi V1-V4 sono sintetici e vanno trattati nel deliverable; Inspector non e attivato e non viene eseguita nessuna scansione. Per verificare la copertura (solo lettura):

```bash
aws inspector2 batch-get-account-status --region us-east-1 2>&1 | head -20      # se Inspector non e attivo / accesso negato: registrare l'errore, non modificare IAM
```

### Cleanup finale (Lab 6-10)

```bash
# Elimina il detector solo se creato personalmente in questo lab
[ "$CREATO_DA_ME" = 1 ] && aws guardduty delete-detector --detector-id $DETECTOR_ID --region us-east-1
aws guardduty list-detectors --region us-east-1                                  # atteso: lista vuota

# Verifiche sulle altre risorse dei Lab 06-09 (rimosse con i rispettivi cleanup)
aws ec2 describe-vpcs --query "Vpcs[].[VpcId,IsDefault]" --output table          # solo la VPC di default
aws wafv2 list-web-acls --scope REGIONAL --region us-east-1 --query "WebACLs[].Name"
aws cloudwatch describe-alarms --alarm-name-prefix sicurezza08 --query "MetricAlarms[].AlarmName"
aws logs describe-log-groups --log-group-name-prefix /sicurezza07 --query "logGroups[].logGroupName"
aws secretsmanager describe-secret --secret-id sicurezza09/rg --query "[Name,DeletedDate]"      # in eliminazione pianificata (7 giorni)
```
