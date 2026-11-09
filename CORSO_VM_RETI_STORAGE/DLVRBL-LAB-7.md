# Deliverable Lab 07 - EBS, EFS, S3 e Gestione Volumi EBS

## Confronto modelli di storage
| Servizio | Modello | Caso d'uso |
|---|---|---|
| EBS | storage a blocchi, 1 istanza, stessa AZ | disco dati di un'istanza EC2 |
| EFS | file system condiviso fra più istanze | contenuti condivisi tra istanze/AZ |
| S3 | oggetti via API | archivi, backup |

## Configurazione
- Istanza: `<nome-istanza>`, `<instance-id>`, `<tipo>`, `us-east-1b` — Linux autonoma, nessun ASG; configurazione via CLI da CloudShell
- Volume: `demo-data-vol`, `vol-00ffa43b2c0932658`, `gp3`, 10 GiB, `us-east-1b`
- Device richiesto: `/dev/sdf`; device reale: `<xvdf / nvme1n1>`
- Mount point: `/mnt/demo-data`, file system `ext4`

## Motivazione scelte
- `gp3` 10 GiB: entro limiti Learner Lab (tipi `gp2/gp3/sc1/standard`, max 100 GiB), nessun `io1/io2`
- Stessa AZ dell'istanza (letta con `describe-instances`): requisito di allegamento EBS
- Volume separato dal root: dati distinti dal sistema operativo
- `sync` prima dello snapshot: dati su disco, backup coerente

## Creazione e allegamento (CLI)
```bash
AZ=$(aws ec2 describe-instances --instance-ids $ID --region $R \
  --query "Reservations[0].Instances[0].Placement.AvailabilityZone" --output text)
VOL=$(aws ec2 create-volume --availability-zone $AZ --volume-type gp3 --size 10 \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=demo-data-vol}]' --query VolumeId --output text --region $R)
aws ec2 wait volume-available --volume-ids $VOL --region $R
aws ec2 attach-volume --volume-id $VOL --instance-id $ID --device /dev/sdf --region $R
aws ec2 wait volume-in-use --volume-ids $VOL --region $R
```
Stato verificato: `available` → `in-use`, allegato alla sola istanza del lab.

## Filesystem e prova dati (SSH)
```bash
lsblk -f
LAB_DATA_DEVICE=/dev/xvdf        # adattare al device reale
sudo blkid "$LAB_DATA_DEVICE"    # nessun output = disco vuoto
sudo mkfs -t ext4 "$LAB_DATA_DEVICE"   # solo se vuoto
sudo mkdir -p /mnt/demo-data
sudo mount "$LAB_DATA_DEVICE" /mnt/demo-data
findmnt /mnt/demo-data
echo "demo storage EBS" | sudo tee /mnt/demo-data/test.txt
cat /mnt/demo-data/test.txt
sync
```
Output atteso: `lsblk -f` mostra disco 10G senza FS; `blkid` vuoto; `findmnt` conferma mount; file riletto: `demo storage EBS`. Formattato solo il nuovo disco, mai il root.

## Snapshot e verifica (CLI)
```bash
SNAP=$(aws ec2 create-snapshot --volume-id $VOL --region $R \
  --description "backup volume dati del laboratorio" --query SnapshotId --output text)
aws ec2 wait snapshot-completed --snapshot-ids $SNAP --region $R
aws ec2 describe-volumes --volume-ids $VOL --region $R \
  --query "Volumes[].{State:State,Size:Size,Type:VolumeType,AZ:AvailabilityZone}"
aws ec2 describe-snapshots --snapshot-ids $SNAP --region $R \
  --query "Snapshots[].{State:State,Progress:Progress}"
```
Output atteso:
```
[{"State": "in-use", "Size": 10, "Type": "gp3", "AZ": "us-east-1b"}]
[{"State": "completed", "Progress": "100%"}]
```

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | Volume EBS | `demo-data-vol`, `gp3`, 10 GiB, `us-east-1b` |
| 2 | Device | richiesto `/dev/sdf`, reale `<xvdf / nvme1n1>` |
| 3 | Mount | `/mnt/demo-data`, `ext4`, `findmnt` OK |
| 4 | File di test | `test.txt` scritto e riletto: «demo storage EBS» |
| 5 | Snapshot | `<snapshot-id>`, `completed`, 100% |

## Checkpoint
- [x] Tipo consentito, dimensione ≤ 100 GiB
- [x] Volume nella stessa AZ dell'istanza
- [x] Snapshot `completed` verificato
- [ ] Cleanup eseguito o giustificato

## Cleanup
- Volume e snapshot conservati per verifica docente e Lab 10, 12, 14: sì/no (ID annotati)
- Se eliminati: `sudo umount /mnt/demo-data` → detach → attendere `available` → delete volume → delete snapshot: sì/no
- Cleanup eseguito / non eseguito: `<...>`
- Nessuna risorsa preesistente eliminata

## Nota metodologica
`<instance-id>`, `<snapshot-id>`, device reale: da compilare con valori osservati. Volume ID e AZ da screenshot del PDF di svolgimento.
