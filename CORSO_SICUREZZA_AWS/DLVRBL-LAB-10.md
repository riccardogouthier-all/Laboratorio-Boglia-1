# Consegna Lab 10 - GuardDuty, Inspector e risposta ai finding

## Stato iniziale (dato reale)
In `us-east-1` non esisteva nessun detector GuardDuty (`list-detectors` vuoto). Ne ho creato uno con Terraform per questo lab (detector `1ad0f299de4dad8adcd72b0f1e05ffdc`), da eliminare a fine lab. Contatori a zero appena creato; ho generato 2 finding SAMPLE via CLI (`create-sample-findings`).

## Finding GuardDuty (SAMPLE)
| # | Tipo | Gravità | Regione | Risorsa | Attività |
|---|---|---|---|---|---|
| G1 | `Backdoor:EC2/DenialOfService.Tcp` | alta 8.0 | us-east-1 | Instance `i-99999999` (fittizia) | l'istanza si comporta come sorgente di DoS via TCP |
| G2 | `UnauthorizedAccess:EC2/SSHBruteForce` | bassa 2.0 | us-east-1 | Instance `i-99999999`, sorgente `198.51.100.0` (indirizzo di documentazione) | tentativi di brute force SSH |

Evidenza SAMPLE: titolo con prefisso `[SAMPLE]` e id istanza fittizio.

| | G1 | G2 |
|---|---|---|
| Prima verifica (caso reale) | traffico in uscita (VPC Flow Logs) e processi sull'istanza | porta 22 esposta? login riusciti? |
| Contenimento | isolare con Security Group senza regole, snapshot per l'analisi | restringere il Security Group, usare SSM invece di SSH |

Priorità: G1 prima di G2. Motivo: G1 ha gravità più alta (8.0 contro 2.0) e indica un'istanza che attacca terzi, con danno possibile ora; G2 è un tentativo di accesso in ingresso che si ferma restringendo la porta 22.

## Inspector (casi sintetici, nessuna scansione reale)
Inspector non attivato: i casi sono forniti dal laboratorio.

| Ordine | Caso | Gravità / contesto | Azione | Tempo obiettivo |
|--:|---|---|---|---|
| 1 | V1 - EC2 esposta | CRITICAL, exploit noto, patch disponibile | applicare la patch | 24 h |
| 2 | V3 - Lambda pubblica con dati riservati | HIGH, exploit pubblico, nessuna patch | mitigazione temporanea con WAF/limitazione accesso e rimozione della dipendenza; verifica con test negativo | 72 h |
| 3 | V2 - ECR di test non distribuita | HIGH, nessun exploit | correzione al prossimo rilascio | prossimo rilascio |
| - | V4 - agente non connesso | lacuna di copertura | ripristinare SSM Agent/copertura e ripetere il controllo Coverage | 7 giorni |

V4 non è priva di vulnerabilità: è una lacuna di copertura (nessuna scansione eseguita). Tempi: 24 ore per V1 perché è critica, con exploit noto e patch già disponibile (nessun motivo per aspettare). 72 ore per V3 perché senza patch serve prima una mitigazione. V2 aspetta il prossimo rilascio perché l'immagine non è distribuita. 7 giorni per V4 perché è una lacuna di copertura senza exploit.

| Caso | Responsabile | Prova di chiusura | Rischio residuo |
|---|---|---|---|
| V1 | team che gestisce l'istanza EC2 | nuova scansione Inspector senza il finding sulla stessa istanza | nessuno dopo la patch; finestra di esposizione fino all'applicazione |
| V3 | team proprietario della Lambda | test negativo: la funzione non risponde più a chiamate pubbliche e la dipendenza vulnerabile non compare nel nuovo pacchetto | fino alla rimozione della dipendenza resta l'exploit pubblico, ridotto dalla limitazione di accesso |
| V2 | team che pubblica l'immagine ECR | scansione dell'immagine ricostruita senza il finding | basso: l'immagine non è distribuita |
| V4 | team che gestisce l'istanza e l'agente SSM | Coverage Inspector che riporta l'istanza come coperta | l'istanza non è scansionata finché l'agente non è connesso: vulnerabilità sconosciute |

## Distinzioni
- G1, G2 e V1-V4 sono SAMPLE/sintetici, non incidenti reali. Il dato reale osservato è solo l'assenza di detector prima del lab.
- Una vulnerabilità non prova uno sfruttamento.
- Zero finding non significa zero vulnerabilità.

## Cleanup finale (risorse dei Lab 06-10)
Eseguito con `terraform destroy` (36 risorse eliminate): VPC `sicurezza06-rg` con subnet, Security Group e Network ACL, log group `/sicurezza07/rg`, allarme `sicurezza08-rg`, Web ACL `sicurezza09-rg`, detector GuardDuty (creato per il lab) e le risorse del documento VM/Storage.

Verifica via CLI: resta solo la VPC di default; nessun detector GuardDuty, nessuna Web ACL, nessun allarme, nessun log group.

Non ancora rimosso: il segreto `sicurezza09/rg`, in eliminazione pianificata con 7 giorni di recupero (data di cancellazione 2026-11-16 20:38:59 +01:00); non è stata usata l'eliminazione forzata. Le metriche già pubblicate in `Sicurezza08` restano secondo la retention AWS e l'evento CloudTrail resta nell'account.

## Screenshot e log
Cartella: `screenshots-sicurezza/lab-10/`

- `cleanup-02.png`
- `cleanup-03.png`
- `log-cleanup-10.txt`
- `log-lab-10.txt`
- `passo-02.png`
- `passo-03.png`
- `passo-04.png`
- `passo-05.png`
- `passo-06.png`

## Checkpoint
- [x] Stato iniziale reale dichiarato
- [x] G1 e G2 analizzati con verifica, contenimento e priorità
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

# Finding SAMPLE: G1 (alta gravità) e G2 (bassa gravità)
aws guardduty create-sample-findings --detector-id $DETECTOR_ID \
  --finding-types Backdoor:EC2/DenialOfService.Tcp UnauthorizedAccess:EC2/SSHBruteForce --region us-east-1

# Elenco e dettaglio dei finding SAMPLE: type, severity, resource, indicatore sample
sleep 15
FIDS=$(aws guardduty list-findings --detector-id $DETECTOR_ID --region us-east-1 --query "FindingIds" --output text)
aws guardduty get-findings --detector-id $DETECTOR_ID --finding-ids $FIDS --region us-east-1 \
  --query "Findings[].[Title,Type,Severity,Resource.ResourceType,Region,Service.AdditionalInfo.Value]" --output table
```

Parte C (Inspector): i casi V1-V4 sono sintetici e vanno trattati nel deliverable; Inspector non è attivato e non viene eseguita nessuna scansione. Per verificare la copertura (solo lettura):

```bash
aws inspector2 batch-get-account-status --region us-east-1 2>&1 | head -20      # se Inspector non è attivo / accesso negato: registrare l'errore, non modificare IAM
```

### Cleanup finale (risorse dei Lab 06-10)

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
