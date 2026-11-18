# Deliverable Lab 05 - Routing, Internet Gateway, NAT Gateway e Bastion Host

## Configurazione
- VPC/subnet (da Lab 04): `demo-vpc`, `demo-subnet-public-1a` (`10.0.1.0/24`), `demo-subnet-private-1a` (`10.0.2.0/24`)
- Internet Gateway: `demo-igw`, collegato a `demo-vpc`
- Route table pubblica: `demo-rt-public`, `0.0.0.0/0 → demo-igw`, associata a `demo-subnet-public-1a`
- NAT Gateway: `demo-nat` (Public), in `demo-subnet-public-1a`, Elastic IP associato
- Route table privata: main route table, `0.0.0.0/0 → demo-nat`
- Bastion: `demo-bastion` (`t3.micro`, AL2023, `demo-key`, IP pubblico), SG `demo-sg-bastion`
- Istanza privata: `demo-private-test` (`t3.micro`, AL2023, `demo-key`, senza IP pubblico), SG `demo-sg-private`

## Motivazione scelte
- IGW su subnet pubblica: accesso bidirezionale Internet
- NAT in subnet pubblica per subnet privata: solo uscita, nessun ingresso da Internet
- `demo-sg-bastion`: SSH 22 solo da `$MYIP/32`, non `0.0.0.0/0`
- `demo-sg-private`: SSH 22 con sorgente `demo-sg-bastion` (SG, non IP): regola valida anche se cambia IP bastion
- Bastion = unico punto d'accesso SSH; chiave privata resta sul computer locale (`ProxyJump`)

## Verifica rotte (CLI)
```bash
aws ec2 describe-route-tables --filters Name=vpc-id,Values=$VPC4 \
  --query "RouteTables[].[RouteTableId,Routes[?DestinationCidrBlock=='0.0.0.0/0'].[GatewayId,NatGatewayId,State]]" --output json
```
Output atteso (illustrativo):
```
[["rtb-0demo-public", [["igw-0demo123", null, "active"]]], ["rtb-0demo-main", [[null, "nat-0demo456", "active"]]]]
```

## Configurazione SSH
File `~/.ssh/config`:
```text
Host lab-bastion
    HostName <IP_PUBBLICO_BASTION>
    User ec2-user
    IdentityFile ~/demo-key.pem
    IdentitiesOnly yes

Host lab-private
    HostName <IP_PRIVATO_ISTANZA>
    User ec2-user
    IdentityFile ~/demo-key.pem
    IdentitiesOnly yes
    ProxyJump lab-bastion
```
```bash
ssh lab-bastion 'hostname'
ssh lab-private 'hostname; curl -sI https://aws.amazon.com | head -1'
```
Output atteso: hostname privato (es. `ip-10-0-2-15...`) + `HTTP/2 200` → uscita via NAT confermata.

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | Internet Gateway | `demo-igw`, collegato a `demo-vpc`, rotta `0.0.0.0/0` su `demo-rt-public` |
| 2 | NAT Gateway | `demo-nat`, `available`, in `demo-subnet-public-1a`, EIP associato |
| 3 | Rotta subnet privata | `0.0.0.0/0 → demo-nat` |
| 4 | Bastion | `demo-bastion`, `demo-sg-bastion` (22 da `$MYIP/32`) |
| 5 | Salto SSH | `lab-bastion` → `lab-private` riuscito; `curl` → HTTP 200 |

Verifica: `demo-private-test` senza IP pubblico (`PublicIpAddress` = `None`).

## Checkpoint
- [x] Subnet pubblica con rotta verso IGW
- [x] Subnet privata con rotta verso NAT
- [x] Bastion con SSH ristretto a IP specifico
- [x] Istanza privata con SSH ristretto al SG del bastion
- [ ] Cleanup (NAT, EIP, bastion, istanza privata): comandi forniti, esecuzione da confermare

## Cleanup
Comandi nella sezione "Cleanup" in fondo; stato da confermare dopo l'esecuzione.
- Se si prosegue con il Lab 06: si conservano bastion, istanza privata, VPC, subnet e IGW (il Lab 06 li riusa).
- NAT `demo-nat` eliminato ed Elastic IP rilasciato: il NAT costa a ore, va eliminato appena finito il lab.
- Rotta `blackhole` (il NAT è stato eliminato) rimossa dalla route table privata.
- Bastion e istanza privata terminati; IGW scollegato ed eliminato (solo a fine percorso).

## Nota metodologica
IP e ID di IGW, NAT ed EIP variano a ogni creazione: la procedura CLI li salva in `BIP`, `PIP`, `IGW`, `NAT`, `EIP`. Il Security Group `demo-sg-private` non limita il traffico in uscita (regola di default), per questo l'istanza privata raggiunge HTTPS attraverso il NAT.

Procedura di esecuzione in CLI Cloudshell:

```bash
# --- Passo 0 ---
export AWS_DEFAULT_REGION=us-east-1
VPC4=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=demo-vpc --query "Vpcs[0].VpcId" --output text)
PUB=$(aws ec2 describe-subnets --filters Name=tag:Name,Values=demo-subnet-public-1a --query "Subnets[0].SubnetId" --output text)
PRIV=$(aws ec2 describe-subnets --filters Name=tag:Name,Values=demo-subnet-private-1a --query "Subnets[0].SubnetId" --output text)
echo $VPC4 $PUB $PRIV; ls -l demo-key.pem

# --- Passo 1 ---
IGW=$(aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=demo-igw}]' --query InternetGateway.InternetGatewayId --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC4

# --- Passo 2 ---
RT_PUB=$(aws ec2 create-route-table --vpc-id $VPC4 --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=demo-rt-public}]' --query RouteTable.RouteTableId --output text)
aws ec2 create-route --route-table-id $RT_PUB --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW
aws ec2 associate-route-table --route-table-id $RT_PUB --subnet-id $PUB

# --- Passo 3 ---
EIP=$(aws ec2 allocate-address --domain vpc --query AllocationId --output text)
NAT=$(aws ec2 create-nat-gateway --subnet-id $PUB --allocation-id $EIP --connectivity-type public --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=demo-nat}]' --query NatGateway.NatGatewayId --output text)
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT
echo $IGW $RT_PUB $EIP $NAT

# --- Passo 4 ---
RT_MAIN=$(aws ec2 describe-route-tables --filters Name=vpc-id,Values=$VPC4 Name=association.main,Values=true --query "RouteTables[0].RouteTableId" --output text)
aws ec2 create-route --route-table-id $RT_MAIN --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT

# --- Passo 5 ---
aws ec2 describe-route-tables --filters Name=vpc-id,Values=$VPC4 --query "RouteTables[].[RouteTableId,Routes[?DestinationCidrBlock=='0.0.0.0/0'].[GatewayId,NatGatewayId,State]]" --output json

# --- Passo 6 ---
MYIP=$(curl -s https://checkip.amazonaws.com)
SG_B=$(aws ec2 create-security-group --group-name demo-sg-bastion --description "demo bastion" --vpc-id $VPC4 --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_B --protocol tcp --port 22 --cidr $MYIP/32

SG_P=$(aws ec2 create-security-group --group-name demo-sg-private --description "demo private" --vpc-id $VPC4 --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_P --protocol tcp --port 22 --source-group $SG_B

# --- Passo 7 ---
BASE_AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text)

BID=$(aws ec2 run-instances --image-id $BASE_AMI --instance-type t3.micro --key-name demo-key --subnet-id $PUB --security-group-ids $SG_B --associate-public-ip-address --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=demo-bastion}]' --query "Instances[0].InstanceId" --output text)

PID=$(aws ec2 run-instances --image-id $BASE_AMI --instance-type t3.micro --key-name demo-key --subnet-id $PRIV --security-group-ids $SG_P --no-associate-public-ip-address --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=demo-private-test}]' --query "Instances[0].InstanceId" --output text)

aws ec2 wait instance-status-ok --instance-ids $BID $PID

BIP=$(aws ec2 describe-instances --instance-ids $BID --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
PIP=$(aws ec2 describe-instances --instance-ids $PID --query "Reservations[0].Instances[0].PrivateIpAddress" --output text)
PPUB=$(aws ec2 describe-instances --instance-ids $PID --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo bastion=$BIP privata=$PIP pubblico_privata=$PPUB

# --- Passo 8 ---
mkdir -p ~/.ssh && chmod 700 ~/.ssh
touch ~/.ssh/config
sed -i '/^# BEGIN lab5/,/^# END lab5/d' ~/.ssh/config     # rende il passo ripetibile: toglie il blocco precedente
cat >> ~/.ssh/config <<EOF
# BEGIN lab5
Host lab-bastion
    HostName $BIP
    User ec2-user
    IdentityFile ~/demo-key.pem
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new

Host lab-private
    HostName $PIP
    User ec2-user
    IdentityFile ~/demo-key.pem
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
    ProxyJump lab-bastion
# END lab5
EOF
chmod 600 ~/.ssh/config

ssh lab-bastion 'hostname'
ssh lab-private 'hostname; curl -sI https://aws.amazon.com | head -1'

# --- Passo 9 ---
# Rotte: pubblica 0.0.0.0/0 → demo-igw; privata 0.0.0.0/0 → demo-nat
# demo-sg-bastion: 22 da $MYIP/32; demo-sg-private: 22 da $SG_B
# Salto SSH + curl annotati
```

### Cleanup

```bash
# Cleanup: NAT, EIP, istanze, route table, IGW, SG (ordine: dipendenze prima)
aws ec2 terminate-instances --instance-ids $BID $PID && aws ec2 wait instance-terminated --instance-ids $BID $PID
aws ec2 delete-nat-gateway --nat-gateway-id $NAT
aws ec2 wait nat-gateway-deleted --nat-gateway-ids $NAT
aws ec2 release-address --allocation-id $EIP
aws ec2 delete-security-group --group-id $SG_P; aws ec2 delete-security-group --group-id $SG_B

# Rotte e Internet Gateway (saltare questo blocco se si prosegue con il Lab 06, che riusa VPC, subnet e IGW)
aws ec2 delete-route --route-table-id $RT_MAIN --destination-cidr-block 0.0.0.0/0      # rotta blackhole verso il NAT eliminato
ASSOC=$(aws ec2 describe-route-tables --route-table-ids $RT_PUB --query "RouteTables[0].Associations[?Main==\`false\`].RouteTableAssociationId" --output text)
aws ec2 disassociate-route-table --association-id $ASSOC
aws ec2 delete-route-table --route-table-id $RT_PUB
aws ec2 detach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC4
aws ec2 delete-internet-gateway --internet-gateway-id $IGW
```
