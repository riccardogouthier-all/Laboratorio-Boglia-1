# Deliverable Lab 06 - Security Group, Network ACL e Architetture di Rete Sicure

## Configurazione
- Rete (da Lab 04/05): `demo-vpc`, bastion `demo-bastion` in `demo-subnet-public-1a`, `demo-private-test` in `demo-subnet-private-1a`
- Security Group: `demo-sg-bastion` (22 da `$MYIP/32`), `demo-sg-private` (22 da `demo-sg-bastion`)
- Network ACL: `demo-nacl-private`, associata a `demo-subnet-private-1a` (NACL precedente annotata per ripristino: `<acl-...>`)

## Motivazione scelte
- Minimo privilegio: nessuna regola `0.0.0.0/0` su porte sensibili
- SG stateful: risposte ammesse automaticamente, nessuna regola di ritorno
- NACL stateless: serve regola esplicita in uscita per le risposte → outbound `1024-65535` verso `10.0.1.0/24` (porte effimere)
- Numerazione a passi di 50/100: margine per eccezioni (es. deny `50`) senza rinumerare
- NACL custom nuova nega tutto di default: regole aggiunte una alla volta, test dopo ciascuna

## Regole NACL `demo-nacl-private`
| Direzione | Regola # | Protocollo | Porta | CIDR | Azione |
|---|--:|---|---|---|---|
| Inbound | 100 | TCP | 22 | `10.0.1.0/24` | Allow |
| Outbound | 100 | TCP | 1024-65535 | `10.0.1.0/24` | Allow |
| Inbound (test, rimossa) | 50 | All | All | `10.0.1.0/24` | Deny |

## Verifica SG (CLI)
```bash
aws ec2 describe-security-groups --group-ids $SG_B $SG_P \
  --query "SecurityGroups[].[GroupName,IpPermissions[].[FromPort,IpRanges[].CidrIp|join(',',@),UserIdGroupPairs[].GroupId|join(',',@)]]" --output json
```
Atteso: `demo-sg-bastion` → 22 da `<MYIP>/32`; `demo-sg-private` → 22 da `$SG_B`.

## Sequenza test (CLI)
```bash
ssh -o ConnectTimeout=5 lab-private hostname
```
| Passo | Modifica NACL | Risultato SSH atteso |
|--:|---|---|
| 0 | nessuna (NACL precedente) | riuscito |
| 1 | NACL custom vuota associata | timeout |
| 2 | + inbound 100 (22 da `10.0.1.0/24`) | timeout (uscita negata) |
| 3 | + outbound 100 (1024-65535) | riuscito: `ip-10-0-2-...` |
| 4 | + inbound 50 deny all | timeout (50 valutata prima di 100) |
| 5 | − inbound 50 | riuscito |

Il confronto passo 2 → 3 evidenzia natura stateless della NACL.

## Verifica regole (CLI)
```bash
aws ec2 describe-network-acls --network-acl-ids $NACL \
  --query "NetworkAcls[0].Entries[?RuleNumber!=\`32767\`].[RuleNumber,Egress,Protocol,PortRange,CidrBlock,RuleAction]" --output json
```
Output atteso: due voci, inbound 100 allow 22, outbound 100 allow 1024-65535 (regola 50 assente).

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | SG istanza privata | `demo-sg-private`: SSH solo da `demo-sg-bastion`, nessun `0.0.0.0/0` |
| 2 | NACL personalizzata | `demo-nacl-private` su `demo-subnet-private-1a` |
| 3 | Inbound 100 | Allow 22 da `10.0.1.0/24` |
| 4 | Outbound 100 | Allow 1024-65535 verso `10.0.1.0/24` |
| 5 | Priorità regole | deny 50 prima di allow 100; rimossa dopo test |

## Checkpoint
- [x] Nessun `0.0.0.0/0` su porte sensibili senza motivazione
- [x] NACL con regola inbound e outbound di risposta
- [x] Traffico legittimo bastion → privata funzionante dopo modifiche
- [ ] Cleanup regole di test eseguito o giustificato

## Cleanup
- Regola deny 50 rimossa: sì/no
- Associazione subnet ripristinata alla NACL precedente (necessario: regole solo-SSH bloccherebbero HTTPS/NFS nei lab successivi): sì/no
- `demo-nacl-private` eliminata: sì/no
- Bastion/istanza privata terminati, o conservati per Lab 11: sì/no

## Nota metodologica
ID NACL e IP privati illustrativi, da sostituire con valori reali. Fallback se Learner Lab non raggiungibile: tabella regole pianificate (porta, protocollo, origine, motivazione), nessuna risorsa reale.

Procedura di esecuzione in CLI Cloudshell:

```bash
# --- Passo 1 ---
ssh -o ConnectTimeout=5 lab-private hostname
aws ec2 describe-security-groups --group-ids $SG_B $SG_P --query "SecurityGroups[].[GroupName,IpPermissions[].[FromPort,IpRanges[].CidrIp|join(',',@),UserIdGroupPairs[].GroupId|join(',',@)]]" --output json

# --- Passo 2 ---
OLD_ASSOC=$(aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=$PRIV --query "NetworkAcls[0].Associations[?SubnetId=='$PRIV'].NetworkAclAssociationId" --output text)
OLD_NACL=$(aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=$PRIV --query "NetworkAcls[0].NetworkAclId" --output text)
echo $OLD_ASSOC $OLD_NACL

NACL=$(aws ec2 create-network-acl --vpc-id $VPC4 --tag-specifications 'ResourceType=network-acl,Tags=[{Key=Name,Value=demo-nacl-private}]' --query NetworkAcl.NetworkAclId --output text)
NEW_ASSOC=$(aws ec2 replace-network-acl-association --association-id $OLD_ASSOC --network-acl-id $NACL --query NewAssociationId --output text)
echo NACL=$NACL NEW_ASSOC=$NEW_ASSOC

# --- Passo 3 ---
aws ec2 create-network-acl-entry --network-acl-id $NACL --ingress --rule-number 100 --protocol 6 --port-range From=22,To=22 --cidr-block 10.0.1.0/24 --rule-action allow
ssh -o ConnectTimeout=5 lab-private hostname

# --- Passo 4 ---
aws ec2 create-network-acl-entry --network-acl-id $NACL --egress --rule-number 100 --protocol 6 --port-range From=1024,To=65535 --cidr-block 10.0.1.0/24 --rule-action allow
ssh -o ConnectTimeout=5 lab-private hostname

# --- Passo 5 ---
aws ec2 create-network-acl-entry --network-acl-id $NACL --ingress --rule-number 50 --protocol=-1 --cidr-block 10.0.1.0/24 --rule-action deny
ssh -o ConnectTimeout=5 lab-private hostname

# --- Passo 6 ---
aws ec2 delete-network-acl-entry --network-acl-id $NACL --ingress --rule-number 50
ssh -o ConnectTimeout=5 lab-private hostname

# --- Passo 7 ---
aws ec2 describe-network-acls --network-acl-ids $NACL --query "NetworkAcls[0].Entries[?RuleNumber!=\`32767\`].[RuleNumber,Egress,Protocol,PortRange,CidrBlock,RuleAction]" --output json
```
