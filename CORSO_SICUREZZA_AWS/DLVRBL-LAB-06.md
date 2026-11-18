# Consegna Lab 06 - VPC, Security Group e Network ACL

## Configurazione
Creata con Terraform (IaC) in `us-east-1`:

| Risorsa | Configurazione |
|---|---|
| VPC `sicurezza06-rg` | `10.60.0.0/16` |
| Subnet | `10.60.1.0/24`, `us-east-1a`, nessun IPv4 pubblico automatico |
| Security Group | inbound HTTPS TCP 443 da `10.20.1.0/24`; regola outbound generale rimossa |
| Network ACL | inbound 100 TCP 443 da `10.20.1.0/24` Allow; outbound 100 TCP 1024-65535 verso `10.20.1.0/24` Allow; associata solo alla subnet del lab |

Nessun accesso Internet e nessuna istanza.

## Motivazione scelte
- Security Group senza outbound generale: solo il traffico necessario, riduce l'esposizione
- Security Group e NACL coerenti: il SG e stateful, il NACL e stateless e richiede la regola di ritorno sulle porte effimere (1024-65535)
- Origine limitata a `10.20.1.0/24` invece di `0.0.0.0/0`: minimo privilegio

## Decisioni sui pacchetti
| # | Direzione | Origine/Destinazione | Porta | Decisione | Motivo |
|--:|---|---|---|---|---|
| 1 | ingresso | da `10.20.1.10` | TCP 443 | ammesso | regola SG e NACL 100 |
| 2 | ingresso | da `10.20.1.10` | TCP 22 | negato | nessuna regola Allow |
| 3 | uscita | verso `10.20.1.10` | TCP 55000 | ammessa | NACL outbound 1024-65535 |
| 4 | uscita | verso `10.20.1.10` | TCP 80 | negata | porta fuori da 1024-65535 |

## Come funzionano le regole
- Una Network ACL appena creata nega tutto (regola finale `*` con `Deny`): senza le regole 100 nessun pacchetto passa.
- Le regole sono valutate in ordine crescente di numero e si ferma alla prima che corrisponde, quindi un `Deny` con numero più basso prevale su un `Allow` con numero più alto.
- Il Security Group è stateful (la risposta passa da sola); la NACL è stateless, per questo serve la regola di uscita sulle porte effimere 1024-65535.

## Identificativi delle risorse create
La procedura CLI stampa `VPC`, `SUB`, `SG`, `NACL`, `OLD_NACL` e `NEW_ASSOC` con `echo`: copiarli qui dopo l'esecuzione. `OLD_NACL` è la ACL precedente della subnet, necessaria per il ripristino nel cleanup.

## Limite
Nessun test applicativo è dichiarato riuscito: senza istanza e senza accesso Internet le decisioni derivano dalla lettura delle regole, non da traffico reale.

## Checkpoint
- [x] SG e NACL configurati con regole minime
- [x] 4 decisioni sui pacchetti motivate
- [x] Dichiarata l'assenza di test applicativi
- [x] Cleanup descritto in questo documento (sezione Cleanup: ripristino ACL, eliminazione ACL, Security Group, subnet e VPC)

Procedura di esecuzione in CLI Cloudshell:

Il lab è stato eseguito con Terraform; qui l'equivalente con AWS CLI. Nessuna istanza, NAT o indirizzo pubblico viene creato.

```bash
export AWS_DEFAULT_REGION=us-east-1
SUF=rg

# Steps 1-6 - VPC sicurezza06-SUFFISSO (10.60.0.0/16)
VPC=$(aws ec2 create-vpc --cidr-block 10.60.0.0/16 --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=sicurezza06-$SUF}]" --query Vpc.VpcId --output text)
aws ec2 wait vpc-available --vpc-ids $VPC

# Steps 7-11 - Subnet 10.60.1.0/24 in una AZ, senza IPv4 pubblico automatico
SUB=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.60.1.0/24 --availability-zone us-east-1a --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=sicurezza06-$SUF}]" --query Subnet.SubnetId --output text)
aws ec2 modify-subnet-attribute --subnet-id $SUB --no-map-public-ip-on-launch

# Steps 12-15 - Security Group: inbound HTTPS 443 da 10.20.1.0/24, outbound generale rimosso
SG=$(aws ec2 create-security-group --group-name sicurezza06-$SUF --description "lab sicurezza06" --vpc-id $VPC --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port 443 --cidr 10.20.1.0/24
aws ec2 revoke-security-group-egress --group-id $SG --ip-permissions 'IpProtocol=-1,IpRanges=[{CidrIp=0.0.0.0/0}]'

# Steps 16-19 - Network ACL: inbound 100 TCP 443 da 10.20.1.0/24 Allow; outbound 100 TCP 1024-65535 verso 10.20.1.0/24 Allow
NACL=$(aws ec2 create-network-acl --vpc-id $VPC --tag-specifications "ResourceType=network-acl,Tags=[{Key=Name,Value=sicurezza06-$SUF}]" --query NetworkAcl.NetworkAclId --output text)
aws ec2 create-network-acl-entry --network-acl-id $NACL --ingress --rule-number 100 --protocol 6 --port-range From=443,To=443 --cidr-block 10.20.1.0/24 --rule-action allow
aws ec2 create-network-acl-entry --network-acl-id $NACL --egress  --rule-number 100 --protocol 6 --port-range From=1024,To=65535 --cidr-block 10.20.1.0/24 --rule-action allow

# Steps 20-21 - Associare la ACL solo alla subnet del lab, annotando quella precedente
OLD_ASSOC=$(aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=$SUB --query "NetworkAcls[0].Associations[?SubnetId=='$SUB'].NetworkAclAssociationId" --output text)
OLD_NACL=$(aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=$SUB --query "NetworkAcls[0].NetworkAclId" --output text)
NEW_ASSOC=$(aws ec2 replace-network-acl-association --association-id $OLD_ASSOC --network-acl-id $NACL --query NewAssociationId --output text)
echo "VPC=$VPC SUB=$SUB SG=$SG NACL=$NACL OLD_NACL=$OLD_NACL NEW_ASSOC=$NEW_ASSOC"

# Verifica regole
aws ec2 describe-security-groups --group-ids $SG --query "SecurityGroups[0].[IpPermissions,IpPermissionsEgress]" --output json
aws ec2 describe-network-acls --network-acl-ids $NACL --query "NetworkAcls[0].Entries[?RuleNumber!=\`32767\`].[RuleNumber,Egress,Protocol,PortRange,CidrBlock,RuleAction]" --output json
```

Decisioni attese sui pacchetti: ingresso da `10.20.1.10` su 443 ammesso, su 22 negato; uscita verso `10.20.1.10:55000` ammessa, verso `:80` negata.

### Cleanup

```bash
aws ec2 replace-network-acl-association --association-id $NEW_ASSOC --network-acl-id $OLD_NACL   # ripristina la ACL precedente
aws ec2 delete-network-acl --network-acl-id $NACL
aws ec2 delete-security-group --group-id $SG
aws ec2 delete-subnet --subnet-id $SUB
aws ec2 delete-vpc --vpc-id $VPC
aws ec2 describe-vpcs --query "Vpcs[].[VpcId,IsDefault]" --output table      # deve restare solo la VPC di default
```
