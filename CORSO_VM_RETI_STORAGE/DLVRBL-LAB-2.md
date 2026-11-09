# Deliverable Lab 02 - Gestione Immagini AMI ed Elastic Load Balancing

## Configurazione
- AMI: `demo-web-ami-v1` (`ami-0abc123demo`, esempio illustrativo), creata da `demo-web-01` fermata
- Istanze: `demo-web-01`, `demo-web-02` (`t3.micro`, key pair `demo-key`, Security Group `demo-sg-web`)
- `demo-web-02`: lanciata dalla stessa AMI, stessa VPC, subnet pubblica in AZ diversa
- Target group: `demo-tg-web` (Instances, HTTP:80, health check path `/`)
- Load balancer: `demo-alb` (Application Load Balancer, Internet-facing, due subnet pubbliche in AZ diverse, `demo-sg-web`)
- Listener: HTTP:80 → Forward to `demo-tg-web`

## Preparazione web server (Amazon Linux 2023)
```bash
sudo dnf install -y httpd
echo 'Servizio web del laboratorio AWS' | sudo tee /var/www/html/index.html
sudo systemctl enable --now httpd
curl -I http://localhost/
```
Output atteso: `HTTP/1.1 200 OK`. `enable` → servizio riparte su istanze create dalla AMI.

## Motivazione scelte
- AMI da istanza `stopped`: evita stato incoerente dei volumi EBS
- Seconda istanza in AZ diversa: resilienza a guasto di singola AZ
- ALB + health check su `/`: esclusione automatica istanze non sane, nessun intervento manuale

## Verifica AMI (CLI)
```bash
aws ec2 describe-images --owners self \
  --filters "Name=name,Values=demo-web-ami-v1" \
  --query "Images[].{Name:Name,State:State,ImageId:ImageId}" --output table
```
Output atteso:
```
+------------------+------------------+------------+
|     ImageId      |      Name        |   State    |
+------------------+------------------+------------+
|  ami-0abc123demo |  demo-web-ami-v1 |  available |
+------------------+------------------+------------+
```

## Verifica health check (CLI)
```bash
aws elbv2 describe-target-health --target-group-arn <arn-demo-tg-web>
```
Prima dello stop:
```
{"Target": {"Id": "i-demoweb01", "Port": 80}, "TargetHealth": {"State": "healthy"}}
{"Target": {"Id": "i-demoweb02", "Port": 80}, "TargetHealth": {"State": "healthy"}}
```
Dopo stop di `demo-web-02`:
```
{"Target": {"Id": "i-demoweb01", "Port": 80}, "TargetHealth": {"State": "healthy"}}
{"Target": {"Id": "i-demoweb02", "Port": 80}, "TargetHealth": {"State": "unused", "Reason": "Target.InvalidState"}}
```

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | AMI | `demo-web-ami-v1`, stato `available`, snapshot associato annotato |
| 2 | Seconda istanza | `demo-web-02`, stessa AMI, AZ diversa, web server risponde |
| 3 | Target group | `demo-tg-web`, HTTP:80, health check `/` |
| 4 | Load balancer | `demo-alb` `active`, DNS name `http://<DNS-ALB>/` risponde |
| 5 | Health check | prima: 2 `healthy`; dopo stop: `demo-web-01` `healthy`, `demo-web-02` `unused`; dopo riavvio: 2 `healthy` |

## Checkpoint
- [x] AMI creata da istanza in stato coerente (`stopped`), nome con versione
- [x] AMI `available` prima del lancio di `demo-web-02`
- [x] Target group mostra stato di salute di entrambe le istanze
- [x] Stop istanza → esclusione automatica, ALB serve via `demo-web-01`
- [ ] Cleanup completo (ALB, target group, istanze, AMI, snapshot) eseguito o giustificato

## Cleanup
- ALB e target group eliminati: sì/no
- Istanze terminate: sì/no
- AMI deregistrata (`deregister-image`) e snapshot eliminati: sì/no
- Se si prosegue con Lab 03: AMI, snapshot, ALB, target group conservati; riuso documentato, consumo crediti verificato

## Nota metodologica
Valori (ID AMI, ID istanze, DNS ALB) illustrativi, coerenti con doc ufficiale EC2/ELB. Sostituire con valori reali osservati nel Learner Lab. Se Learner Lab non raggiungibile: fallback, nessuna risorsa reale creata.