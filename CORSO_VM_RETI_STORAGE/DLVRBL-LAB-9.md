# Deliverable Lab 09 - Storage Gateway e cifratura a riposo

## Storage Gateway (solo esame dei tipi, nessun gateway creato)
| Tipo | Interfaccia esposta | Caso d'uso |
|---|---|---|
| S3 File Gateway | NFS / SMB | condivisione di file da server on-premises |
| Volume Gateway | iSCSI | dischi a blocchi |
| Tape Gateway | nastri virtuali | applicazione di backup con nastri virtuali |

La scelta si fa in base all'interfaccia richiesta dall'applicazione.

## Configurazione
### Volume EBS cifrato (Terraform)
- Nome `demo-encrypted-vol`, `gp3`, 10 GiB, `us-east-1a`
- `Encrypted = Yes`, chiave `aws/ebs` (KMS key id `ac8cde50-ebef-427c-839c-507c08c27833`)
- Stato `available`

### Bucket S3
- Bucket `demo-vm-reti-storage-rg-2026`, Default encryption = SSE-S3 (`AES256`) a livello di bucket
- Oggetto di prova: `test-cifratura.txt`

## Verifica (CLI)
```bash
aws ec2 describe-volumes --volume-ids <vol-id> --query "Volumes[].Encrypted"
aws s3api head-object --bucket demo-vm-reti-storage-rg-2026 --key test-cifratura.txt
aws s3api get-bucket-encryption --bucket demo-vm-reti-storage-rg-2026
```
Esito: `describe-volumes` -> `Encrypted: true`; `head-object` -> `ServerSideEncryption: AES256`; `get-bucket-encryption` -> `SSEAlgorithm: AES256`.

## Motivazione scelte
- Cifratura gestita (`aws/ebs`, SSE-S3): attiva senza modificare le applicazioni
- Default encryption sul bucket: ogni nuovo oggetto risulta cifrato

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | Volume | `demo-encrypted-vol`, `gp3`, 10 GiB, `Encrypted` true |
| 2 | Bucket | SSE-S3 `AES256` di default |
| 3 | Oggetto | `test-cifratura.txt` cifrato (`head-object`: `AES256`) |

## Limite
La cifratura a riposo e verificata su volume e oggetto. HTTPS protegge il trasferimento ed e una cosa distinta, non provata da queste verifiche.

## Checkpoint
- [x] Tipi di Storage Gateway confrontati e scelta motivata
- [x] Volume EBS cifrato verificato via CLI
- [x] Cifratura di bucket e oggetto verificata
- [x] Cifratura a riposo distinta dal trasferimento
- [x] Cleanup eseguito (vedi sotto)

## Cleanup
Volume e bucket rimossi a fine percorso (cleanup finale Lab 8-11, nel Lab 11).

## Nota metodologica
`<vol-id>` da sostituire con l'ID osservato del volume. Nessun Storage Gateway creato.

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
BUCKET=demo-vm-reti-storage-rg-2026      # bucket del Lab 08

# Steps 1-2 - Storage Gateway: solo esame dei tipi (nessun gateway creato).
# S3 File Gateway = NFS/SMB | Volume Gateway = iSCSI | Tape Gateway = nastri virtuali (app di backup)

# Step 3 - Volume EBS cifrato gp3 10 GiB in us-east-1a, chiave aws/ebs
VOL=$(aws ec2 create-volume --availability-zone us-east-1a --volume-type gp3 --size 10 --encrypted \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=demo-encrypted-vol}]' \
  --query VolumeId --output text)
aws ec2 wait volume-available --volume-ids $VOL
aws ec2 describe-volumes --volume-ids $VOL --query "Volumes[].{Encrypted:Encrypted,KmsKeyId:KmsKeyId,State:State,Size:Size,Type:VolumeType}"

# Steps 4-5 - Bucket del Lab 08: cifratura di default SSE-S3 (AES256)
aws s3api put-bucket-encryption --bucket $BUCKET --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api get-bucket-encryption --bucket $BUCKET

# Step 6 - Oggetto di prova e verifica della cifratura
echo "prova di cifratura a riposo" > test-cifratura.txt
aws s3api put-object --bucket $BUCKET --key test-cifratura.txt --body test-cifratura.txt
aws s3api head-object --bucket $BUCKET --key test-cifratura.txt --query ServerSideEncryption
```

Output atteso: `Encrypted: true` con KMS key `aws/ebs`, `SSEAlgorithm: AES256`, `ServerSideEncryption: "AES256"`. La verifica riguarda la cifratura a riposo; HTTPS (trasferimento) e un controllo distinto.

### Cleanup (se il volume non serve piu)

```bash
aws ec2 delete-volume --volume-id $VOL
aws s3api delete-object --bucket $BUCKET --key test-cifratura.txt
```

Il bucket resta fino al cleanup finale (procedura del Lab 11).
