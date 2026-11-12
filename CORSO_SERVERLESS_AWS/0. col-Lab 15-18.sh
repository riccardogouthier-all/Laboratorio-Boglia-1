Lab 15
export AWS_DEFAULT_REGION=us-east-1

aws dynamodb create-table --table-name lab15-sessions --attribute-definitions AttributeName=session_id,AttributeType=S --key-schema AttributeName=session_id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab15-sessions
aws dynamodb describe-table --table-name lab15-sessions --query "Table.[TableName,TableStatus,KeySchema]" --output json

aws dynamodb update-time-to-live --table-name lab15-sessions --time-to-live-specification Enabled=true,AttributeName=expires_at
aws dynamodb describe-time-to-live --table-name lab15-sessions

cat > lambda_function.py <<'EOF'
import json
import time
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('lab15-sessions')

def lambda_handler(event, context):
    now = int(time.time())

    sessions = [
        {'session_id': 'sess-001', 'user_id': 'alice', 'created_at': now, 'expires_at': now + 60},
        {'session_id': 'sess-002', 'user_id': 'bob', 'created_at': now, 'expires_at': now + 3600},
        {'session_id': 'sess-003', 'user_id': 'charlie', 'created_at': now, 'expires_at': now + 86400}
    ]

    for session in sessions:
        table.put_item(Item=session)
        print(f"Created session {session['session_id']}, expires in {session['expires_at'] - now}s")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Created {len(sessions)} sessions',
            'current_epoch': now
        })
    }
EOF
zip function.zip lambda_function.py

ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
aws lambda create-function --function-name insert-sessions --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip
aws lambda wait function-active-v2 --function-name insert-sessions

aws lambda invoke --function-name insert-sessions out.json
cat out.json

date +%s
aws dynamodb scan --table-name lab15-sessions --query "Items[].[session_id.S,user_id.S,expires_at.N]" --output table

date +%s
aws dynamodb scan --table-name lab15-sessions --query "Items[].[session_id.S,expires_at.N]" --output table

BK_ARN=$(aws dynamodb create-backup --table-name lab15-sessions --backup-name sessions-backup-test --query BackupDetails.BackupArn --output text)
echo $BK_ARN
aws dynamodb describe-backup --backup-arn $BK_ARN --query "BackupDescription.BackupDetails.[BackupName,BackupStatus,BackupType]" --output text

aws dynamodb update-continuous-backups --table-name lab15-sessions --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
aws dynamodb describe-continuous-backups --table-name lab15-sessions --query "ContinuousBackupsDescription.PointInTimeRecoveryDescription"

NOME=riccardogouthier
BUCKET=lab15-lifecycle-$NOME
aws s3api create-bucket --bucket $BUCKET
echo "file di test 1" > test1.txt; echo "file di test 2" > test2.txt
aws s3 cp test1.txt s3://$BUCKET/
aws s3 cp test2.txt s3://$BUCKET/
aws s3 ls s3://$BUCKET/

cat > lifecycle.json <<'EOF'
{
  "Rules": [
    {
      "ID": "archive-old-files",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"}
      ],
      "Expiration": {"Days": 365}
    }
  ]
}
EOF
aws s3api put-bucket-lifecycle-configuration --bucket $BUCKET --lifecycle-configuration file://lifecycle.json
aws s3api get-bucket-lifecycle-configuration --bucket $BUCKET



Lab 16
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
echo $ROLE_ARN

mkdir -p lab16 && cd lab16

cat > validate.py <<'EOF'
import json

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)

    if total <= 0:
        raise ValueError(f"Invalid order total: {total}")

    return {
        'order_id': order_id,
        'total': total,
        'status': 'validated'
    }
EOF

cat > discount.py <<'EOF'
import json

def lambda_handler(event, context):
    total = event['total']
    discount = total * 0.1  # 10% discount
    new_total = round(total - discount, 2)

    return {
        'order_id': event['order_id'],
        'original_total': total,
        'discount': round(discount, 2),
        'total': new_total,
        'status': 'discounted'
    }
EOF

cat > confirm.py <<'EOF'
import json

def lambda_handler(event, context):
    return {
        'order_id': event['order_id'],
        'total': event['total'],
        'status': 'confirmed',
        'message': f"Order {event['order_id']} confirmed. Total: {event['total']} EUR"
    }
EOF

for p in "validate validate-order" "discount apply-discount" "confirm confirm-order"; do
  set -- $p
  cp $1.py lambda_function.py
  zip -q $1.zip lambda_function.py
  aws lambda create-function --function-name $2 --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://$1.zip --query "[FunctionName,Runtime,State]" --output text
  aws lambda wait function-active-v2 --function-name $2
done
cd ..
aws lambda list-functions --query "Functions[?starts_with(FunctionName,'validate-')||starts_with(FunctionName,'apply-')||starts_with(FunctionName,'confirm-')].[FunctionName,Runtime]" --output table

REGION=us-east-1
ACC=$(aws sts get-caller-identity --query Account --output text)
VAL=arn:aws:lambda:$REGION:$ACC:function:validate-order
DIS=arn:aws:lambda:$REGION:$ACC:function:apply-discount
CON=arn:aws:lambda:$REGION:$ACC:function:confirm-order

cat > order-processor.asl.json <<EOF
{
  "Comment": "Order processor",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$VAL", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "CheckAmount"
    },
    "CheckAmount": {
      "Type": "Choice",
      "Choices": [
        {"Variable": "\$.total", "NumericGreaterThan": 100, "Next": "ApplyDiscount"}
      ],
      "Default": "ConfirmOrder"
    },
    "ApplyDiscount": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$DIS", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "ConfirmOrder"
    },
    "ConfirmOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$CON", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "Success"
    },
    "Success": {"Type": "Succeed"}
  }
}
EOF

SM_ARN=$(aws stepfunctions create-state-machine --name order-processor --definition file://order-processor.asl.json --role-arn $ROLE_ARN --type STANDARD --query stateMachineArn --output text)
echo $SM_ARN
aws stepfunctions describe-state-machine --state-machine-arn $SM_ARN --query "[name,status,type]" --output text

EX1=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-001 --input '{"order_id":"ORD-001","total":50}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX1 --query "[status,output]" --output text

aws stepfunctions get-execution-history --execution-arn $EX1 --query "events[?type=='TaskStateEntered'||type=='ChoiceStateEntered'].[id,type,stateEnteredEventDetails.name]" --output table

EX2=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-002 --input '{"order_id":"ORD-002","total":200}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX2 --query "[status,output]" --output text
aws stepfunctions get-execution-history --execution-arn $EX2 --query "events[?type=='TaskStateEntered'||type=='ChoiceStateEntered'].[id,type,stateEnteredEventDetails.name]" --output table

EX3=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-003 --input '{"order_id":"ORD-003","total":-10}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX3 --query "[status,error,cause]" --output text



Lab 17


Lab 18


