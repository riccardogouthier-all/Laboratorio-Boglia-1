# Consegna Lab 11 - Backup e ripristino sicuro

## Stato iniziale (dato reale)
Account Learner Lab, regione `us-east-1`, ruolo `voclabs`. Nessuna istanza necessaria. Come ruolo IAM per Backup e Restore ho usato `LabRole`, già presente nel Learner Lab (nessun ruolo nuovo, `AWSBackupDefaultServiceRole` non creato).

## Volume origine (EBS)
| Campo | Valore |
|---|---|
| Nome (tag Name) | `sicurezza11-rg` |
| ID | `vol-0b6525be00f61679b` |
| Tipo / dimensione | gp3 / 1 GiB |
| Availability Zone | `us-east-1a` |
| Cifratura | abilitata, chiave `aws/ebs` |
| Collegato a istanze | no |
| Stato prima del backup | `available` |

## Backup (AWS Backup)
| Campo | Valore |
|---|---|
| Vault | `sicurezza11-rg` (Vault Lock non attivato) |
| Tipo di backup | on-demand, resource type EBS |
| Risorsa | `vol-0b6525be00f61679b` |
| Ruolo IAM | `LabRole` |
| Conservazione | 1 giorno, nessun cold storage |
| Backup job | `d12dad94-8eb7-431d-acd3-eb0b1354a835` |
| Stato finale | `COMPLETED` |
| Recovery point | `snap-08692aef2fe312c5c` (visibile nel vault) |

## Restore
| Campo | Valore |
|---|---|
| Restore job | `abe6b32e-a6e0-4c48-979b-a8b9bd6234ba` |
| Recovery point | `snap-08692aef2fe312c5c` |
| Tipo | nuovo volume EBS, gp3, 1 GiB |
| Availability Zone | `us-east-1a` (stessa dell'origine) |
| Cifratura | abilitata, coerente con l'origine |
| Ruolo IAM | `LabRole` |
| Stato finale | `COMPLETED` (durata circa 1 minuto) |
| Volume creato | `vol-081e302b5df3d95ae` |

## Confronto dei volumi
| | Origine | Ripristinato |
|---|---|---|
| ID | `vol-0b6525be00f61679b` | `vol-081e302b5df3d95ae` |
| Stato | `available` | `available` |
| Tipo / dimensione | gp3 / 1 GiB | gp3 / 1 GiB |
| Zona | `us-east-1a` | `us-east-1a` |
| Cifratura | sì | sì |

I due ID sono diversi: il restore ha prodotto una risorsa nuova senza toccare l'originale.

## Prova locale di integrità
File di testo `originale11.txt` (contenuto `rapporto sintetico 11`) copiato in `copia11.txt` e poi in `recuperato11.txt`.

```
ede21663ae3f0602cb61f6570edab60b797db6511c7282788814a06634ebe218  originale11.txt
ede21663ae3f0602cb61f6570edab60b797db6511c7282788814a06634ebe218  recuperato11.txt
```
`cmp` non trova differenze.

## Limiti e distinzioni
- L'hash uguale dimostra che il metodo di confronto funziona, non che il volume AWS contenga dati applicativi: sui volumi non c'era nessuna applicazione e non dichiaro recuperato nessun dato.
- "Processo completato" (backup e restore `COMPLETED`) e "servizio funzionante" sono risultati diversi: un restore riuscito non prova che un servizio sopra quel volume funzionerebbe.
- Lo screenshot del dettaglio di cifratura del volume non è stato catturato; la cifratura è documentata nei dati CLI (`Enc: true`, chiave `aws/ebs`) e nel riepilogo del restore.

## Screenshot (cartella `screenshots-sicurezza/lab-11`)
| File | Contenuto |
|---|---|
| `passo-02.jpg` | dettaglio del volume origine `sicurezza11-rg` (gp3, 1 GiB, `available`, `us-east-1a`) |
| `passo-03.jpg` | vault `sicurezza11-rg` con il recovery point `Completed` |
| `passo-04.jpg` | AWS Backup > Jobs > Backup jobs: job `Completed` |
| `passo-05.jpg` | AWS Backup > Jobs > Restore jobs: job `Completed`, volume `vol-081e302b5df3d95ae` |
| `passo-06.jpg` | EC2 > Volumes: i due volumi, entrambi `Available` |
| `log-lab-11.txt` | output CLI salvati durante il lab |

## Cleanup finale
Eliminati, in ordine: recovery point (atteso che sparisse dal vault), volume ripristinato, volume originale, vault vuoto. Non toccate le chiavi gestite da AWS. File locali di prova eliminati.

Verifica via CLI: nessun volume `sicurezza11`, nessuno snapshot, nessun vault `sicurezza11-rg` nell'account. Le risorse sono state create con Terraform (`aws_ebs_volume` + `aws_backup_vault`) e rimosse con `terraform destroy`.

Rimane solo il segreto `sicurezza09/rg` (Lab 09), in eliminazione pianificata con 7 giorni di recupero.

## Checkpoint
- [x] Due ID di volume distinti
- [x] Backup e restore `COMPLETED`
- [x] Nessun dato applicativo dichiarato recuperato
- [x] Processo completato distinto da servizio funzionante
- [x] Cleanup eseguito e verificato

Procedura di esecuzione in CLI (AWS CLI, regione `us-east-1`):

```bash
export AWS_DEFAULT_REGION=us-east-1

# Volume origine: gp3, 1 GiB, cifrato (aws/ebs), tag Name (creato con Terraform)
aws ec2 describe-volumes --filters Name=tag:Name,Values=sicurezza11-rg \
  --query "Volumes[].[VolumeId,State,VolumeType,Size,AvailabilityZone,Encrypted,Attachments]"

# Vault senza Vault Lock
aws backup create-backup-vault --backup-vault-name sicurezza11-rg

# Backup on-demand, conservazione 1 giorno, ruolo LabRole
ROLE=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
aws backup start-backup-job --backup-vault-name sicurezza11-rg \
  --resource-arn arn:aws:ec2:us-east-1:ACCOUNT_ID:volume/VOLUME_ID \
  --iam-role-arn $ROLE --lifecycle DeleteAfterDays=1
aws backup describe-backup-job --backup-job-id BACKUP_JOB_ID --query State   # atteso COMPLETED

# Restore in un nuovo volume nella stessa zona
aws backup start-restore-job --recovery-point-arn RECOVERY_POINT_ARN \
  --iam-role-arn $ROLE \
  --metadata availabilityZone=us-east-1a,volumeType=gp3,encrypted=true,kmsKeyId=KMS_KEY_ARN
aws backup describe-restore-job --restore-job-id RESTORE_JOB_ID --query "[Status,CreatedResourceArn]"

# Confronto dei due volumi
aws ec2 describe-volumes --query "Volumes[].[VolumeId,State,VolumeType,Size,AvailabilityZone,Encrypted]" --output table
```

Prova locale (Git Bash / Ubuntu):

```bash
printf '%s' 'rapporto sintetico 11' > originale11.txt
cp originale11.txt copia11.txt
cp copia11.txt recuperato11.txt
sha256sum originale11.txt recuperato11.txt
cmp originale11.txt recuperato11.txt
```

### Cleanup

```bash
aws backup delete-recovery-point --backup-vault-name sicurezza11-rg --recovery-point-arn RECOVERY_POINT_ARN
aws backup list-recovery-points-by-backup-vault --backup-vault-name sicurezza11-rg   # attendere lista vuota
aws ec2 delete-volume --volume-id RESTORED_VOLUME_ID
aws ec2 delete-volume --volume-id SOURCE_VOLUME_ID
aws backup delete-backup-vault --backup-vault-name sicurezza11-rg

# Verifiche
aws ec2 describe-volumes --query "Volumes[].VolumeId"
aws ec2 describe-snapshots --owner-ids self --query "Snapshots[].SnapshotId"
aws backup list-backup-vaults --query "BackupVaultList[].BackupVaultName"
rm -f originale11.txt copia11.txt recuperato11.txt
```
