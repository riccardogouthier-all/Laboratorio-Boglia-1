# Relazione di collaudo — SnackOverflow S.r.l.

Autore: Riccardo Gouthier  
Template collaudati: `NestedStack/root.yaml` + 4 figli, `10-core-exports.yaml`, `20-consumer.yaml`

---

## Requisiti funzionali (RF)

### RF1 — L'applicazione è raggiungibile via HTTP

L'ALB definito in `compute.yaml` espone la porta 80 su internet (`Scheme: internet-facing`).
Il listener inoltra il traffico al Target Group collegato all'ASG.
L'output `SiteURL` del root stack restituisce l'URL pubblico al termine del deploy.

Collaudo: URL aperto nel browser → pagina HTML con AZ di provenienza visibile.

---

### RF2 — Gli asset statici sono persistiti su S3

Il bucket `AssetsBucket` in `data.yaml` è configurato con `DeletionPolicy: Retain` e
`UpdateReplacePolicy: Retain`. La cifratura lato server (AES-256) è abilitata di default.
Il bucket sopravvive a `delete-stack` (CA7 verificato).

---

### RF3 — Le sessioni utente sono gestite su DynamoDB

La tabella `SessionsTable` usa `BillingMode: PAY_PER_REQUEST` e TTL sul campo `ExpiresAt`.
Nessuna capacità da pre-allocare: scala automaticamente con il carico.

---

### RF4 — Gli ordini sono persistiti su RDS MySQL

Il database `Database` in `data.yaml` usa MySQL 8.0. La password master non è mai scritta
in chiaro: viene generata da `AWS::SecretsManager::Secret` e letta a runtime tramite
dynamic reference `{{resolve:secretsmanager:${DbSecret}:SecretString:password}}`.
`DeletionPolicy: Snapshot` garantisce che i dati non vengano persi con `delete-stack`.

---

### RF5 — Il nome del bucket core è condiviso tra stack tramite export/import

`10-core-exports.yaml` crea il bucket e ne esporta il nome fisico con
`Export: Name: snackoverflow-core-bucket-name`.
`20-consumer.yaml` lo importa con `!ImportValue` e lo scrive nel parametro SSM
`/snackoverflow/core-bucket-name`, consumabile da applicazioni o altri stack senza
accoppiamento diretto.

Collaudo della dipendenza: tentativo di `delete-stack snackoverflow-core` con il consumer
attivo → CloudFormation rifiuta, lo stack rimane `CREATE_COMPLETE`.
Cancellazione corretta: prima consumer, poi core.

---

## Requisiti non funzionali (RNF)

### RNF1 — Sicurezza: nessun segreto in chiaro, accesso DB solo dall'app

Nessuna password è presente nei template (CA4: `grep -r "password" NestedStack/` non
restituisce valori in chiaro, solo la dynamic reference).

La catena di Security Group in `security.yaml` implementa il principio del minimo
privilegio:
- `AlbSecurityGroup`: accetta TCP/80 da `0.0.0.0/0`
- `AppSecurityGroup`: accetta TCP/80 solo da `AlbSecurityGroup`
- `DbSecurityGroup`: accetta TCP/3306 solo da `AppSecurityGroup`

Nessun CIDR dopo l'ALB: un SG identifica esattamente la risorsa sorgente, indipendentemente
da subnet o IP (CA5 verificato).

---

### RNF2 — Affidabilità: alta disponibilità su 2 AZ

ALB e ASG sono distribuiti su `PublicSubnet1` e `PublicSubnet2`, in due AZ distinte
(selezionate dinamicamente con `!Select [0/1, !GetAZs '']`).
Se un'AZ diventa non disponibile, l'ALB smette di inviare traffico alle istanze in quella
AZ e l'ASG lancia nuove istanze nell'AZ sana.

RDS è `single-AZ` in dev (vincolo Learner Lab); il Mapping `EnvironmentMap` imposta
`MultiAZ: true` per prod senza modifiche al codice.

---

### RNF3 — Prestazioni: sizing adattivo per ambiente

Il Mapping `EnvironmentMap` nei template `compute.yaml` e `data.yaml` centralizza il
sizing per ambiente:

| Parametro | dev | prod |
|---|---|---|
| EC2 InstanceType | t3.micro | t3.small |
| ASG MinSize | 1 | 2 |
| ASG MaxSize | 2 | 6 |
| RDS DBInstanceClass | db.t3.micro | db.t3.small |
| RDS MultiAZ | false | true |

Il cambio avviene passando `EnvType=prod` al deploy, senza toccare il codice (CA6
verificato con change set `to-prod`).

---

### RNF4 — Costi: nessun sovradimensionamento statico

- ASG scala col carico reale tra `MinSize` e `MaxSize`
- DynamoDB `PAY_PER_REQUEST`: nessuna capacità pagata a riposo
- `Condition CreateDatabase` in `data.yaml`: in dev si può saltare il provisioning RDS
  con `CreateDatabase=false`, eliminando il costo dell'istanza durante lo sviluppo
- Stesso template per tutti gli ambienti: nessun codice duplicato da mantenere

---

### RNF5 — Operabilità: deploy e lifecycle completamente automatizzati

L'intero stack nasce con un comando:

```bash
aws cloudformation deploy \
  --stack-name snackoverflow \
  --template-file NestedStack/root.yaml \
  --parameter-overrides EnvType=dev CreateDatabase=true TemplateBaseURL=<url> \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND
```

Le modifiche vengono valutate prima dell'applicazione tramite change set:

```bash
aws cloudformation create-change-set \
  --stack-name snackoverflow \
  --change-set-name to-prod \
  --template-body file://NestedStack/root.yaml \
  --parameters ParameterKey=EnvType,ParameterValue=prod \
               ParameterKey=CreateDatabase,ParameterValue=true \
               ParameterKey=TemplateBaseURL,ParameterValue=<url> \
  --change-set-type UPDATE \
  --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM
```

Il drift viene rilevato con `detect-stack-drift` e riconciliato ri-applicando il template,
mai intervenendo manualmente in console.

`DeletionPolicy: Retain` sul bucket asset garantisce che `delete-stack` non cancelli i
dati (CA7 verificato).

---

## Riepilogo criteri di accettazione

| Cod. | Criterio | Esito | RF/RNF coperti |
|---|---|---|---|
| CA1 | cfn-lint pulito su tutti i template | ✅ | qualità |
| CA2 | deploy a CREATE_COMPLETE senza intervento manuale | ✅ | RF1–5, RNF5 |
| CA3 | SiteURL risponde nel browser | ✅ | RF1 |
| CA4 | nessun segreto in chiaro nel repo | ✅ | RNF1 |
| CA5 | DB accetta connessioni solo dall'app (catena SG) | ✅ | RNF1 |
| CA6 | EnvType=prod cambia il sizing senza toccare il codice | ✅ | RNF3, RNF4 |
| CA7 | delete-stack NON cancella il bucket asset (Retain) | ✅ | RNF5 |
| CA8 | questa relazione copre tutti gli RF e RNF | ✅ | tutti |

---

## Note sul collaudo

L'unica difficoltà riscontrata durante il collaudo ha riguardato la sintassi dei comandi
AWS CLI: in particolare la composizione corretta di `--parameters`, l'aggiunta di
`--capabilities CAPABILITY_AUTO_EXPAND` per i nested stack, e la comprensione del
comportamento asincrono di `delete-stack` (nessun output immediato è il comportamento
atteso, non un errore).
Nessun problema architetturale o di logica nei template.

Comandi usati per l'esecuzione
```bash
aws s3 mb s3://snackoverflow-tpl-bucket

aws s3 cp NestedStack/ s3://snackoverflow-tpl-bucket/snackoverflow/ --recursive --exclude "root.yaml"

aws cloudformation deploy --stack-name snackoverflow --template-file NestedStack/root.yaml --parameter-overrides TemplateBaseURL=https://snackoverflow-tpl-bucket.s3.amazonaws.com/snackoverflow --capabilities CAPABILITY_NAMED_IAM

aws cloudformation deploy --stack-name snackoverflow --template-file NestedStack/root.yaml --parameter-overrides TemplateBaseURL=https://snackoverflow-tpl-bucket.s3.amazonaws.com/snackoverflow EnvType=dev CreateDatabase=true

aws cloudformation describe-stacks --stack-name snackoverflow --query "Stacks[0].Outputs" --output table

aws cloudformation create-change-set --stack-name snackoverflow --change-set-name to-prod --template-body file://NestedStack/root.yaml --parameters   ParameterKey=TemplateBaseURL,ParameterValue=https://snackoverflow-tpl-bucket.s3.amazonaws.com/snackoverflow   ParameterKey=EnvType,ParameterValue=prod   ParameterKey=CreateDatabase,ParameterValue=true --change-set-type UPDATE --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM

aws cloudformation describe-change-set --change-set-name to-prod --stack-name snackoverflow --query "Changes[].ResourceChange.[Action,LogicalResourceId,Replacement]" --output table

aws cloudformation list-stack-resources --stack-name snackoverflow --query "StackResourceSummaries[?ResourceType=='AWS::CloudFormation::Stack'].{Nome:LogicalResourceId,ARN:PhysicalResourceId}" --output table

aws cloudformation describe-stack-drift-detection-status --stack-name snackoverflow

aws cloudformation update-termination-protection --stack-name snackoverflow --enable-termination-protection


aws cloudformation deploy --stack-name snackoverflow-core --template-file 10-core-exports.yaml

aws cloudformation list-exports --query "Exports[?Name=='snackoverflow-core-bucket-name']" --output table


aws cloudformation deploy --stack-name snackoverflow-consumer --template-file 20-consumer.yaml

aws ssm get-parameter --name /snackoverflow/core-bucket-name --query "Parameter.Value" --output text


aws cloudformation delete-stack --stack-name snackoverflow-core

aws cloudformation describe-stacks --stack-name snackoverflow-core --query "Stacks[0].StackStatus" --output text

aws cloudformation describe-stack-events --stack-name snackoverflow-core --query "StackEvents[0].{Stato:ResourceStatus,Motivo:ResourceStatusReason}" --output table
```
