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
aws ec2 describe-instances `
  --filters "Name=tag:Name,Values=demo-web-01" `
  --query "Reservations[].Instances[].{State:State.Name,Type:InstanceType,PublicIP:PublicIpAddress}" `
  --output table
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
ssh -i $key ec2-user@X.X.X.X
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