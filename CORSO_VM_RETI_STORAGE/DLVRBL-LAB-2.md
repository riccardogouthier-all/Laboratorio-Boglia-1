# Deliverable Lab 02 - Gestione Immagini AMI ed Elastic Load Balancing

## Configurazione
- AMI: `demo-web-ami-v1` (`ami-0abc123demo`, esempio illustrativo), creata da `demo-web-01` fermata
- Istanze: `demo-web-01`, `demo-web-02` (`t3.micro`, key pair `demo-key`, Security Group `demo-sg-web`)
- `demo-web-02`: lanciata dalla stessa AMI, stessa VPC, subnet pubblica in AZ diversa
- Target group: `demo-tg-web` (Instances, HTTP:80, health check path `/`)
- Load balancer: `demo-alb` (Application Load Balancer, Internet-facing, due subnet pubbliche in AZ diverse, `demo-sg-web`)
- Listener: HTTP:80 → Forward to `demo-tg-web`

## Preparazione web server (Amazon Linux 2023)
```bash
sudo dnf install -y httpd
echo 'Servizio web del laboratorio AWS' | sudo tee /var/www/html/index.html
sudo systemctl enable --now httpd
curl -I http://localhost/
```
Output atteso: `HTTP/1.1 200 OK`. `enable` → servizio riparte su istanze create dalla AMI.

## Motivazione scelte
- AMI da istanza `stopped`: evita stato incoerente dei volumi EBS
- Seconda istanza in AZ diversa: resilienza a guasto di singola AZ
- ALB + health check su `/`: esclusione automatica istanze non sane, nessun intervento manuale

## Verifica AMI (CLI)
```bash
aws ec2 describe-images --owners self \
  --filters "Name=name,Values=demo-web-ami-v1" \
  --query "Images[].{Name:Name,State:State,ImageId:ImageId}" --output table
```
Output atteso:
```
+------------------+------------------+------------+
|     ImageId      |      Name        |   State    |
+------------------+------------------+------------+
|  ami-0abc123demo |  demo-web-ami-v1 |  available |
+------------------+------------------+------------+
```

## Verifica health check (CLI)
```bash
aws elbv2 describe-target-health --target-group-arn <arn-demo-tg-web>
```
Prima dello stop:
```
{"Target": {"Id": "i-demoweb01", "Port": 80}, "TargetHealth": {"State": "healthy"}}
{"Target": {"Id": "i-demoweb02", "Port": 80}, "TargetHealth": {"State": "healthy"}}
```
Dopo stop di `demo-web-02`:
```
{"Target": {"Id": "i-demoweb01", "Port": 80}, "TargetHealth": {"State": "healthy"}}
{"Target": {"Id": "i-demoweb02", "Port": 80}, "TargetHealth": {"State": "unused", "Reason": "Target.InvalidState"}}
```

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | AMI | `demo-web-ami-v1`, stato `available`, snapshot associato annotato |
| 2 | Seconda istanza | `demo-web-02`, stessa AMI, AZ diversa, web server risponde |
| 3 | Target group | `demo-tg-web`, HTTP:80, health check `/` |
| 4 | Load balancer | `demo-alb` `active`, DNS name `http://<DNS-ALB>/` risponde |
| 5 | Health check | prima: 2 `healthy`; dopo stop: `demo-web-01` `healthy`, `demo-web-02` `unused`; dopo riavvio: 2 `healthy` |

## Checkpoint
- [x] AMI creata da istanza in stato coerente (`stopped`), nome con versione
- [x] AMI `available` prima del lancio di `demo-web-02`
- [x] Target group mostra stato di salute di entrambe le istanze
- [x] Stop istanza → esclusione automatica, ALB serve via `demo-web-01`
- [ ] Cleanup completo (ALB, target group, istanze, AMI, snapshot): comandi forniti, esecuzione da confermare

## Cleanup
Comandi nella sezione "Cleanup" in fondo; stato da confermare dopo l'esecuzione.
- ALB e target group: eliminati (prima l'ALB, poi si attende la sua cancellazione, poi il target group).
- Istanze: terminate.
- AMI: `deregister-image`, poi eliminazione dello snapshot associato.
- Se si prosegue con il Lab 03: tenere AMI, snapshot, key pair e Security Group (il Lab 03 li riusa) ed eseguire solo il cleanup dell'ALB e del target group se non servono.

## Nota metodologica
Gli ID (AMI, istanze, DNS dell'ALB) sono illustrativi: nella procedura CLI si ricavano dai comandi (`AMI_ID`, `ID2`, `DNS`).

Procedura di esecuzione in CLI Cloudshell:

Passi 4-8 dello script: AMI da `demo-web-01`, seconda istanza, target group, ALB e verifica.

```bash
# Se la sessione CloudShell è nuova, ricostruire le variabili del Lab 01
export AWS_DEFAULT_REGION=us-east-1
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
read SUB1 SUB2 <<< $(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID Name=default-for-az,Values=true --query "sort_by(Subnets,&AvailabilityZone)[0:2].SubnetId" --output text)
SG_ID=$(aws ec2 describe-security-groups --filters Name=group-name,Values=demo-sg-web --query "SecurityGroups[0].GroupId" --output text)
ID1=$(aws ec2 describe-instances --filters Name=tag:Name,Values=demo-web-01 Name=instance-state-name,Values=running,stopped --query "Reservations[0].Instances[0].InstanceId" --output text)

# --- Passo 4 ---
aws ec2 stop-instances --instance-ids $ID1
aws ec2 wait instance-stopped --instance-ids $ID1
AMI_ID=$(aws ec2 create-image --instance-id $ID1 --name demo-web-ami-v1 --description "AL2023 httpd" --query ImageId --output text)
aws ec2 wait image-available --image-ids $AMI_ID
aws ec2 start-instances --instance-ids $ID1
aws ec2 wait instance-running --instance-ids $ID1
echo $AMI_ID

# --- Passo 5 ---
cat > ud02.sh <<'EOF'
#!/bin/bash
hostname > /var/www/html/index.html
EOF

ID2=$(aws ec2 run-instances --image-id $AMI_ID --instance-type t3.micro --key-name demo-key --security-group-ids $SG_ID --subnet-id $SUB2 --user-data file://ud02.sh --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=demo-web-02}]' --query "Instances[0].InstanceId" --output text)
aws ec2 wait instance-status-ok --instance-ids $ID2

# --- Passo 6 ---
TG_ARN=$(aws elbv2 create-target-group --name demo-tg-web --protocol HTTP --port 80 --vpc-id $VPC_ID --target-type instance --health-check-path / --query "TargetGroups[0].TargetGroupArn" --output text)
aws elbv2 register-targets --target-group-arn $TG_ARN --targets Id=$ID1 Id=$ID2

# --- Passo 7 ---
ALB_ARN=$(aws elbv2 create-load-balancer --name demo-alb --type application --scheme internet-facing --subnets $SUB1 $SUB2 --security-groups $SG_ID --query "LoadBalancers[0].LoadBalancerArn" --output text)
aws elbv2 wait load-balancer-available --load-balancer-arns $ALB_ARN
aws elbv2 create-listener --load-balancer-arn $ALB_ARN --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=$TG_ARN

# --- Passo 8 ---
# I target restano "initial" per 1-2 minuti dopo la creazione dell'ALB: si attende lo stato healthy prima di leggere
aws elbv2 wait target-in-service --target-group-arn $TG_ARN
aws elbv2 describe-target-health --target-group-arn $TG_ARN --query "TargetHealthDescriptions[].[Target.Id,TargetHealth.State]" --output table
DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query "LoadBalancers[0].DNSName" --output text)
curl -s http://$DNS/

# --- Passo 9 --- Prova del health check: stop di demo-web-02, lettura dello stato, riavvio
aws ec2 stop-instances --instance-ids $ID2 --query "StoppingInstances[0].CurrentState.Name" --output text
aws ec2 wait instance-stopped --instance-ids $ID2
sleep 30
aws elbv2 describe-target-health --target-group-arn $TG_ARN --query "TargetHealthDescriptions[].[Target.Id,TargetHealth.State,TargetHealth.Reason]" --output table
for i in 1 2 3 4; do curl -s -m 10 http://$DNS/; done     # risponde solo demo-web-01
aws ec2 start-instances --instance-ids $ID2 --query "StartingInstances[0].CurrentState.Name" --output text
aws ec2 wait instance-running --instance-ids $ID2
aws elbv2 wait target-in-service --target-group-arn $TG_ARN
aws elbv2 describe-target-health --target-group-arn $TG_ARN --query "TargetHealthDescriptions[].[Target.Id,TargetHealth.State]" --output table
```

### Cleanup

```bash
# Cleanup a fine percorso (ordine: listener/ALB, target group, istanze, AMI e snapshot, key pair, SG)
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
aws elbv2 wait load-balancers-deleted --load-balancer-arns $ALB_ARN
aws elbv2 delete-target-group --target-group-arn $TG_ARN
aws ec2 terminate-instances --instance-ids $ID1 $ID2
aws ec2 wait instance-terminated --instance-ids $ID1 $ID2
SNAP_ID=$(aws ec2 describe-images --image-ids $AMI_ID --query "Images[0].BlockDeviceMappings[0].Ebs.SnapshotId" --output text)
aws ec2 deregister-image --image-id $AMI_ID
aws ec2 delete-snapshot --snapshot-id $SNAP_ID
# Key pair e Security Group servono anche al Lab 03: eliminarli solo a fine percorso
# aws ec2 delete-key-pair --key-name demo-key
# aws ec2 delete-security-group --group-id $SG_ID
```
