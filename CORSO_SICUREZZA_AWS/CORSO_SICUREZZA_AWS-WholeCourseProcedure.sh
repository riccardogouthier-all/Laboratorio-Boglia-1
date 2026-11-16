#!/bin/bash
# Sicurezza AWS - procedura completa dei laboratori 1-10 da eseguire in AWS CloudShell (us-east-1).
# I blocchi di cleanup sono commentati: i laboratori successivi riusano le risorse. Decommentarli solo a fine corso.
# Lo script e pensato per essere eseguito per sezioni (lab per lab) leggendo l'output, non come unico lancio cieco.


#==============================================================================
# LABORATORIO 1 - Consegna 01 — Fondamenti di sicurezza
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1

# Identita della sessione: e il dato che permette di attribuire le operazioni a un singolo attore
aws sts get-caller-identity

# Scheletro di consegna01.md con le otto componenti della responsabilita condivisa
cat > consegna01.md <<'EOF'
# Consegna 01 - Fondamenti di sicurezza

## Scenario
Tecnico carica rapporti in S3; analista li legge; responsabile autorizza la cancellazione; app EC2 li elabora.

## Responsabilita
| # | Componente | Responsabile | Controllo | Evidenza |
|--:|---|---|---|---|
| 1 | Edifici (data center) | AWS | Controllo fisico e ambientale | Documentazione di conformita AWS |
| 2 | Host fisico | AWS | Hardware e hypervisor | Modello di responsabilita condivisa |
| 3 | Guest OS su EC2 | Cliente | Patching e hardening | Piano di aggiornamento |
| 4 | Libreria applicativa | Cliente | Aggiornamento dipendenze | Versione installata / changelog |
| 5 | Accesso ai rapporti | Cliente | Permessi minimi su S3 | Lettura consentita, cancellazione negata all'analista |
| 6 | Classificazione dati | Cliente | Etichetta "sintetici" | Etichetta nella consegna |
| 7 | Configurazione di rete | Cliente | Regole coerenti con il flusso | Diagramma |
| 8 | Credenziali e sessioni | Cliente | Identita distinte | Log attribuibile |
EOF
cat consegna01.md

# (Opzionale) prova di attribuzione: ultimi eventi della propria identita in CloudTrail
aws cloudtrail lookup-events --max-results 5 --query "Events[].[EventTime,EventName,Username]" --output table

#==============================================================================
# LABORATORIO 2 - Consegna 02 - Regioni e crittografia dei dati
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
SUF=riccardogouthier

# Step 1-2 - Zone name e Zone ID
aws ec2 describe-availability-zones --region us-east-1 --query 'AvailabilityZones[].[ZoneName,ZoneId,State]' --output table

# Step 3-9 - Bucket privato con SSE-S3, ACL disabilitate, Block Public Access, versioning non abilitato
aws s3api create-bucket --bucket sicurezza02-$SUF --region us-east-1
aws s3api put-bucket-ownership-controls --bucket sicurezza02-$SUF --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'
aws s3api put-public-access-block --bucket sicurezza02-$SUF --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket sicurezza02-$SUF --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Step 10-12 - Oggetto sintetico e verifica della cifratura a riposo
echo "Rapporto manutenzione sintetico" > rapporto.txt
aws s3 cp rapporto.txt s3://sicurezza02-$SUF/rapporto.txt
aws s3api head-object --bucket sicurezza02-$SUF --key rapporto.txt --region us-east-1 --query '{Encryption:ServerSideEncryption,Size:ContentLength}'

# Step 13 - Download autenticato e confronto del contenuto
aws s3 cp s3://sicurezza02-$SUF/rapporto.txt scaricato.txt
sha256sum rapporto.txt scaricato.txt

# Accesso pubblico bloccato
aws s3api get-public-access-block --bucket sicurezza02-$SUF

# --- Cleanup ---
# (cleanup, commentato)
# aws s3 rm s3://sicurezza02-$SUF --recursive
# aws s3api delete-bucket --bucket sicurezza02-$SUF
# rm -f rapporto.txt scaricato.txt

#==============================================================================
# LABORATORIO 3 - Consegna Lab 03 - Compliance, KMS e identità
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
SUF=riccardogouthier

# Step 1-3 - Trust policy del ruolo del lab (sola lettura, nessuna modifica)
aws iam get-role --role-name LabRole --query Role.AssumeRolePolicyDocument

# Step 4-9 - Chiave KMS customer managed: simmetrica, encrypt and decrypt, alias sicurezza03-SUFFISSO
KEY_ID=$(aws kms create-key --key-spec SYMMETRIC_DEFAULT --key-usage ENCRYPT_DECRYPT --description "sicurezza03-$SUF" --region us-east-1 --query KeyMetadata.KeyId --output text)
aws kms create-alias --alias-name alias/sicurezza03-$SUF --target-key-id $KEY_ID --region us-east-1
echo $KEY_ID

# Step 10-11 - Ciclo encrypt -> decrypt e confronto con l'originale
printf '%s' 'rapporto sintetico 03' > chiaro03.txt
aws kms encrypt --key-id $KEY_ID --plaintext fileb://chiaro03.txt --region us-east-1 --query CiphertextBlob --output text > cifrato03.b64
base64 -d cifrato03.b64 > cifrato03.bin
aws kms decrypt --ciphertext-blob fileb://cifrato03.bin --region us-east-1 --query Plaintext --output text > decifrato03.b64
base64 -d decifrato03.b64 > decifrato03.txt
cmp chiaro03.txt decifrato03.txt; echo "exit=$?"      # exit=0: nessuna differenza

# --- Cleanup (Step 13-14) ---
# (cleanup, commentato)
# aws kms delete-alias --alias-name alias/sicurezza03-$SUF --region us-east-1
# aws kms schedule-key-deletion --key-id $KEY_ID --pending-window-in-days 7 --region us-east-1
# aws kms describe-key --key-id $KEY_ID --region us-east-1 --query 'KeyMetadata.[KeyState,DeletionDate]' --output text
# rm chiaro03.txt cifrato03.b64 cifrato03.bin decifrato03.b64 decifrato03.txt
# ls

#==============================================================================
# LABORATORIO 4 - Deliverable Lab 04 - IAM: buone pratiche, MFA e policy JSON
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1

# Policy base (punto 1)
cat > policy04.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "AllowReadReports", "Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::didattica-esempio/report/*"},
    {"Sid": "DenyDeleteObjects", "Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "arn:aws:s3:::didattica-esempio/*"}
  ]
}
EOF

# Policy MFA (punto 3)
cat > policy04_mfa.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "AllowReadReports", "Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::didattica-esempio/report/*"},
    {"Sid": "DenyDeleteObjects", "Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "arn:aws:s3:::didattica-esempio/*"},
    {"Sid": "DenyReadReportsWithoutMFA", "Effect": "Deny", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::didattica-esempio/report/*",
     "Condition": {"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}}}
  ]
}
EOF

# Casi base 1-4
sim() { aws iam simulate-custom-policy --policy-input-list file://$1 --action-names $2 --resource-arns $3 "${@:4}" --query 'EvaluationResults[].[EvalActionName,EvalResourceName,EvalDecision]' --output text; }
sim policy04.json s3:GetObject    arn:aws:s3:::didattica-esempio/report/a.txt     # allowed
sim policy04.json s3:DeleteObject arn:aws:s3:::didattica-esempio/report/a.txt     # explicitDeny
sim policy04.json s3:GetObject    arn:aws:s3:::didattica-esempio/privato/a.txt    # implicitDeny
sim policy04.json s3:ListBucket   arn:aws:s3:::didattica-esempio                  # implicitDeny

# Casi MFA 5-7 (chiave MFA nel contesto della simulazione)
sim policy04_mfa.json s3:GetObject arn:aws:s3:::didattica-esempio/report/a.txt --context-entries ContextKeyName=aws:MultiFactorAuthPresent,ContextKeyValues=true,ContextKeyType=boolean    # allowed
sim policy04_mfa.json s3:GetObject arn:aws:s3:::didattica-esempio/report/a.txt --context-entries ContextKeyName=aws:MultiFactorAuthPresent,ContextKeyValues=false,ContextKeyType=boolean   # explicitDeny
sim policy04_mfa.json s3:GetObject arn:aws:s3:::didattica-esempio/report/a.txt                                                                                                         # chiave omessa: explicitDeny

#==============================================================================
# LABORATORIO 5 - Consegna Lab 05 - SCP e Access Analyzer (modello locale)
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1

# Policy IAM del ruolo applicativo: Get e Delete su rapporti-demo
cat > iam-ruolo.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObject","s3:DeleteObject"],"Resource":"arn:aws:s3:::rapporti-demo/*"}]}
EOF

# SCP della OU Produzione (letta, non distribuita)
cat > scp-ou.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"s3:DeleteObject","Resource":"*"}]}
EOF

sim() { aws iam simulate-custom-policy --policy-input-list "$@" --action-names s3:GetObject s3:DeleteObject s3:PutObject --resource-arns arn:aws:s3:::rapporti-demo/a.txt --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output table; }

echo "== Con SCP Deny attiva =="    ; sim file://iam-ruolo.json file://scp-ou.json   # Get allowed, Delete explicitDeny, Put implicitDeny
echo "== Senza SCP Deny =="         ; sim file://iam-ruolo.json                       # Get allowed, Delete allowed, Put implicitDeny
# Finding A - correzione: partner limitato a export/*
cat > partner-corretta.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:GetObject","Resource":"arn:aws:s3:::rapporti-demo/export/*"}]}
EOF
for K in export/a.txt interno/b.txt; do
  aws iam simulate-custom-policy --policy-input-list file://partner-corretta.json --action-names s3:GetObject --resource-arns arn:aws:s3:::rapporti-demo/$K --query 'EvaluationResults[].[EvalResourceName,EvalDecision]' --output text
done     # export/a.txt allowed (prova positiva), interno/b.txt implicitDeny (prova negativa)

#==============================================================================
# LABORATORIO 6 - Consegna Lab 06 - VPC, Security Group e Network ACL
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
SUF=rg

# Steps 1-6 - VPC sicurezza06-SUFFISSO (10.60.0.0/16)
VPC=$(aws ec2 create-vpc --cidr-block 10.60.0.0/16 --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=sicurezza06-$SUF}]" --query Vpc.VpcId --output text)
aws ec2 wait vpc-available --vpc-ids $VPC

# Steps 7-11 - Subnet 10.60.1.0/24 in una AZ, senza IPv4 pubblico automatico
SUB=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.60.1.0/24 --availability-zone us-east-1a --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=sicurezza06-$SUF}]" --query Subnet.SubnetId --output text)
aws ec2 modify-subnet-attribute --subnet-id $SUB --no-map-public-ip-on-launch

# Steps 12-15 - Security Group: inbound HTTPS 443 da 10.20.1.0/24, outbound generale rimosso
SG=$(aws ec2 create-security-group --group-name sicurezza06-$SUF --description "lab sicurezza06" --vpc-id $VPC --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port 443 --cidr 10.20.1.0/24
aws ec2 revoke-security-group-egress --group-id $SG --ip-permissions 'IpProtocol=-1,IpRanges=[{CidrIp=0.0.0.0/0}]'

# Steps 16-19 - Network ACL: inbound 100 TCP 443 da 10.20.1.0/24 Allow; outbound 100 TCP 1024-65535 verso 10.20.1.0/24 Allow
NACL=$(aws ec2 create-network-acl --vpc-id $VPC --tag-specifications "ResourceType=network-acl,Tags=[{Key=Name,Value=sicurezza06-$SUF}]" --query NetworkAcl.NetworkAclId --output text)
aws ec2 create-network-acl-entry --network-acl-id $NACL --ingress --rule-number 100 --protocol 6 --port-range From=443,To=443 --cidr-block 10.20.1.0/24 --rule-action allow
aws ec2 create-network-acl-entry --network-acl-id $NACL --egress  --rule-number 100 --protocol 6 --port-range From=1024,To=65535 --cidr-block 10.20.1.0/24 --rule-action allow

# Steps 20-21 - Associare la ACL solo alla subnet del lab, annotando quella precedente
OLD_ASSOC=$(aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=$SUB --query "NetworkAcls[0].Associations[?SubnetId=='$SUB'].NetworkAclAssociationId" --output text)
OLD_NACL=$(aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=$SUB --query "NetworkAcls[0].NetworkAclId" --output text)
NEW_ASSOC=$(aws ec2 replace-network-acl-association --association-id $OLD_ASSOC --network-acl-id $NACL --query NewAssociationId --output text)
echo "VPC=$VPC SUB=$SUB SG=$SG NACL=$NACL OLD_NACL=$OLD_NACL NEW_ASSOC=$NEW_ASSOC"

# Verifica regole
aws ec2 describe-security-groups --group-ids $SG --query "SecurityGroups[0].[IpPermissions,IpPermissionsEgress]" --output json
aws ec2 describe-network-acls --network-acl-ids $NACL --query "NetworkAcls[0].Entries[?RuleNumber!=\`32767\`].[RuleNumber,Egress,Protocol,PortRange,CidrBlock,RuleAction]" --output json

# --- Cleanup ---
# (cleanup, commentato)
# aws ec2 replace-network-acl-association --association-id $NEW_ASSOC --network-acl-id $OLD_NACL   # ripristina la ACL precedente
# aws ec2 delete-network-acl --network-acl-id $NACL
# aws ec2 delete-security-group --group-id $SG
# aws ec2 delete-subnet --subnet-id $SUB
# aws ec2 delete-vpc --vpc-id $VPC
# aws ec2 describe-vpcs --query "Vpcs[].[VpcId,IsDefault]" --output table      # deve restare solo la VPC di default

#==============================================================================
# LABORATORIO 7 - Consegna Lab 07 - Connettivita sicura e CloudTrail
#==============================================================================
cd "$HOME"
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

# --- Cleanup ---
# (cleanup, commentato)
# aws logs delete-log-group --log-group-name /sicurezza07/$SUF --region us-east-1
# aws logs describe-log-groups --log-group-name-prefix /sicurezza07 --query "logGroups[].logGroupName"   # atteso: vuoto

#==============================================================================
# LABORATORIO 8 - Consegna Lab 08 - CloudWatch e AWS Config
#==============================================================================
cd "$HOME"
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

# --- Cleanup ---
# (cleanup, commentato)
# aws cloudwatch delete-alarms --alarm-names sicurezza08-$SUF --region us-east-1
# aws cloudwatch describe-alarms --alarm-names sicurezza08-$SUF --query "MetricAlarms" --output text    # atteso: vuoto

#==============================================================================
# LABORATORIO 9 - Consegna Lab 09 - AWS WAF e Secrets Manager
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
SUF=rg

# ---------- WAF ----------
# Steps 1-13 - Web ACL regionale sicurezza09-SUFFISSO: default Allow, regola osserva-admin (URI path starts with /admin, NONE, Count, priority 0)
cat > rules.json <<'EOF'
[
  {
    "Name": "osserva-admin",
    "Priority": 0,
    "Statement": {
      "ByteMatchStatement": {
        "SearchString": "/admin",
        "FieldToMatch": {"UriPath": {}},
        "TextTransformations": [{"Priority": 0, "Type": "NONE"}],
        "PositionalConstraint": "STARTS_WITH"
      }
    },
    "Action": {"Count": {}},
    "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "osserva-admin"}
  }
]
EOF
aws wafv2 create-web-acl --name sicurezza09-$SUF --scope REGIONAL --region us-east-1 \
  --default-action Allow={} --rules file://rules.json \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=sicurezza09-$SUF
aws wafv2 list-web-acls --scope REGIONAL --region us-east-1 --query "WebACLs[].[Name,Id]" --output table

# Nessuna risorsa associata (associazioni: 0): la Web ACL non protegge traffico reale
WACL_ID=$(aws wafv2 list-web-acls --scope REGIONAL --region us-east-1 --query "WebACLs[?Name=='sicurezza09-$SUF'].Id" --output text)
aws wafv2 list-resources-for-web-acl --web-acl-arn $(aws wafv2 get-web-acl --name sicurezza09-$SUF --scope REGIONAL --id $WACL_ID --region us-east-1 --query WebACL.ARN --output text) --resource-type APPLICATION_LOAD_BALANCER --region us-east-1

# ---------- Secrets Manager ----------
# Steps 14-21 - Segreto sicurezza09/SUFFISSO (chiave aws/secretsmanager, nessuna rotazione/replica), valore v1
aws secretsmanager create-secret --name sicurezza09/$SUF --secret-string '{"password":"DEMO-NON-VALIDO-v1"}' --region us-east-1
# Steps 22-23 - Aggiornare a v2
aws secretsmanager put-secret-value --secret-id sicurezza09/$SUF --secret-string '{"password":"DEMO-NON-VALIDO-v2"}' --region us-east-1
# Step 24 - Versioni: la v2 e AWSCURRENT, la v1 e AWSPREVIOUS
aws secretsmanager list-secret-version-ids --secret-id sicurezza09/$SUF --region us-east-1 --query "Versions[].[VersionId,VersionStages]" --output json

# --- Cleanup ---
# (cleanup, commentato)
# LOCK=$(aws wafv2 get-web-acl --name sicurezza09-$SUF --scope REGIONAL --id $WACL_ID --region us-east-1 --query LockToken --output text)
# aws wafv2 delete-web-acl --name sicurezza09-$SUF --scope REGIONAL --id $WACL_ID --lock-token $LOCK --region us-east-1
# aws secretsmanager delete-secret --secret-id sicurezza09/$SUF --recovery-window-in-days 7 --region us-east-1     # eliminazione pianificata, non forzata
# aws secretsmanager describe-secret --secret-id sicurezza09/$SUF --region us-east-1 --query DeletedDate
# rm rules.json

#==============================================================================
# LABORATORIO 10 - Consegna Lab 10 - GuardDuty, Inspector e risposta ai finding
#==============================================================================
cd "$HOME"
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
aws inspector2 batch-get-account-status --region us-east-1 2>&1 | head -20      # se Inspector non e attivo / accesso negato: registrare l'errore, non modificare IAM

# --- Cleanup finale (Lab 6-10) ---
# (cleanup, commentato)
# # Elimina il detector solo se creato personalmente in questo lab
# [ "$CREATO_DA_ME" = 1 ] && aws guardduty delete-detector --detector-id $DETECTOR_ID --region us-east-1
# aws guardduty list-detectors --region us-east-1                                  # atteso: lista vuota
#
# # Verifiche sulle altre risorse dei Lab 06-09 (rimosse con i rispettivi cleanup)
# aws ec2 describe-vpcs --query "Vpcs[].[VpcId,IsDefault]" --output table          # solo la VPC di default
# aws wafv2 list-web-acls --scope REGIONAL --region us-east-1 --query "WebACLs[].Name"
# aws cloudwatch describe-alarms --alarm-name-prefix sicurezza08 --query "MetricAlarms[].AlarmName"
# aws logs describe-log-groups --log-group-name-prefix /sicurezza07 --query "logGroups[].logGroupName"
# aws secretsmanager describe-secret --secret-id sicurezza09/rg --query "[Name,DeletedDate]"      # in eliminazione pianificata (7 giorni)
