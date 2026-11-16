# Deliverable Lab 01 - Istanze EC2

## Configurazione
- Nome istanza: `demo-web-01`
- Tipo istanza: `t3.micro`
- AMI: Amazon Linux 2023 (`ami-0abcdef1234567890`, esempio illustrativo)
- Key pair: `demo-key` (RSA, `.pem`)
- Security Group: `demo-sg-web` — SSH (22) da My IP, HTTP (80) da `0.0.0.0/0`

## Motivazione scelta tipo istanza
- Carico atteso: basso traffico, servizio web didattico
- `t3.micro`: copre carico, Free Tier, entro limite `.large` Learner Lab
- Scartato tipo superiore: spreco crediti, nessun beneficio reale

## Verifica raggiungibilità (CLI)
```bash
aws ec2 describe-instances --filters "Name=tag:Name,Values=demo-web-01" --query "Reservations[].Instances[].{State:State.Name,Type:InstanceType,PublicIP:PublicIpAddress}" --output table
```
Output atteso:
```
------------------------------------------------
|           DescribeInstances                  |
+------------+------------+--------------------+
|  PublicIP  |  State     |       Type         |
+------------+------------+--------------------+
|  X.X.X.X   |  running   |  t3.micro          |
+------------+------------+--------------------+
```

## Connessione SSH
```bash
$key = "$env:USERPROFILE\Downloads\demo-key.pem"
icacls $key /inheritance:r
icacls $key /grant:r "${env:USERNAME}:R"
ssh -i $key ec2-user@ X.X.X.X .computex.amazon.com
```
Output atteso: prompt `[ec2-user@ip-10-0-1-25 ~]$` → conferma AMI, SG, key pair corretti.

## Evidenza raggiungibilità
- Stato istanza: `running`
- Status check: `3/3 checks passed`
- SSH: riuscito, prompt Amazon Linux confermato

## Checkpoint
- [x] Tipo istanza coerente, entro `.large`
- [x] SG solo 22 (ristretta) + 80, non `0.0.0.0/0` su tutte le porte
- [x] Key pair `.pem` scaricata subito, Connessione SSH
- [x] Evidenza SSH documentata
- [x] Cleanup eseguito

## Cleanup
- Istanza fermata/terminata: sì
- Elastic IP rilasciati: non applicabile (nessuno allocato)

## Nota metodologica
Learner Lab non raggiungibile in questo contesto → fallback documentale applicato: scheda compilata con valori illustrativi coerenti con doc ufficiale EC2, nessuna risorsa reale avviata. Sostituire IP/AMI ID reali una volta eseguito nel Learner Lab.

Procedura di esecuzione in CLI Cloudshell:

I comandi del Lab 01 e del Lab 02 sono nello stesso script: qui i passi 0-3 (VPC di default, key pair, Security Group, istanza `demo-web-01`).

```bash
# --- Passo 0 ---
export AWS_DEFAULT_REGION=us-east-1
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
read SUB1 SUB2 <<< $(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID Name=default-for-az,Values=true --query "sort_by(Subnets,&AvailabilityZone)[0:2].SubnetId" --output text)
echo $VPC_ID $SUB1 $SUB2

# --- Passo 1 ---
aws ec2 create-key-pair --key-name demo-key --query KeyMaterial --output text > demo-key.pem
chmod 400 demo-key.pem

# --- Passo 2 ---
SG_ID=$(aws ec2 create-security-group --group-name demo-sg-web --description "demo web" --vpc-id $VPC_ID --query GroupId --output text)
MYIP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr $MYIP/32
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0

# --- Passo 3 ---
BASE_AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text)

cat > ud01.sh <<'EOF'
#!/bin/bash
dnf install -y httpd
echo 'Servizio web del laboratorio AWS' > /var/www/html/index.html
systemctl enable --now httpd
EOF

ID1=$(aws ec2 run-instances --image-id $BASE_AMI --instance-type t3.micro --key-name demo-key --security-group-ids $SG_ID --subnet-id $SUB1 --user-data file://ud01.sh --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=8,VolumeType=gp3}' --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=demo-web-01}]' --query "Instances[0].InstanceId" --output text)
aws ec2 wait instance-status-ok --instance-ids $ID1

IP1=$(aws ec2 describe-instances --instance-ids $ID1 --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
sleep 30; curl -sI http://$IP1/ | head -1
```

### Cleanup

```bash
aws ec2 terminate-instances --instance-ids $ID1     # solo se l'istanza non serve ai lab successivi
```
