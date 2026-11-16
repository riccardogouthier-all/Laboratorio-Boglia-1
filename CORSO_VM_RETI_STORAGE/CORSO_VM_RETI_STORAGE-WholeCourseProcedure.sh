#!/bin/bash
# VM, Reti e Storage AWS - procedura completa dei laboratori 1-11 da eseguire in AWS CloudShell (us-east-1).
# I blocchi di cleanup sono commentati: i laboratori successivi riusano le risorse. Decommentarli solo a fine corso.
# Lo script e pensato per essere eseguito per sezioni (lab per lab) leggendo l'output, non come unico lancio cieco.


#==============================================================================
# LABORATORIO 1 - Deliverable Lab 01 - Istanze EC2
#==============================================================================
cd "$HOME"
# --- Passo 0 ---
export AWS_DEFAULT_REGION=us-east-1
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
read SUB1 SUB2 <<< $(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID Name=default-for-az,Values=true --query "sort_by(Subnets,&AvailabilityZone)[0:2].SubnetId" --output text)
echo $VPC_ID $SUB1 $SUB2

# --- Passo 1 ---
aws ec2 create-key-pair --key-name demo-key --query KeyMaterial --output text > demo-key.pem
chmod 400 demo-key.pem

# --- Passo 2 ---
SG_ID=$(aws ec2 create-security-group --group-name demo-sg-web --description "demo web" --vpc-id $VPC_ID --query GroupId --output text)
MYIP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr $MYIP/32
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0

# --- Passo 3 ---
BASE_AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text)

cat > ud01.sh <<'EOF'
#!/bin/bash
dnf install -y httpd
echo 'Servizio web del laboratorio AWS' > /var/www/html/index.html
systemctl enable --now httpd
EOF

ID1=$(aws ec2 run-instances --image-id $BASE_AMI --instance-type t3.micro --key-name demo-key --security-group-ids $SG_ID --subnet-id $SUB1 --user-data file://ud01.sh --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=8,VolumeType=gp3}' --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=demo-web-01}]' --query "Instances[0].InstanceId" --output text)
aws ec2 wait instance-status-ok --instance-ids $ID1

IP1=$(aws ec2 describe-instances --instance-ids $ID1 --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
sleep 30; curl -sI http://$IP1/ | head -1

# --- Cleanup ---
# (cleanup, commentato)
# aws ec2 terminate-instances --instance-ids $ID1     # solo se l'istanza non serve ai lab successivi

#==============================================================================
# LABORATORIO 2 - Deliverable Lab 02 - Gestione Immagini AMI ed Elastic Load Balancing
#==============================================================================
cd "$HOME"
# Se la sessione CloudShell e nuova, ricostruire le variabili del Lab 01
export AWS_DEFAULT_REGION=us-east-1
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
read SUB1 SUB2 <<< $(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID Name=default-for-az,Values=true --query "sort_by(Subnets,&AvailabilityZone)[0:2].SubnetId" --output text)
SG_ID=$(aws ec2 describe-security-groups --filters Name=group-name,Values=demo-sg-web --query "SecurityGroups[0].GroupId" --output text)
ID1=$(aws ec2 describe-instances --filters Name=tag:Name,Values=demo-web-01 Name=instance-state-name,Values=running,stopped --query "Reservations[0].Instances[0].InstanceId" --output text)

# --- Passo 4 ---
aws ec2 stop-instances --instance-ids $ID1
aws ec2 wait instance-stopped --instance-ids $ID1
AMI_ID=$(aws ec2 create-image --instance-id $ID1 --name demo-web-ami-v1 --description "AL2023 httpd" --query ImageId --output text)
aws ec2 wait image-available --image-ids $AMI_ID
aws ec2 start-instances --instance-ids $ID1
aws ec2 wait instance-running --instance-ids $ID1
echo $AMI_ID

# --- Passo 5 ---
cat > ud02.sh <<'EOF'
#!/bin/bash
hostname > /var/www/html/index.html
EOF

ID2=$(aws ec2 run-instances --image-id $AMI_ID --instance-type t3.micro --key-name demo-key --security-group-ids $SG_ID --subnet-id $SUB2 --user-data file://ud02.sh --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=demo-web-02}]' --query "Instances[0].InstanceId" --output text)
aws ec2 wait instance-status-ok --instance-ids $ID2

# --- Passo 6 ---
TG_ARN=$(aws elbv2 create-target-group --name demo-tg-web --protocol HTTP --port 80 --vpc-id $VPC_ID --target-type instance --health-check-path / --query "TargetGroups[0].TargetGroupArn" --output text)
aws elbv2 register-targets --target-group-arn $TG_ARN --targets Id=$ID1 Id=$ID2

# --- Passo 7 ---
ALB_ARN=$(aws elbv2 create-load-balancer --name demo-alb --type application --scheme internet-facing --subnets $SUB1 $SUB2 --security-groups $SG_ID --query "LoadBalancers[0].LoadBalancerArn" --output text)
aws elbv2 wait load-balancer-available --load-balancer-arns $ALB_ARN
aws elbv2 create-listener --load-balancer-arn $ALB_ARN --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=$TG_ARN

# --- Passo 8 ---
aws elbv2 describe-target-health --target-group-arn $TG_ARN --query "TargetHealthDescriptions[].[Target.Id,TargetHealth.State]" --output table
DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query "LoadBalancers[0].DNSName" --output text)
curl -s http://$DNS/

# --- Cleanup ---
# (cleanup, commentato)
# # Cleanup a fine percorso (ordine: listener/ALB, target group, istanze, AMI e snapshot, key pair, SG)
# aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
# aws elbv2 delete-target-group --target-group-arn $TG_ARN
# aws ec2 terminate-instances --instance-ids $ID1 $ID2
# aws ec2 deregister-image --image-id $AMI_ID
# aws ec2 delete-key-pair --key-name demo-key
# aws ec2 delete-security-group --group-id $SG_ID

#==============================================================================
# LABORATORIO 3 - Deliverable Lab 03 - Auto Scaling Group e Monitoraggio con CloudWatch
#==============================================================================
cd "$HOME"
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

# --- Cleanup ---
# (cleanup, commentato)
# # Cleanup: eliminare l'ASG (termina le istanze), la launch template e l'allarme
# aws autoscaling delete-auto-scaling-group --auto-scaling-group-name demo-asg-web-2 --force-delete
# aws ec2 delete-launch-template --launch-template-name demo-lt-web
# aws cloudwatch delete-alarms --alarm-names demo-cpu-alta

#==============================================================================
# LABORATORIO 4 - Deliverable Lab 04 - Concetti Base di VPC e Subnet Pubbliche/Private
#==============================================================================
cd "$HOME"
# --- Passo 1 ---
export AWS_DEFAULT_REGION=us-east-1
VPC4=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --instance-tenancy default --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=demo-vpc}]' --query Vpc.VpcId --output text)
aws ec2 wait vpc-available --vpc-ids $VPC4
echo $VPC4

# --- Passo 2 ---
# Nome	                CIDR	        AZ  	        Tipo
# demo-vpc	            10.0.0.0/16	    -	            -
# demo-subnet-public-1a	10.0.1.0/24	    us-east-1a	    pubblica (pianificata)
# demo-subnet-private-1a	10.0.2.0/24	    us-east-1a	    privata

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

#==============================================================================
# LABORATORIO 5 - Deliverable Lab 05 - Routing, Internet Gateway, NAT Gateway e Bastion Host
#==============================================================================
cd "$HOME"
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
cat >> ~/.ssh/config <<EOF
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
EOF
chmod 600 ~/.ssh/config

ssh lab-bastion 'hostname'
ssh lab-private 'hostname; curl -sI https://aws.amazon.com | head -1'

# --- Passo 9 ---
# Rotte: pubblica 0.0.0.0/0 → demo-igw; privata 0.0.0.0/0 → demo-nat
# demo-sg-bastion: 22 da $MYIP/32; demo-sg-private: 22 da $SG_B
# Salto SSH + curl annotati

# --- Cleanup ---
# (cleanup, commentato)
# # Cleanup: NAT, EIP, istanze, route table, IGW, SG (ordine: dipendenze prima)
# aws ec2 terminate-instances --instance-ids $BID $PID && aws ec2 wait instance-terminated --instance-ids $BID $PID
# aws ec2 delete-nat-gateway --nat-gateway-id $NAT
# aws ec2 wait nat-gateway-deleted --nat-gateway-ids $NAT
# aws ec2 release-address --allocation-id $EIP
# aws ec2 delete-security-group --group-id $SG_P; aws ec2 delete-security-group --group-id $SG_B

#==============================================================================
# LABORATORIO 6 - Deliverable Lab 06 - Security Group, Network ACL e Architetture di Rete Sicure
#==============================================================================
cd "$HOME"
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

#==============================================================================
# LABORATORIO 7 - Deliverable Lab 07 - EBS, EFS, S3 e Gestione Volumi EBS
#==============================================================================
cd "$HOME"
R=us-east-1
ID=$ID2     # istanza demo-web-02 creata al Lab 02

AZ=$(aws ec2 describe-instances --instance-ids $ID --region $R \
  --query "Reservations[0].Instances[0].Placement.AvailabilityZone" --output text)
echo $AZ

VOL=$(aws ec2 create-volume --availability-zone $AZ --volume-type gp3 --size 10 \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=demo-data-vol}]' \
  --query VolumeId --output text --region $R)
echo $VOL

aws ec2 wait volume-available --volume-ids $VOL --region $R
aws ec2 attach-volume --volume-id $VOL --instance-id $ID --device /dev/sdf --region $R
aws ec2 wait volume-in-use --volume-ids $VOL --region $R


# --- Dentro l'istanza (sessione SSH) ---  [da eseguire sull'istanza via SSH, non in CloudShell]

# lsblk -f                       # trova disco 10G senza FS (xvdf o nvme1n1)
# LAB_DATA_DEVICE=/dev/xvdf      # adatta al device reale
# sudo blkid "$LAB_DATA_DEVICE"  # vuoto = nessun output
# sudo mkfs -t ext4 "$LAB_DATA_DEVICE"   # solo se vuoto
# sudo mkdir -p /mnt/demo-data
# sudo mount "$LAB_DATA_DEVICE" /mnt/demo-data
# findmnt /mnt/demo-data
# echo "demo storage EBS" | sudo tee /mnt/demo-data/test.txt
# cat /mnt/demo-data/test.txt
# sync


# --- Di nuovo in CloudShell (snapshot e verifica) ---

SNAP=$(aws ec2 create-snapshot --volume-id $VOL --region $R \
  --description "backup volume dati del laboratorio" \
  --query SnapshotId --output text)
echo $SNAP

aws ec2 wait snapshot-completed --snapshot-ids $SNAP --region $R

aws ec2 describe-volumes --volume-ids $VOL --region $R \
  --query "Volumes[].{State:State,Size:Size,Type:VolumeType,AZ:AvailabilityZone}"
aws ec2 describe-snapshots --snapshot-ids $SNAP --region $R \
  --query "Snapshots[].{State:State,Progress:Progress}"

# --- Cleanup ---
# (cleanup, commentato)
# aws ec2 detach-volume --volume-id $VOL && aws ec2 wait volume-available --volume-ids $VOL
# aws ec2 delete-volume --volume-id $VOL
# aws ec2 delete-snapshot --snapshot-id $SNAP

#==============================================================================
# LABORATORIO 8 - Deliverable Lab 08 - S3: versioning e lifecycle
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
BUCKET=demo-vm-reti-storage-rg-2026

# Step 1 - Bucket con Block all public access
aws s3api create-bucket --bucket $BUCKET
aws s3api put-public-access-block --bucket $BUCKET --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Step 2 - Versioning Enabled
aws s3api put-bucket-versioning --bucket $BUCKET --versioning-configuration Status=Enabled
aws s3api get-bucket-versioning --bucket $BUCKET
sleep 15    # propagazione della prima abilitazione

# Step 3 - Prima versione di report.txt
echo "report v1 - contenuto originale" > report.txt
aws s3api put-object --bucket $BUCKET --key report.txt --body report.txt --query VersionId --output text

# Step 4 - Sovrascrittura: seconda versione
echo "report v2 - contenuto modificato dopo la sovrascrittura" > report.txt
aws s3api put-object --bucket $BUCKET --key report.txt --body report.txt --query VersionId --output text
aws s3api list-object-versions --bucket $BUCKET --prefix report.txt --query "Versions[].{VersionId:VersionId,IsLatest:IsLatest,Size:Size}"

# Versione precedente: scaricarla e confrontare il contenuto
V1=$(aws s3api list-object-versions --bucket $BUCKET --prefix report.txt --query "Versions[?IsLatest==\`false\`].VersionId | [0]" --output text)
aws s3api get-object --bucket $BUCKET --key report.txt --version-id $V1 report-v1.txt > /dev/null && cat report-v1.txt

# Step 5 - Lifecycle: versioni non correnti a Standard-IA dopo 30 giorni, ambito intero bucket
cat > lifecycle.json <<'EOF'
{
  "Rules": [
    {
      "ID": "demo-lifecycle-standard-ia",
      "Status": "Enabled",
      "Filter": {},
      "NoncurrentVersionTransitions": [
        {"NoncurrentDays": 30, "StorageClass": "STANDARD_IA"}
      ]
    }
  ]
}
EOF
aws s3api put-bucket-lifecycle-configuration --bucket $BUCKET --lifecycle-configuration file://lifecycle.json
aws s3api get-bucket-lifecycle-configuration --bucket $BUCKET

# Step 6 - Eliminazione semplice: crea un delete marker, le versioni restano
aws s3api delete-object --bucket $BUCKET --key report.txt
aws s3api list-object-versions --bucket $BUCKET --prefix report.txt --query "{Versions:Versions[].VersionId,DeleteMarkers:DeleteMarkers[].VersionId}"
aws s3 ls s3://$BUCKET/        # report.txt non compare piu nella vista normale

# Step 7 - Recupero: rimuovere solo il delete marker
DM=$(aws s3api list-object-versions --bucket $BUCKET --prefix report.txt --query "DeleteMarkers[?IsLatest==\`true\`].VersionId | [0]" --output text)
aws s3api delete-object --bucket $BUCKET --key report.txt --version-id $DM
aws s3 cp s3://$BUCKET/report.txt - 

#==============================================================================
# LABORATORIO 9 - Deliverable Lab 09 - Storage Gateway e cifratura a riposo
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
BUCKET=demo-vm-reti-storage-rg-2026      # bucket del Lab 08

# Steps 1-2 - Storage Gateway: solo esame dei tipi (nessun gateway creato).
# S3 File Gateway = NFS/SMB | Volume Gateway = iSCSI | Tape Gateway = nastri virtuali (app di backup)

# Step 3 - Volume EBS cifrato gp3 10 GiB in us-east-1a, chiave aws/ebs
VOL=$(aws ec2 create-volume --availability-zone us-east-1a --volume-type gp3 --size 10 --encrypted \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=demo-encrypted-vol}]' \
  --query VolumeId --output text)
aws ec2 wait volume-available --volume-ids $VOL
aws ec2 describe-volumes --volume-ids $VOL --query "Volumes[].{Encrypted:Encrypted,KmsKeyId:KmsKeyId,State:State,Size:Size,Type:VolumeType}"

# Steps 4-5 - Bucket del Lab 08: cifratura di default SSE-S3 (AES256)
aws s3api put-bucket-encryption --bucket $BUCKET --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api get-bucket-encryption --bucket $BUCKET

# Step 6 - Oggetto di prova e verifica della cifratura
echo "prova di cifratura a riposo" > test-cifratura.txt
aws s3api put-object --bucket $BUCKET --key test-cifratura.txt --body test-cifratura.txt
aws s3api head-object --bucket $BUCKET --key test-cifratura.txt --query ServerSideEncryption

# --- Cleanup (se il volume non serve piu) ---
# (cleanup, commentato)
# aws ec2 delete-volume --volume-id $VOL
# aws s3api delete-object --bucket $BUCKET --key test-cifratura.txt

#==============================================================================
# LABORATORIO 10 - Deliverable Lab 10 - EBS vs EFS: storage condiviso tra istanze
#==============================================================================
cd "$HOME"
export AWS_DEFAULT_REGION=us-east-1
VPC=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=demo-vpc --query "Vpcs[0].VpcId" --output text)
SUB_A=$(aws ec2 describe-subnets --filters Name=tag:Name,Values=demo-subnet-public-1a --query "Subnets[0].SubnetId" --output text)
RT_PUB=$(aws ec2 describe-route-tables --filters Name=tag:Name,Values=demo-rt-public --query "RouteTables[0].RouteTableId" --output text)

# Step 3 (parte DNS) - DNS resolution e DNS hostnames abilitati
aws ec2 modify-vpc-attribute --vpc-id $VPC --enable-dns-support '{"Value":true}'
aws ec2 modify-vpc-attribute --vpc-id $VPC --enable-dns-hostnames '{"Value":true}'

# Step 1 - Seconda subnet pubblica in us-east-1b e due istanze Amazon Linux 2023 (indipendenti da ASG)
SUB_B=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.0.4.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=demo-subnet-public-1b}]' --query Subnet.SubnetId --output text)
aws ec2 modify-subnet-attribute --subnet-id $SUB_B --map-public-ip-on-launch
aws ec2 associate-route-table --route-table-id $RT_PUB --subnet-id $SUB_B
aws ec2 modify-subnet-attribute --subnet-id $SUB_A --map-public-ip-on-launch

SG_I=$(aws ec2 create-security-group --group-name demo-sg-instances --description "demo istanze applicative" --vpc-id $VPC --query GroupId --output text)
BASE_AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text)
mk() { aws ec2 run-instances --image-id $BASE_AMI --instance-type t3.micro --subnet-id $2 --security-group-ids $SG_I --iam-instance-profile Name=LabInstanceProfile --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$1}]" --query "Instances[0].InstanceId" --output text; }
ID1=$(mk demo-web-01 $SUB_A)
ID2=$(mk demo-web-02 $SUB_B)
aws ec2 wait instance-status-ok --instance-ids $ID1 $ID2
echo $ID1 $ID2

# Step 2 - Volumi EBS dedicati gp3 10 GiB, uno per istanza, nella rispettiva AZ
V1=$(aws ec2 create-volume --availability-zone us-east-1a --volume-type gp3 --size 10 --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=demo-data-vol}]' --query VolumeId --output text)
V2=$(aws ec2 create-volume --availability-zone us-east-1b --volume-type gp3 --size 10 --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=demo-data-vol-02}]' --query VolumeId --output text)
aws ec2 wait volume-available --volume-ids $V1 $V2
aws ec2 attach-volume --volume-id $V1 --instance-id $ID1 --device /dev/sdf
aws ec2 attach-volume --volume-id $V2 --instance-id $ID2 --device /dev/sdf
aws ec2 wait volume-in-use --volume-ids $V1 $V2

# Formattazione xfs e mount su /mnt/demo-data (via SSM, nessuna chiave SSH necessaria)
DATA_CMDS='["sudo mkfs -t xfs /dev/nvme1n1","sudo mkdir -p /mnt/demo-data","sudo mount /dev/nvme1n1 /mnt/demo-data","df -h /mnt/demo-data"]'
aws ssm send-command --instance-ids $ID1 $ID2 --document-name AWS-RunShellScript --parameters "commands=$DATA_CMDS"

# Step 3 - Security Group EFS: NFS 2049 solo dal SG delle istanze
SG_E=$(aws ec2 create-security-group --group-name demo-sg-efs --description "demo EFS" --vpc-id $VPC --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_E --protocol tcp --port 2049 --source-group $SG_I

# Step 4 - File system EFS Regional, General Purpose
EFS=$(aws efs create-file-system --performance-mode generalPurpose --tags Key=Name,Value=demo-efs-shared --query FileSystemId --output text)
until [ "$(aws efs describe-file-systems --file-system-id $EFS --query 'FileSystems[0].LifeCycleState' --output text)" = available ]; do sleep 5; done
echo $EFS

# Step 5 - Mount target nelle due AZ con demo-sg-efs
aws efs create-mount-target --file-system-id $EFS --subnet-id $SUB_A --security-groups $SG_E
aws efs create-mount-target --file-system-id $EFS --subnet-id $SUB_B --security-groups $SG_E
until [ "$(aws efs describe-mount-targets --file-system-id $EFS --query 'length(MountTargets[?LifeCycleState==`available`])' --output text)" = 2 ]; do sleep 10; done
aws efs describe-mount-targets --file-system-id $EFS --query "MountTargets[].[AvailabilityZoneName,IpAddress,LifeCycleState]" --output table

# Step 6 - Mount EFS su entrambe le istanze (via SSM)
MNT="[\"sudo dnf install -y amazon-efs-utils\",\"sudo mkdir -p /mnt/efs-shared\",\"sudo mount -t efs -o tls $EFS:/ /mnt/efs-shared\",\"findmnt --mountpoint /mnt/efs-shared\"]"
aws ssm send-command --instance-ids $ID1 $ID2 --document-name AWS-RunShellScript --parameters "commands=$MNT"

# Step 7 - Prova di condivisione: scrive su web-01, legge su web-02
run() { CID=$(aws ssm send-command --instance-ids $1 --document-name AWS-RunShellScript --parameters "commands=[\"$2\"]" --query Command.CommandId --output text); sleep 6; aws ssm get-command-invocation --command-id $CID --instance-id $1 --query StandardOutputContent --output text; }
run $ID1 "findmnt --mountpoint /mnt/efs-shared && echo 'scritto dalla istanza 1' | sudo tee /mnt/efs-shared/condiviso.txt"
run $ID2 "findmnt --mountpoint /mnt/efs-shared && cat /mnt/efs-shared/condiviso.txt"

# Step 8 - Contrasto: i volumi EBS restano separati (su web-02 /mnt/demo-data non contiene i dati di web-01)
run $ID2 "ls -la /mnt/demo-data"

#==============================================================================
# LABORATORIO 11 - Deliverable Lab 11 - Architettura multi-tier e connettivita ibrida
#==============================================================================
cd "$HOME"
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

# --- Cleanup finale (Lab 8-11) ---
# (cleanup, commentato)
# # S3: svuotare tutte le versioni e i delete marker, poi eliminare il bucket
# BUCKET=demo-vm-reti-storage-rg-2026
# aws s3api list-object-versions --bucket $BUCKET --query "Versions[].[Key,VersionId]" --output text | while read K V; do aws s3api delete-object --bucket $BUCKET --key "$K" --version-id "$V" > /dev/null; done
# aws s3api list-object-versions --bucket $BUCKET --query "DeleteMarkers[].[Key,VersionId]" --output text | while read K V; do aws s3api delete-object --bucket $BUCKET --key "$K" --version-id "$V" > /dev/null; done
# aws s3api delete-bucket --bucket $BUCKET
#
# # Istanze, volumi, EFS (ID dei Lab 09-10: ID1 ID2 V1 V2 VOL EFS SG_I SG_E)
# aws ec2 terminate-instances --instance-ids $ID1 $ID2 && aws ec2 wait instance-terminated --instance-ids $ID1 $ID2
# for M in $(aws efs describe-mount-targets --file-system-id $EFS --query "MountTargets[].MountTargetId" --output text); do aws efs delete-mount-target --mount-target-id $M; done
# sleep 60
# aws efs delete-file-system --file-system-id $EFS
# aws ec2 delete-volume --volume-id $V1; aws ec2 delete-volume --volume-id $V2; aws ec2 delete-volume --volume-id $VOL
#
# # Rete: SG, subnet, VGW e VPC
# for G in $SG_E $SG_I $SG_DB $SG_APP $SG_WEB $SG_ALB; do aws ec2 delete-security-group --group-id $G; done
# aws ec2 detach-vpn-gateway --vpn-gateway-id $VGW --vpc-id $VPC
# sleep 30
# aws ec2 delete-vpn-gateway --vpn-gateway-id $VGW
# # Subnet/route table/IGW/VPC: usare la procedura di cleanup dei Lab 04-06 (NAT, IGW, route table, subnet, VPC demo-vpc)
