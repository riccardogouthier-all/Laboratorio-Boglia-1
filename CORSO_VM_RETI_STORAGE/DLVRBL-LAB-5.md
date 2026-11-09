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
[[GatewayId: "igw-0demo123", State: "active"], [NatGatewayId: "nat-0demo456", State: "active"]]
```

## Configurazione SSH
```bash
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
- [ ] Cleanup (NAT, EIP, bastion, istanza privata) eseguito o giustificato

## Cleanup
- Se si prosegue con Lab 06: conservati bastion, istanza privata, VPC, subnet, IGW (riuso documentato): sì/no
- NAT `demo-nat` eliminato ed Elastic IP rilasciato (costo orario NAT): sì/no
- Rotta `blackhole` verso NAT eliminato rimossa dalla route table privata: sì/no
- Bastion e istanza privata terminati: sì/no
- IGW scollegato ed eliminato: sì/no

## Nota metodologica
IP pubblico/privato, ID IGW/NAT/EIP: valori reali da sostituire. Fallback se Learner Lab non raggiungibile: schema routing (IGW, NAT, bastion) su Markdown, nessuna risorsa reale.
