# Deliverable Lab 11 - Architettura multi-tier e connettivita ibrida

## Configurazione
Creato con Terraform in `demo-vpc` (`10.0.0.0/16`).

### Subnet
| Tier | CIDR | Tipo |
|---|---|---|
| web | `10.0.1.0/24` | pubblica |
| application | `10.0.2.0/24` | privata |
| database | `10.0.3.0/24` | privata dedicata, nessuna rotta verso IGW |

### Catena di Security Group
L'origine e sempre il gruppo a monte, non un CIDR.

| Security Group | Regola inbound | Origine | ID |
|---|---|---|---|
| `demo-sg-tier-alb` | gruppo di ingresso pianificato, nessun ALB associato | - | - |
| `demo-sg-tier-web` | HTTP 80 | SG ALB | `sg-026804242271f1f08` |
| `demo-sg-tier-app` | TCP 8080 | SG web | `sg-0cb2e1e70ba4e1cee` |
| `demo-sg-tier-db` | MySQL/Aurora 3306 | SG app | `sg-0d921e876b3a6e2c5` |

Il database non accetta direttamente il gruppo web (screenshot: inbound 3306 con un Security Group come origine; verifica CLI `describe-security-groups` coerente).

## Collegamento ibrido
### Creato
Virtual Private Gateway `demo-vgw` (`vgw-000a3229e7834c3fc`) creato e attached a `demo-vpc` (screenshot: Available, Attached).

### Non creato (SCP del Learner Lab)
`ec2:CreateCustomerGateway` e negato da una service control policy (`UnauthorizedOperation`, explicit deny in a service control policy). Customer Gateway e VPN Connection non sono stati creati; la parte VPN e documentale:

| Risorsa | Configurazione prevista |
|---|---|
| Customer Gateway `demo-cgw` | BGP ASN 65000, IP `203.0.113.10` (indirizzo riservato agli esempi) |
| VPN Connection `demo-vpn` | target `demo-vgw`, routing Static, rete on-premises `192.168.0.0/16` |

Senza un dispositivo remoto i tunnel resterebbero DOWN: la configurazione documenta solo il lato AWS, non una connettivita riuscita.

## Scelta VPN o Direct Connect
| Criterio | Site-to-Site VPN | Direct Connect |
|---|---|---|
| Banda | moderata | elevata e stabile |
| Latenza | variabile (Internet) | prevedibile |
| Costo | contenuto | piu alto |
| Attivazione | pochi minuti | settimane |
| Cifratura | IPsec inclusa | da progettare separatamente |

Per uno scenario con banda moderata, costo contenuto e attivazione rapida si sceglie la Site-to-Site VPN.

## Motivazione scelte
- SG a catena con origine il gruppo a monte: ogni tier raggiungibile solo dal tier precedente
- Subnet database senza rotta verso IGW: nessuna esposizione diretta a Internet
- VPN come documento perche l'operazione e negata dal Learner Lab

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | Subnet | web pubblica, app e db private |
| 2 | Catena SG | ALB -> web (80) -> app (8080) -> db (3306) |
| 3 | VGW | `vgw-000a3229e7834c3fc`, Available, Attached |
| 4 | CGW/VPN | non creati: `UnauthorizedOperation` (SCP) |

## Checkpoint
- [x] Tre tier con subnet dedicate, database senza IGW
- [x] Security Group a catena, origine = SG a monte
- [x] VGW creato e attached
- [x] Limite SCP su CGW/VPN dichiarato; configurazione solo documentale
- [x] Scelta VPN/Direct Connect motivata
- [x] Cleanup eseguito (vedi sotto)

## Cleanup
Security Group, subnet, VGW e VPC rimossi a fine percorso.

### Cleanup finale (Lab 8-11)
- Bucket `demo-vm-reti-storage-rg-2026`: svuotato (tutte le versioni e i delete marker) ed eliminato
- `terraform destroy`: rimossi istanze `demo-web-01` e `demo-web-02`, volumi EBS (`demo-encrypted-vol`, `demo-data-vol`, `demo-data-vol-02`), EFS `demo-efs-shared` con i mount target, Security Group (`demo-sg-efs`, `demo-sg-instances`, `demo-sg-tier-alb/web/app/db`), subnet, internet gateway, VGW `demo-vgw` e VPC `demo-vpc`
- Verifica via CLI: nessuna istanza, volume, file system EFS, VGW o bucket residuo; resta solo la VPC di default
- Customer Gateway e VPN Connection non creati (SCP), nulla da eliminare

## Nota metodologica
ID dei Security Group e del VGW sono valori osservati dalle risorse create.

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
VPC=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=demo-vpc --query "Vpcs[0].VpcId" --output text)

# Step 1 - Subnet database privata dedicata (10.0.3.0/24), senza rotta verso IGW
SUB_DB=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.0.3.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=demo-subnet-db-1a}]' --query Subnet.SubnetId --output text)
RT_DB=$(aws ec2 create-route-table --vpc-id $VPC --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=demo-rt-db}]' --query RouteTable.RouteTableId --output text)
aws ec2 associate-route-table --route-table-id $RT_DB --subnet-id $SUB_DB      # solo rotta locale
aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC --query "Subnets[].[Tags[?Key=='Name']|[0].Value,CidrBlock,AvailabilityZone]" --output table

# Steps 2-3 - Security Group a catena: origine sempre il gruppo a monte
SG_ALB=$(aws ec2 create-security-group --group-name demo-sg-tier-alb --description "ingresso pianificato (nessun ALB)" --vpc-id $VPC --query GroupId --output text)
SG_WEB=$(aws ec2 create-security-group --group-name demo-sg-tier-web --description "tier web" --vpc-id $VPC --query GroupId --output text)
SG_APP=$(aws ec2 create-security-group --group-name demo-sg-tier-app --description "tier application" --vpc-id $VPC --query GroupId --output text)
SG_DB=$(aws ec2 create-security-group --group-name demo-sg-tier-db --description "tier database" --vpc-id $VPC --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_WEB --protocol tcp --port 80   --source-group $SG_ALB
aws ec2 authorize-security-group-ingress --group-id $SG_APP --protocol tcp --port 8080 --source-group $SG_WEB
aws ec2 authorize-security-group-ingress --group-id $SG_DB  --protocol tcp --port 3306 --source-group $SG_APP

# Step 4 - Verifica della catena ALB -> web -> app -> db (il db non accetta direttamente il gruppo web)
aws ec2 describe-security-groups --filters "Name=group-name,Values=demo-sg-tier-web,demo-sg-tier-app,demo-sg-tier-db" --query "SecurityGroups[].{Name:GroupName,Rules:IpPermissions[].UserIdGroupPairs[].GroupId}"
echo "ALB=$SG_ALB WEB=$SG_WEB APP=$SG_APP DB=$SG_DB"

# Step 6 - Virtual Private Gateway attached a demo-vpc
VGW=$(aws ec2 create-vpn-gateway --type ipsec.1 --tag-specifications 'ResourceType=vpn-gateway,Tags=[{Key=Name,Value=demo-vgw}]' --query VpnGateway.VpnGatewayId --output text)
aws ec2 attach-vpn-gateway --vpn-gateway-id $VGW --vpc-id $VPC
aws ec2 describe-vpn-gateways --vpn-gateway-ids $VGW --query "VpnGateways[].[VpnGatewayId,State,VpcAttachments[0].State]" --output text

# Step 5 e 7 - Customer Gateway e VPN Connection (nel Learner Lab falliscono: UnauthorizedOperation, SCP)
CGW=$(aws ec2 create-customer-gateway --type ipsec.1 --bgp-asn 65000 --public-ip 203.0.113.10 --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=demo-cgw}]' --query CustomerGateway.CustomerGatewayId --output text) || echo "CGW non creabile: parte VPN solo documentale"
# Se il CGW fosse consentito:
# aws ec2 create-vpn-connection --type ipsec.1 --customer-gateway-id $CGW --vpn-gateway-id $VGW --options StaticRoutesOnly=true --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=demo-vpn}]'
# aws ec2 create-vpn-connection-route --vpn-connection-id <vpn-id> --destination-cidr-block 192.168.0.0/16
```

Scelta VPN o Direct Connect: Site-to-Site VPN (banda moderata, costo contenuto, attivazione in minuti, tunnel IPsec); Direct Connect per banda elevata e latenza prevedibile.

### Cleanup finale (Lab 8-11)

```bash
# S3: svuotare tutte le versioni e i delete marker, poi eliminare il bucket
BUCKET=demo-vm-reti-storage-rg-2026
aws s3api list-object-versions --bucket $BUCKET --query "Versions[].[Key,VersionId]" --output text | while read K V; do aws s3api delete-object --bucket $BUCKET --key "$K" --version-id "$V" > /dev/null; done
aws s3api list-object-versions --bucket $BUCKET --query "DeleteMarkers[].[Key,VersionId]" --output text | while read K V; do aws s3api delete-object --bucket $BUCKET --key "$K" --version-id "$V" > /dev/null; done
aws s3api delete-bucket --bucket $BUCKET

# Istanze, volumi, EFS (ID dei Lab 09-10: ID1 ID2 V1 V2 VOL EFS SG_I SG_E)
aws ec2 terminate-instances --instance-ids $ID1 $ID2 && aws ec2 wait instance-terminated --instance-ids $ID1 $ID2
for M in $(aws efs describe-mount-targets --file-system-id $EFS --query "MountTargets[].MountTargetId" --output text); do aws efs delete-mount-target --mount-target-id $M; done
sleep 60
aws efs delete-file-system --file-system-id $EFS
aws ec2 delete-volume --volume-id $V1; aws ec2 delete-volume --volume-id $V2; aws ec2 delete-volume --volume-id $VOL

# Rete: SG, subnet, VGW e VPC
for G in $SG_E $SG_I $SG_DB $SG_APP $SG_WEB $SG_ALB; do aws ec2 delete-security-group --group-id $G; done
aws ec2 detach-vpn-gateway --vpn-gateway-id $VGW --vpc-id $VPC
sleep 30
aws ec2 delete-vpn-gateway --vpn-gateway-id $VGW
# Subnet/route table/IGW/VPC: usare la procedura di cleanup dei Lab 04-06 (NAT, IGW, route table, subnet, VPC demo-vpc)
```

Verifica finale: `aws ec2 describe-instances`, `describe-volumes`, `efs describe-file-systems`, `ec2 describe-vpn-gateways` e `s3api list-buckets` non devono mostrare risorse del lab.
