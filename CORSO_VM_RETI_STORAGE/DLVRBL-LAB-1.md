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
Da CloudShell o da Linux/macOS (sostituire `IP_PUBBLICO` con l'IP letto dal comando precedente):

```bash
chmod 400 demo-key.pem
ssh -i demo-key.pem ec2-user@IP_PUBBLICO
```

Da Windows PowerShell, prima si restringono i permessi del file `.pem`:

```powershell
$key = "$env:USERPROFILE\Downloads\demo-key.pem"
icacls $key /inheritance:r
icacls $key /grant:r "${env:USERNAME}:R"
ssh -i $key ec2-user@IP_PUBBLICO
```

Output atteso: prompt `[ec2-user@ip-10-0-1-25 ~]$`, che conferma AMI, Security Group e key pair corretti.

## Evidenza raggiungibilità (da registrare dopo l'esecuzione)
- Stato istanza atteso: `running`
- Status check atteso: `3/3 checks passed` (`aws ec2 wait instance-status-ok` lo attende)
- SSH: prompt Amazon Linux

## Screenshot e log
Cartella: `screenshots-vm-reti-storage/lab-1/`

- `log-lab-1.txt`
- `passo-01.png`
- `passo-02.png`
- `passo-03.png`
- `passo-04.png`
- `passo-05.png`

## Checkpoint
- [x] Tipo istanza coerente, entro `.large`
- [x] SG solo 22 (ristretta) + 80, non `0.0.0.0/0` su tutte le porte
- [x] Key pair `.pem` scaricata subito, Connessione SSH descritta
- [ ] Evidenza SSH registrata (valori reali da inserire dopo l'esecuzione nel Learner Lab)
- [ ] Cleanup eseguito (comando nella sezione Cleanup)

## Cleanup
- Istanza: `aws ec2 terminate-instances` (comando in fondo); da eseguire solo se non serve ai lab successivi.
- Elastic IP: nessuno allocato, niente da rilasciare.

## Nota
IP pubblico e ID AMI nel testo sono illustrativi. L'ID reale dell'AMI Amazon Linux 2023 si ottiene dal parametro SSM usato nella procedura CLI (`BASE_AMI`), non si scrive a mano.

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
# User data (dnf install httpd) può finire dopo lo status check: si riprova fino a 20 volte invece di un solo tentativo dopo 30 s
for i in $(seq 1 20); do curl -sI -m 5 http://$IP1/ | head -1 | grep -q "200 OK" && break; sleep 15; done
curl -sI http://$IP1/ | head -1
```

### Cleanup

```bash
aws ec2 terminate-instances --instance-ids $ID1     # solo se l'istanza non serve ai lab successivi
```
