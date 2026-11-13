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
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
echo $ROLE_ARN $ACC

mkdir -p lab17 && cd lab17

cat > validate.py <<'EOF'
import json

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)
    simulate_error = event.get('simulate_error', False)

    if total <= 0:
        raise ValueError(f"Invalid total: {total}")

    return {
        'order_id': order_id,
        'total': total,
        'status': 'validated',
        'simulate_error': simulate_error
    }
EOF

cat > payment.py <<'EOF'
import json
import random

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)
    simulate_error = event.get('simulate_error', False)

    # Simulate transient failure (50% chance if simulate_error is True)
    if simulate_error and random.random() < 0.5:
        raise RuntimeError(f"Payment service temporarily unavailable for order {order_id}")

    return {
        'order_id': order_id,
        'total': total,
        'payment_id': f'PAY-{order_id}',
        'status': 'paid'
    }
EOF

cat > failure.py <<'EOF'
import json

def lambda_handler(event, context):
    error = event.get('error', {})
    order_id = event.get('order_id', 'unknown')

    print(f"FAILURE HANDLER: Order {order_id}")
    print(f"Error: {json.dumps(error)}")

    return {
        'order_id': order_id,
        'status': 'failed',
        'error_handled': True,
        'message': f'Order {order_id} failed and has been logged for review'
    }
EOF

for p in "validate validate-order-v2" "payment process-payment" "failure handle-failure"; do
  set -- $p
  cp $1.py lambda_function.py
  zip -q $1.zip lambda_function.py
  aws lambda create-function --function-name $2 --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://$1.zip --query "[FunctionName,Runtime]" --output text
  aws lambda wait function-active-v2 --function-name $2
done
cd ..
aws lambda list-functions --query "Functions[?FunctionName=='validate-order-v2'||FunctionName=='process-payment'||FunctionName=='handle-failure'].[FunctionName,Runtime]" --output table

cat > order-v2.asl.json <<'EOF'
{
  "Comment": "Order processing with error handling",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:validate-order-v2",
      "Catch": [
        {"ErrorEquals": ["States.ALL"], "ResultPath": "$.error", "Next": "HandleFailure"}
      ],
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:process-payment",
      "Retry": [
        {"ErrorEquals": ["RuntimeError"], "IntervalSeconds": 2, "MaxAttempts": 3, "BackoffRate": 2.0}
      ],
      "Catch": [
        {"ErrorEquals": ["States.ALL"], "ResultPath": "$.error", "Next": "HandleFailure"}
      ],
      "Next": "OrderConfirmed"
    },
    "OrderConfirmed": {"Type": "Succeed"},
    "HandleFailure": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:handle-failure",
      "Next": "OrderFailed"
    },
    "OrderFailed": {
      "Type": "Fail",
      "Error": "OrderProcessingFailed",
      "Cause": "The order could not be processed after all retry attempts"
    }
  }
}
EOF
sed -i "s/ACCOUNT_ID/$ACC/g" order-v2.asl.json

SM2=$(aws stepfunctions create-state-machine --name order-processor-v2 --definition file://order-v2.asl.json --role-arn $ROLE_ARN --type STANDARD --query stateMachineArn --output text)
echo $SM2
aws stepfunctions describe-state-machine --state-machine-arn $SM2 --query "[name,status,type]" --output text

EX1=$(aws stepfunctions start-execution --state-machine-arn $SM2 --name exec-ord-100 --input '{"order_id":"ORD-100","total":150,"simulate_error":false}' --query executionArn --output text)
sleep 6
aws stepfunctions describe-execution --execution-arn $EX1 --query "[status,output]" --output text

EX2=$(aws stepfunctions start-execution --state-machine-arn $SM2 --name exec-ord-200 --input '{"order_id":"ORD-200","total":200,"simulate_error":true}' --query executionArn --output text)
sleep 25
aws stepfunctions describe-execution --execution-arn $EX2 --query "[status,error]" --output text

for i in 1 2 3 4 5; do
  aws stepfunctions start-execution --state-machine-arn $SM2 --name exec-retry-$i --input "{\"order_id\":\"ORD-2$i\",\"total\":200,\"simulate_error\":true}" --query executionArn --output text
done
sleep 25
aws stepfunctions list-executions --state-machine-arn $SM2 --query "executions[].[name,status]" --output table

EX3=$(aws stepfunctions start-execution --state-machine-arn $SM2 --name exec-ord-300 --input '{"order_id":"ORD-300","total":-50}' --query executionArn --output text)
sleep 6
aws stepfunctions describe-execution --execution-arn $EX3 --query "[status,error,cause]" --output text
aws stepfunctions get-execution-history --execution-arn $EX3 --query "events[?type=='TaskStateEntered'||type=='FailStateEntered'].[id,type,stateEnteredEventDetails.name]" --output table

EXR=$(aws stepfunctions list-executions --state-machine-arn $SM2 --query "executions[0].executionArn" --output text)
aws stepfunctions get-execution-history --execution-arn $EXR --query "events[?type=='TaskScheduled'||type=='TaskFailed'||type=='TaskSucceeded'].[id,timestamp,type]" --output table

NOME=riccardogouthier
BUCKET=lab17-receipts-$NOME

aws dynamodb create-table --table-name lab17-orders --attribute-definitions AttributeName=order_id,AttributeType=S --key-schema AttributeName=order_id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab17-orders
aws s3api create-bucket --bucket $BUCKET
aws dynamodb describe-table --table-name lab17-orders --query "Table.TableStatus" --output text
aws s3 ls | grep lab17

cat > direct.asl.json <<'EOF'
{
  "Comment": "Direct SDK integration workflow",
  "StartAt": "SaveOrder",
  "States": {
    "SaveOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:putItem",
      "Parameters": {
        "TableName": "lab17-orders",
        "Item": {
          "order_id": { "S.$": "$.order_id" },
          "customer": { "S.$": "$.customer" },
          "total": { "N.$": "States.Format('{}', $.total)" },
          "status": { "S": "confirmed" }
        }
      },
      "ResultPath": "$.dynamoResult",
      "Next": "SaveReceipt"
    },
    "SaveReceipt": {
      "Type": "Task",
      "Resource": "arn:aws:states:::aws-sdk:s3:putObject",
      "Parameters": {
        "Bucket": "BUCKET_NAME",
        "Key.$": "States.Format('receipts/{}.json', $.order_id)",
        "Body": {
          "order_id.$": "$.order_id",
          "customer.$": "$.customer",
          "total.$": "$.total",
          "status": "confirmed"
        }
      },
      "ResultPath": "$.s3Result",
      "Next": "OrderComplete"
    },
    "OrderComplete": {"Type": "Succeed"}
  }
}
EOF
sed -i "s/BUCKET_NAME/$BUCKET/" direct.asl.json

aws logs create-log-group --log-group-name step-functions-lab17
LOG_ARN=$(aws logs describe-log-groups --log-group-name-prefix step-functions-lab17 --query "logGroups[0].arn" --output text)
echo $LOG_ARN

SM3=$(aws stepfunctions create-state-machine --name direct-integration-demo --definition file://direct.asl.json --role-arn $ROLE_ARN --type STANDARD --logging-configuration "{\"level\":\"ALL\",\"includeExecutionData\":true,\"destinations\":[{\"cloudWatchLogsLogGroup\":{\"logGroupArn\":\"$LOG_ARN\"}}]}" --query stateMachineArn --output text)
echo $SM3
aws stepfunctions describe-state-machine --state-machine-arn $SM3 --query "[name,status,loggingConfiguration.level]" --output text

EX4=$(aws stepfunctions start-execution --state-machine-arn $SM3 --name exec-ord-500 --input '{"order_id":"ORD-500","customer":"Alice","total":199.99}' --query executionArn --output text)
sleep 6
aws stepfunctions describe-execution --execution-arn $EX4 --query "[status,error,cause]" --output text

aws dynamodb get-item --table-name lab17-orders --key '{"order_id":{"S":"ORD-500"}}'
aws s3 ls s3://$BUCKET/receipts/
aws s3 cp s3://$BUCKET/receipts/ORD-500.json -

EX5=$(aws stepfunctions start-execution --state-machine-arn $SM3 --name exec-ord-501 --input '{"order_id":"ORD-501","customer":"Bob","total":49.99}' --query executionArn --output text)
sleep 6
aws stepfunctions describe-execution --execution-arn $EX5 --query "status" --output text
aws dynamodb scan --table-name lab17-orders --query "Items[].[order_id.S,customer.S,total.N]" --output table
aws s3 ls s3://$BUCKET/receipts/

aws logs filter-log-events --log-group-name step-functions-lab17 --max-items 30 --output json | jq -r '.events[].message | fromjson | [.type, (.details.name // "")] | @tsv'




Lab 18
export AWS_DEFAULT_REGION=us-east-1
ACC=$(aws sts get-caller-identity --query Account --output text)
sam --version
aws iam get-role --role-name LabRole --query Role.Arn --output text

cd ~
sam init --runtime python3.12 --name order-api --app-template hello-world --package-type Zip --dependency-manager pip --no-tracing --no-application-insights --no-interactive
cd order-api && ls

cat > template.yaml <<'EOF'
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Order API - SAM Lab 18

Globals:
  Function:
    Runtime: python3.12
    Timeout: 10
    MemorySize: 128
    Environment:
      Variables:
        TABLE_NAME: !Ref OrdersTable

Resources:
  CreateOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.create_order
      CodeUri: src/
      Role: !Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:role/LabRole
      Events:
        CreateOrder:
          Type: Api
          Properties:
            Path: /orders
            Method: post

  GetOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.get_order
      CodeUri: src/
      Role: !Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:role/LabRole
      Events:
        GetOrder:
          Type: Api
          Properties:
            Path: /orders/{order_id}
            Method: get

  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: sam-lab18-orders
      AttributeDefinitions:
        - AttributeName: order_id
          AttributeType: S
      KeySchema:
        - AttributeName: order_id
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST

Outputs:
  ApiUrl:
    Description: API endpoint URL
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
EOF

mkdir -p src
cat > src/app.py <<'EOF'
import json
import os
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def create_order(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = str(uuid.uuid4())[:8]

        item = {
            'order_id': order_id,
            'customer': body.get('customer', 'unknown'),
            'total': str(body.get('total', 0)),
            'status': 'created'
        }

        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Order created', 'order': item})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_order(event, context):
    try:
        order_id = event['pathParameters']['order_id']

        response = table.get_item(Key={'order_id': order_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Order not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'order': item})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
EOF

sam validate --region us-east-1
sam build

sam deploy --stack-name order-api-lab18 --region us-east-1 --capabilities CAPABILITY_IAM --resolve-s3 --no-disable-rollback --confirm-changeset --save-params

aws cloudformation describe-stacks --stack-name order-api-lab18 --query "Stacks[0].StackStatus" --output text
API_URL=$(aws cloudformation describe-stacks --stack-name order-api-lab18 --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
echo $API_URL

RES=$(curl -s -X POST ${API_URL}orders -H "Content-Type: application/json" -d '{"customer": "Bob", "total": 150}')
echo $RES
OID=$(echo $RES | jq -r .order.order_id)
curl -s ${API_URL}orders/$OID
curl -s -o /dev/null -w "%{http_code}\n" ${API_URL}orders/nonexistent

cd ~
sam init --runtime python3.12 --name monitored-api --app-template hello-world --package-type Zip --dependency-manager pip --no-tracing --no-application-insights --no-interactive
cd monitored-api

cat > template.yaml <<'EOF'
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Monitored API - Lab 18

Resources:
  ProcessFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler
      CodeUri: src/
      Runtime: python3.12
      Timeout: 10
      MemorySize: 128
      Role: !Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:role/LabRole
      Events:
        Process:
          Type: Api
          Properties:
            Path: /process
            Method: post

Outputs:
  ApiUrl:
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
EOF

mkdir -p src
cat > src/app.py <<'EOF'
import json
import time
import random

def handler(event, context):
    body = json.loads(event.get('body', '{}'))
    action = body.get('action', 'fast')

    if action == 'error':
        raise ValueError("Simulated error for monitoring test")
    elif action == 'slow':
        time.sleep(3)
    elif action == 'random':
        if random.random() < 0.3:
            raise RuntimeError("Random failure")

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'ok', 'action': action})
    }
EOF

sam build
sam deploy --stack-name monitored-api-lab18 --region us-east-1 --capabilities CAPABILITY_IAM --resolve-s3 --no-disable-rollback --confirm-changeset --save-params

API2=$(aws cloudformation describe-stacks --stack-name monitored-api-lab18 --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
FN=$(aws cloudformation describe-stack-resource --stack-name monitored-api-lab18 --logical-resource-id ProcessFunction --query StackResourceDetail.PhysicalResourceId --output text)
LG=/aws/lambda/$FN
echo $API2 $FN

for i in {1..10}; do curl -s -X POST "${API2}process" -H "Content-Type: application/json" -d '{"action": "fast"}' & done; wait
for i in {1..3};  do curl -s -X POST "${API2}process" -H "Content-Type: application/json" -d '{"action": "slow"}' & done; wait
for i in {1..5};  do curl -s -X POST "${API2}process" -H "Content-Type: application/json" -d '{"action": "error"}' & done; wait

aws cloudformation describe-stack-resources --stack-name monitored-api-lab18 --query "StackResources[].[LogicalResourceId,ResourceType,ResourceStatus]" --output table
aws cloudformation describe-stack-events --stack-name monitored-api-lab18 --query "reverse(StackEvents)[].[Timestamp,LogicalResourceId,ResourceStatus]" --output table

q() {
  local QID=$(aws logs start-query --log-group-name "$LG" --start-time $(date -d '-1 hour' +%s) --end-time $(date +%s) --query-string "$1" --query queryId --output text)
  sleep 5
  aws logs get-query-results --query-id $QID --query "results[]" --output json | jq -r '.[] | map(.field + "=" + .value) | join(" | ")'
}

q 'filter @type = "REPORT" | sort @duration desc | limit 10'
q 'filter @type = "REPORT" | stats count() as total, sum(@duration > 1000) as slow, count(@initDuration) as coldStarts'
q 'filter @message like /ERROR/ | fields @timestamp, @message | sort @timestamp desc | limit 10'

aws cloudwatch put-metric-alarm --alarm-name lab18-lambda-errors --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value=$FN --statistic Sum --period 300 --evaluation-periods 1 --threshold 2 --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching
aws cloudwatch describe-alarms --alarm-names lab18-lambda-errors --query "MetricAlarms[].[AlarmName,StateValue,Threshold]" --output table

cat > dash.json <<EOF
{
  "widgets": [
    {"type":"metric","x":0,"y":0,"width":12,"height":6,
     "properties":{"title":"Invocations","view":"timeSeries","region":"us-east-1","stat":"Sum","period":60,
       "metrics":[["AWS/Lambda","Invocations","FunctionName","$FN"]]}},
    {"type":"metric","x":12,"y":0,"width":12,"height":6,
     "properties":{"title":"Errors","view":"timeSeries","region":"us-east-1","stat":"Sum","period":60,
       "metrics":[["AWS/Lambda","Errors","FunctionName","$FN"]]}},
    {"type":"metric","x":0,"y":6,"width":12,"height":4,
     "properties":{"title":"Duration (Average)","view":"singleValue","region":"us-east-1","stat":"Average","period":300,
       "metrics":[["AWS/Lambda","Duration","FunctionName","$FN"]]}}
  ]
}
EOF

aws cloudwatch put-dashboard --dashboard-name lab18-serverless --dashboard-body file://dash.json
aws cloudwatch list-dashboards --query "DashboardEntries[].DashboardName" --output text
