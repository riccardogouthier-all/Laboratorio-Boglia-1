# Deliverable Lab 03 - Auto Scaling Group e Monitoraggio con CloudWatch

## Configurazione
- Launch template: `demo-lt-web` (v1) — AMI `demo-web-ami-v1`, `t3.micro`, key pair `demo-key`, Security Group `demo-sg-web`
- Auto Scaling Group: `demo-asg-web` — minimo=1, desiderato=2, massimo=3
- Subnet: le due subnet pubbliche in AZ diverse già usate da `demo-alb`
- Target group collegato: `demo-tg-web` (health check tipo ELB, grace period 300 s)
- Scaling policy: `demo-cpu-target` — target tracking, CPU media gruppo, target 70%
- Allarme CloudWatch: `demo-cpu-alta` — `AWS/EC2` `CPUUtilization`, Average, periodo 5 min, soglia > 70, 1 punto su 1

## Motivazione scelte
- `minimo=1`: servizio mai a zero istanze in scale-in
- `desiderato=2` su 2 AZ: resilienza a guasto singola istanza/AZ
- `massimo=3`: tetto consumo crediti Learner Lab
- Health check ELB: ASG sostituisce istanze non sane per l'applicazione, non solo per status check EC2
- Soglia 70%: margine prima della saturazione, evita scaling su carichi normali
- `demo-cpu-alta` = allarme manuale di osservazione su singola istanza, non attiva `demo-cpu-target` (la policy gestisce propri allarmi)

## Verifica prerequisiti (CLI)
```bash
aws ec2 describe-images --image-ids $AMI_ID --query "Images[0].State" --output text
aws elbv2 describe-target-groups --names demo-tg-web --query "TargetGroups[0].TargetGroupArn" --output text
```
Output atteso: `available` + ARN di `demo-tg-web`.

## Verifica ASG e target group (CLI)
```bash
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names demo-asg-web \
  --query "AutoScalingGroups[0].Instances[].[InstanceId,LifecycleState,HealthStatus]" --output table
aws elbv2 describe-target-health --target-group-arn $TG_ARN \
  --query "TargetHealthDescriptions[].[Target.Id,TargetHealth.State]" --output table
```
Output atteso (illustrativo):
```
|  i-0asg0001  |  InService  |  Healthy  |
|  i-0asg0002  |  InService  |  Healthy  |
```
Target group: 2 istanze gestite `healthy`. Istanze originali Lab 02: non nell'ASG → deregistrate dopo verifica:
```bash
aws elbv2 deregister-targets --target-group-arn $TG_ARN --targets Id=<i-originale1> Id=<i-originale2>
```

## Verifica allarme (CLI)
```bash
aws cloudwatch describe-alarms --alarm-names demo-cpu-alta \
  --query "MetricAlarms[].{Name:AlarmName,State:StateValue,Threshold:Threshold}"
```
Output atteso:
```
[{"Name": "demo-cpu-alta", "State": "OK", "Threshold": 70.0}]
```
Se `INSUFFICIENT_DATA`: attendere primo datapoint (5 min).

## Evidenza sostituzione automatica
```bash
aws ec2 terminate-instances --instance-ids $INST2
aws autoscaling describe-scaling-activities --auto-scaling-group-name demo-asg-web --max-items 3
```
Output atteso (illustrativo):
```
"Description": "Launching a new EC2 instance: i-0newinstance",
"StatusCode": "Successful"
```
- Istanza terminata manualmente: `<i-...>`
- Istanza sostitutiva da ASG: `<i-...>`, tempo osservato: `<mm:ss>`
- Stato nel target group: `healthy`
- `desiderato` invariato a 2 durante la prova

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | Launch template | `demo-lt-web`: AMI `demo-web-ami-v1`, `t3.micro`, key `demo-key` |
| 2 | Auto Scaling Group | `demo-asg-web`: 1/2/3, target group `demo-tg-web`, health check ELB |
| 3 | Scaling policy | `demo-cpu-target`, CPU media 70% |
| 4 | Allarme CloudWatch | `demo-cpu-alta`, CPUUtilization, Average, 5 min, soglia 70 |
| 5 | Sostituzione automatica | istanza terminata → nuova `InService` + `healthy` (tab Activity) |

## Checkpoint
- [x] Min/desiderato/max coerenti con servizio sempre disponibile (min ≥ 1)
- [x] Allarme con soglia e periodo motivati
- [x] Terminazione istanza gestita → sostituta automatica registrata e sana
- [ ] Cleanup (ASG, launch template, allarme) eseguito o giustificato

## Cleanup
- ASG eliminato (termina istanze gestite): sì/no
- Launch template eliminato: sì/no
- Allarme `demo-cpu-alta` eliminato: sì/no
- Fine sequenza 01–03: ALB, target group, AMI (`deregister-image`) + snapshot eliminati: sì/no — oppure conservati per giustificazione: `<motivo>`
- Istanze originali Lab 02: fermate/terminate: sì/no

## Nota metodologica
ID istanza, tempi e timestamp illustrativi, da sostituire con valori osservati nel Learner Lab. Nome ASG uniformato a `demo-asg-web` (nello script `0. Lab tutti.sh` compare anche `demo-asg-web-2` in creazione: usare un solo nome coerente nei comandi successivi).

Procedura di esecuzione in CLI Cloudshell:

```bash
# --- Passo 1 ---
AMI_ID=$(aws ec2 describe-images --owners self --filters Name=name,Values=demo-web-ami-v1 --query "Images[0].ImageId" --output text)
aws ec2 describe-images --image-ids $AMI_ID --query "Images[0].State" --output text   # atteso: available

TG_ARN=$(aws elbv2 describe-target-groups --names demo-tg-web --query "TargetGroups[0].TargetGroupArn" --output text)
SG_ID=$(aws ec2 describe-security-groups --filters Name=group-name,Values=demo-sg-web --query "SecurityGroups[0].GroupId" --output text)
SUBNETS=$(aws elbv2 describe-load-balancers --names demo-alb --query "LoadBalancers[0].AvailabilityZones[].SubnetId" --output text | tr '\t' ',')
echo $AMI_ID $TG_ARN $SG_ID $SUBNETS

# --- Passo 2 ---
aws ec2 create-launch-template --launch-template-name demo-lt-web --version-description v1 --launch-template-data "{\"ImageId\":\"$AMI_ID\",\"InstanceType\":\"t3.micro\",\"KeyName\":\"demo-key\",\"SecurityGroupIds\":[\"$SG_ID\"]}"

# --- Passo 3 ---
aws autoscaling create-auto-scaling-group --auto-scaling-group-name demo-asg-web-2 --launch-template 'LaunchTemplateName=demo-lt-web,Version=$Latest' --min-size 1 --desired-capacity 2 --max-size 3 --vpc-zone-identifier "$SUBNETS" --target-group-arns "$TG_ARN" --health-check-type ELB --health-check-grace-period 300

# --- Passo 4 ---
aws autoscaling put-scaling-policy --auto-scaling-group-name demo-asg-web-2 --policy-name demo-cpu-target --policy-type TargetTrackingScaling --target-tracking-configuration '{"PredefinedMetricSpecification":{"PredefinedMetricType":"ASGAverageCPUUtilization"},"TargetValue":70.0}'

# --- Passo 5 ---
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names demo-asg-web-2 --query "AutoScalingGroups[0].Instances[].[InstanceId,LifecycleState,HealthStatus]" --output table

aws elbv2 describe-target-health --target-group-arn $TG_ARN --query "TargetHealthDescriptions[].[Target.Id,TargetHealth.State]" --output table

# Ripeti finché 2 InService + healthy. Istanze originali Lab 02 nel target group: non nell’ASG. Dopo verifica, deregistra:
aws elbv2 deregister-targets --target-group-arn $TG_ARN --targets Id=i-ORIGINALE1 Id=i-ORIGINALE2

# --- Passo 6 ---
IDS=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names demo-asg-web --query "AutoScalingGroups[0].Instances[].InstanceId" --output text)
INST1=$(echo $IDS | awk '{print $1}'); INST2=$(echo $IDS | awk '{print $2}')

aws cloudwatch put-metric-alarm --alarm-name demo-cpu-alta --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=$INST1 --statistic Average --period 300 --evaluation-periods 1 --datapoints-to-alarm 1 --threshold 70 --comparison-operator GreaterThanThreshold

aws cloudwatch describe-alarms --alarm-names demo-cpu-alta --query "MetricAlarms[].{Name:AlarmName,State:StateValue,Threshold:Threshold}"

# --- Passo 7 ---
aws ec2 terminate-instances --instance-ids $INST2

aws autoscaling describe-scaling-activities --auto-scaling-group-name demo-asg-web --max-items 3
```

### Cleanup

```bash
# Cleanup: eliminare l'ASG (termina le istanze), la launch template e l'allarme
aws autoscaling delete-auto-scaling-group --auto-scaling-group-name demo-asg-web-2 --force-delete
aws ec2 delete-launch-template --launch-template-name demo-lt-web
aws cloudwatch delete-alarms --alarm-names demo-cpu-alta
```
