# Deliverable Lab 10 - EBS vs EFS: storage condiviso tra istanze

## Confronto
| Servizio | Modello | Condivisione |
|---|---|---|
| EBS | blocchi, una istanza, stessa AZ | no: ogni istanza ha il proprio volume |
| EFS | file system NFS | sì: stesso file system montato da più istanze/AZ |

## Configurazione
Regione `us-east-1`.

### Istanze
| Istanza | AZ | Instance ID | Volume EBS dedicato |
|---|---|---|---|
| `demo-web-01` | `us-east-1a` | `i-09d43125add0a6e50` | `demo-data-vol` |
| `demo-web-02` | `us-east-1b` | `i-0f91ef84fffb17150` | `demo-data-vol-02` |

- Amazon Linux 2023, `t3.micro`, stessa VPC `demo-vpc` (`10.0.0.0/16`, DNS resolution e hostnames abilitati), indipendenti da qualsiasi ASG
- Volumi `gp3` da 10 GiB, formattati `xfs` (nel Lab 07 il volume dati era `ext4`: qui sono volumi nuovi e la scelta del file system non cambia il risultato del lab) e montati su `/mnt/demo-data` (`df`: `/dev/nvme1n1` 10G su entrambe)

### EFS
- File system `demo-efs-shared` (`fs-0c416404a678a550e`), General Purpose, Regional
- Security Group `demo-sg-efs`: NFS TCP 2049 solo dal Security Group delle istanze (`demo-sg-instances`)
- Mount target `available`: `us-east-1a` (`10.0.1.240`) e `us-east-1b` (`10.0.4.227`), con `demo-sg-efs` associato (verificabile con `describe-mount-targets` e `describe-mount-target-security-groups`)

## Mount (via SSM)
```bash
sudo mount -t efs -o tls fs-0c416404a678a550e:/ /mnt/efs-shared
findmnt --mountpoint /mnt/efs-shared
```
`findmnt` conferma il file system `nfs4` montato su entrambe le istanze.

## Prova di condivisione
```bash
# su demo-web-01
echo 'scritto dalla istanza 1' | sudo tee /mnt/efs-shared/condiviso.txt
# su demo-web-02
cat /mnt/efs-shared/condiviso.txt
```
Su `demo-web-02` il file contiene esattamente `scritto dalla istanza 1`, senza copia manuale.

I volumi EBS restano separati: `/mnt/demo-data` di `demo-web-02` è vuoto e non contiene i dati di `demo-web-01`.

## Motivazione scelte
- SG EFS con origine il SG delle istanze: solo le istanze del lab raggiungono la porta 2049
- Un mount target per AZ: le istanze montano il file system dalla propria AZ
- Montaggio con `tls`: traffico NFS cifrato in transito

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | Istanze | `demo-web-01` (1a), `demo-web-02` (1b), stessa VPC |
| 2 | EBS | volumi separati, `/mnt/demo-data` diverso su ciascuna |
| 3 | EFS | `fs-0c416404a678a550e`, 2 mount target `available` |
| 4 | Condivisione | file scritto su istanza 1 letto su istanza 2 |

## Checkpoint
- [x] EBS separato per istanza, dati non condivisi
- [x] EFS con SG dedicato e mount target in due AZ
- [x] Mount eseguito su entrambe le istanze
- [x] File condiviso letto dall'altra istanza
- [x] Cleanup descritto in questo documento (sezione Cleanup)

## Cleanup
Si eliminano nell'ordine: smontaggio, mount target (attendere la cancellazione), file system EFS, Security Group `demo-sg-efs` e `demo-sg-instances`, volumi, istanze. I comandi sono in fondo (sezione "Cleanup").

## Nota metodologica
ID di istanze, file system e IP dei mount target sono quelli dell'infrastruttura creata con la procedura qui sotto.

Procedura di esecuzione in CLI Cloudshell:

Prerequisito: `demo-vpc` (`10.0.0.0/16`) con `demo-subnet-public-1a` (`10.0.1.0/24`, us-east-1a) e `demo-rt-public` dei Lab 04-05.

```bash
export AWS_DEFAULT_REGION=us-east-1
VPC=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=demo-vpc --query "Vpcs[0].VpcId" --output text)
SUB_A=$(aws ec2 describe-subnets --filters Name=tag:Name,Values=demo-subnet-public-1a --query "Subnets[0].SubnetId" --output text)
RT_PUB=$(aws ec2 describe-route-tables --filters Name=tag:Name,Values=demo-rt-public --query "RouteTables[0].RouteTableId" --output text)

# Step 3 (parte DNS) - DNS resolution e DNS hostnames abilitati
aws ec2 modify-vpc-attribute --vpc-id $VPC --enable-dns-support '{"Value":true}'
aws ec2 modify-vpc-attribute --vpc-id $VPC --enable-dns-hostnames '{"Value":true}'

# Step 1 - Seconda subnet pubblica in us-east-1b e due istanze Amazon Linux 2023 (indipendenti da ASG)
SUB_B=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.0.4.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=demo-subnet-public-1b}]' --query Subnet.SubnetId --output text)
aws ec2 modify-subnet-attribute --subnet-id $SUB_B --map-public-ip-on-launch
aws ec2 associate-route-table --route-table-id $RT_PUB --subnet-id $SUB_B
aws ec2 modify-subnet-attribute --subnet-id $SUB_A --map-public-ip-on-launch

SG_I=$(aws ec2 create-security-group --group-name demo-sg-instances --description "demo istanze applicative" --vpc-id $VPC --query GroupId --output text)
BASE_AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text)
mk() { aws ec2 run-instances --image-id $BASE_AMI --instance-type t3.micro --subnet-id $2 --security-group-ids $SG_I --iam-instance-profile Name=LabInstanceProfile --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$1}]" --query "Instances[0].InstanceId" --output text; }
ID1=$(mk demo-web-01 $SUB_A)
ID2=$(mk demo-web-02 $SUB_B)
aws ec2 wait instance-status-ok --instance-ids $ID1 $ID2
echo $ID1 $ID2

# Step 2 - Volumi EBS dedicati gp3 10 GiB, uno per istanza, nella rispettiva AZ
V1=$(aws ec2 create-volume --availability-zone us-east-1a --volume-type gp3 --size 10 --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=demo-data-vol}]' --query VolumeId --output text)
V2=$(aws ec2 create-volume --availability-zone us-east-1b --volume-type gp3 --size 10 --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=demo-data-vol-02}]' --query VolumeId --output text)
aws ec2 wait volume-available --volume-ids $V1 $V2
aws ec2 attach-volume --volume-id $V1 --instance-id $ID1 --device /dev/sdf
aws ec2 attach-volume --volume-id $V2 --instance-id $ID2 --device /dev/sdf
aws ec2 wait volume-in-use --volume-ids $V1 $V2

# Formattazione xfs e mount su /mnt/demo-data (via SSM, nessuna chiave SSH necessaria)
# Su t3 (Nitro) il volume allegato come /dev/sdf è /dev/nvme1n1; il root è nvme0n1. Si controlla prima con lsblk e si formatta solo se il disco è vuoto.
DATA_CMDS='["lsblk","sudo blkid /dev/nvme1n1 || sudo mkfs -t xfs /dev/nvme1n1","sudo mkdir -p /mnt/demo-data","sudo mount /dev/nvme1n1 /mnt/demo-data","df -h /mnt/demo-data"]'
for I in $ID1 $ID2; do
  CID=$(aws ssm send-command --instance-ids $I --document-name AWS-RunShellScript --parameters "commands=$DATA_CMDS" --query Command.CommandId --output text)
  aws ssm wait command-executed --command-id $CID --instance-id $I     # si attende la fine, altrimenti lo step 7 parte prima del mount
  aws ssm get-command-invocation --command-id $CID --instance-id $I --query "[InstanceId,Status]" --output text
done

# Step 3 - Security Group EFS: NFS 2049 solo dal SG delle istanze
SG_E=$(aws ec2 create-security-group --group-name demo-sg-efs --description "demo EFS" --vpc-id $VPC --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_E --protocol tcp --port 2049 --source-group $SG_I

# Step 4 - File system EFS Regional, General Purpose
EFS=$(aws efs create-file-system --performance-mode generalPurpose --tags Key=Name,Value=demo-efs-shared --query FileSystemId --output text)
until [ "$(aws efs describe-file-systems --file-system-id $EFS --query 'FileSystems[0].LifeCycleState' --output text)" = available ]; do sleep 5; done
echo $EFS

# Step 5 - Mount target nelle due AZ con demo-sg-efs
aws efs create-mount-target --file-system-id $EFS --subnet-id $SUB_A --security-groups $SG_E
aws efs create-mount-target --file-system-id $EFS --subnet-id $SUB_B --security-groups $SG_E
until [ "$(aws efs describe-mount-targets --file-system-id $EFS --query 'length(MountTargets[?LifeCycleState==`available`])' --output text)" = 2 ]; do sleep 10; done
aws efs describe-mount-targets --file-system-id $EFS --query "MountTargets[].[AvailabilityZoneName,IpAddress,LifeCycleState]" --output table

# Step 6 - Mount EFS su entrambe le istanze (via SSM)
# Si usa l'opzione az=: il mount helper risolve il nome DNS di zona (us-east-1a.fs-...). Il nome generico fs-....efs.us-east-1.amazonaws.com
# nel nostro test non si risolveva ("Failed to resolve") anche con il mount target già available.
# Anche il nome di zona compare nel DNS della VPC con qualche minuto di ritardo rispetto allo stato available: il mount si ritenta ogni 15 s con until.
for P in "$ID1 us-east-1a" "$ID2 us-east-1b"; do
  set -- $P
  MNT="[\"sudo dnf install -y amazon-efs-utils\",\"sudo mkdir -p /mnt/efs-shared\",\"until sudo mount -t efs -o tls,az=$2 $EFS:/ /mnt/efs-shared; do sleep 15; done\",\"findmnt --mountpoint /mnt/efs-shared\"]"
  CID=$(aws ssm send-command --instance-ids $1 --document-name AWS-RunShellScript --parameters "commands=$MNT" --query Command.CommandId --output text)
  aws ssm wait command-executed --command-id $CID --instance-id $1
  aws ssm get-command-invocation --command-id $CID --instance-id $1 --query "[InstanceId,Status]" --output text
done

# Step 7 - Prova di condivisione: scrive su web-01, legge su web-02
run() { CID=$(aws ssm send-command --instance-ids $1 --document-name AWS-RunShellScript --parameters "commands=[\"$2\"]" --query Command.CommandId --output text); aws ssm wait command-executed --command-id $CID --instance-id $1; aws ssm get-command-invocation --command-id $CID --instance-id $1 --query StandardOutputContent --output text; }
run $ID1 "findmnt --mountpoint /mnt/efs-shared && echo 'scritto dalla istanza 1' | sudo tee /mnt/efs-shared/condiviso.txt"
run $ID2 "findmnt --mountpoint /mnt/efs-shared && cat /mnt/efs-shared/condiviso.txt"

# Step 8 - Contrasto: i volumi EBS restano separati (su web-02 /mnt/demo-data non contiene i dati di web-01)
run $ID2 "ls -la /mnt/demo-data"
```

Output atteso allo Step 7: su `demo-web-02` compare `scritto dalla istanza 1` senza copia manuale. 
### Cleanup

```bash
aws ssm send-command --instance-ids $ID1 $ID2 --document-name AWS-RunShellScript --parameters 'commands=["sudo umount /mnt/efs-shared","sudo umount /mnt/demo-data"]'
for MT in $(aws efs describe-mount-targets --file-system-id $EFS --query "MountTargets[].MountTargetId" --output text); do aws efs delete-mount-target --mount-target-id $MT; done
until [ "$(aws efs describe-mount-targets --file-system-id $EFS --query 'length(MountTargets)' --output text)" = 0 ]; do sleep 10; done
aws efs delete-file-system --file-system-id $EFS
aws ec2 terminate-instances --instance-ids $ID1 $ID2 && aws ec2 wait instance-terminated --instance-ids $ID1 $ID2
aws ec2 delete-volume --volume-id $V1; aws ec2 delete-volume --volume-id $V2
aws ec2 delete-security-group --group-id $SG_E
aws ec2 delete-security-group --group-id $SG_I
# La subnet demo-subnet-public-1b è creata da questo lab: si elimina qui, dopo averla dissociata dalla route table pubblica
# (altrimenti il cleanup del Lab 05 trova due associazioni su demo-rt-public e `disassociate-route-table` fallisce)
ASSOC_B=$(aws ec2 describe-route-tables --route-table-ids $RT_PUB --query "RouteTables[0].Associations[?SubnetId=='$SUB_B'].RouteTableAssociationId" --output text)
aws ec2 disassociate-route-table --association-id $ASSOC_B
aws ec2 delete-subnet --subnet-id $SUB_B
```
