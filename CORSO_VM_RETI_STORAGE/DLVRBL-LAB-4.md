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
- [ ] Cleanup eseguito o giustificato

## Cleanup
- Subnet e VPC mantenute intenzionalmente per Lab 05: sì/no
- Se non si prosegue: subnet eliminate, poi `demo-vpc`: sì/no

## Nota metodologica
ID VPC/subnet non riportati: variano a ogni creazione, sostituire con valori reali del Learner Lab. Fallback se Learner Lab non raggiungibile: tabella CIDR + confronto con documentazione VPC, nessuna risorsa reale.
