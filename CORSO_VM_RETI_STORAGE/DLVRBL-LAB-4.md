# Deliverable Lab 04 - Concetti Base di VPC e Subnet Pubbliche/Private

## Configurazione
- VPC: `demo-vpc`, CIDR `10.0.0.0/16`, tenancy `default` (separata dalla VPC di default dei Lab 01–03)
- Regione: `us-east-1`

## Pianificazione CIDR
| Nome | CIDR | AZ | Tipo |
|---|---|---|---|
| `demo-vpc` | `10.0.0.0/16` | - | rete dedicata |
| `demo-subnet-public-1a` | `10.0.1.0/24` | `us-east-1a` | pubblica (pianificata) |
| `demo-subnet-private-1a` | `10.0.2.0/24` | `us-east-1a` | privata |

## Motivazione scelte
- `/16`: spazio per subnet future senza rinumerazione
- `/24` distinte non sovrapposte: 251 IP utilizzabili ciascuna, nessun conflitto di creazione
- Stessa AZ `us-east-1a`: lab minimale, una subnet per livello
- Distinzione pubblica/privata basata su route table, non sul nome

## Verifica subnet (CLI)
```bash
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC4" \
  --query "Subnets[].{Name:Tags[?Key=='Name']|[0].Value,CIDR:CidrBlock,AZ:AvailabilityZone}" --output table
```
Output atteso:
```
| us-east-1a | demo-subnet-public-1a  | 10.0.1.0/24 |
| us-east-1a | demo-subnet-private-1a | 10.0.2.0/24 |
```

## Verifica route table (CLI)
```bash
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC4" "Name=association.main,Values=true" \
  --query "RouteTables[].Routes"
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC4" "Name=association.subnet-id,Values=$PUB,$PRIV" \
  --query "RouteTables[].RouteTableId"
```
Output atteso (main route table):
```
[[{"DestinationCidrBlock": "10.0.0.0/16", "GatewayId": "local", "State": "active"}]]
```
Secondo comando: output vuoto → nessuna associazione esplicita, entrambe le subnet usano implicitamente la main route table.

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | VPC | `demo-vpc`, `10.0.0.0/16` |
| 2 | Subnet pubblica (pianificata) | `demo-subnet-public-1a`, `10.0.1.0/24`, `us-east-1a` |
| 3 | Subnet privata | `demo-subnet-private-1a`, `10.0.2.0/24`, `us-east-1a` |
| 4 | Route table osservata | main, solo `10.0.0.0/16 → local`, nessun IGW |
| 5 | Conclusione | nessuna subnet realmente pubblica: manca rotta `0.0.0.0/0 → IGW`; `public` = solo nome |

## Checkpoint
- [x] CIDR VPC abbastanza ampio per subnet pianificate
- [x] Due subnet con CIDR distinti, non sovrapposti
- [x] Distinzione pubblica/privata motivata da route table, non dal nome
- [x] Cleanup giustificato: subnet e VPC si tengono per il Lab 05 (comandi di eliminazione nella sezione Cleanup)

## Cleanup
- Subnet e VPC si mantengono per il Lab 05, che le riusa.
- Se non si prosegue: si eliminano prima le subnet, poi `demo-vpc` (comandi sotto).

## Nota metodologica
Gli ID di VPC e subnet variano a ogni creazione: la procedura CLI li salva in `VPC4`, `PUB` e `PRIV`.

Procedura di esecuzione in CLI Cloudshell:

```bash
# --- Passo 1 ---
export AWS_DEFAULT_REGION=us-east-1
VPC4=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --instance-tenancy default --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=demo-vpc}]' --query Vpc.VpcId --output text)
aws ec2 wait vpc-available --vpc-ids $VPC4
echo $VPC4

# --- Passo 2 ---
# Piano dei CIDR (vedi tabella "Pianificazione CIDR" sopra):
#   demo-vpc                10.0.0.0/16
#   demo-subnet-public-1a   10.0.1.0/24   us-east-1a   pubblica (pianificata)
#   demo-subnet-private-1a  10.0.2.0/24   us-east-1a   privata

# --- Passo 3 ---
PUB=$(aws ec2 create-subnet --vpc-id $VPC4 --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=demo-subnet-public-1a}]' --query Subnet.SubnetId --output text)
PRIV=$(aws ec2 create-subnet --vpc-id $VPC4 --cidr-block 10.0.2.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=demo-subnet-private-1a}]' --query Subnet.SubnetId --output text)
echo $PUB $PRIV

# --- Passo 4 ---
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC4" --query "Subnets[].{Name:Tags[?Key=='Name']|[0].Value,CIDR:CidrBlock,AZ:AvailabilityZone}" --output table

# --- Passo 5 ---
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC4" "Name=association.main,Values=true" --query "RouteTables[].Routes"

# --- Passo 6 ---
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC4" "Name=association.subnet-id,Values=$PUB,$PRIV" --query "RouteTables[].RouteTableId"

# --- Passo 7 ---
# Nessuna subnet realmente pubblica: manca rotta 0.0.0.0/0 → IGW. public = solo nome.
```

### Cleanup

```bash
# Solo se non si prosegue con il Lab 05
aws ec2 delete-subnet --subnet-id $PUB
aws ec2 delete-subnet --subnet-id $PRIV
aws ec2 delete-vpc --vpc-id $VPC4
```
