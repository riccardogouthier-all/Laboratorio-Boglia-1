# Laboratorio 14 - Pipeline S3 -> Lambda -> DynamoDB

Autore: Riccardo Gouthier. Regione `us-east-1`, 26 ottobre 2026.

## Scenario

Due pipeline event-driven: (1) metadati dei file caricati su S3 salvati su DynamoDB; (2) import di un CSV di prodotti con tabella dotata di Global Secondary Index (GSI).

## Parte 1 - Metadati dei file

### Flusso

```
Upload S3 (lab14-uploads-gouthier) --ObjectCreated--> Lambda process-upload-metadata --> DynamoDB lab14-file-metadata
```

### Step 1 - Tabella DynamoDB

- Tabella: `lab14-file-metadata`
- Partition key: `file_key` (String)
- Modalita capacita: On-demand

### Step 2 - Bucket S3

- Bucket: `lab14-uploads-gouthier`

### Step 3 - Funzione `process-upload-metadata`

Per ogni record dell'evento:

1. legge `bucket`, `key`, `size` ed `eventTime`;
2. `s3.head_object` per ottenere `ContentType` (default `unknown`);
3. `put_item` con `file_key`, `bucket`, `size_bytes`, `content_type`, `uploaded_at` (= `eventTime`), `processed_at` (UTC ISO);
4. log `Saved metadata for: {key} ({size} bytes, {content_type})`;
5. risposta 200 `Processed N files`.

### Step 4 - Trigger S3

| Nome | Eventi | Destinazione |
|---|---|---|
| `upload-metadata-trigger` | All object create events | Lambda `process-upload-metadata` |

### Step 5 - Test della pipeline

Upload di 3 file (26 ottobre 2026, 15:07:07 UTC+01:00):

| File | Tipo | Dimensione |
|---|---|---|
| `data.json` | json | 219 B |
| `list.csv` | csv | 127 B |
| `test.txt` | txt | 122 B |

### Step 6 - Verifica nella tabella

| file_key | bucket | content_type | size_bytes |
|---|---|---|---|
| `list.csv` | `lab14-uploads-gouthier` | `text/csv` | 127 |
| `data.json` | `lab14-uploads-gouthier` | `application/json` | 219 |
| `test.txt` | `lab14-uploads-gouthier` | `text/plain` | 122 |

Scan: 3 elementi, tutti con `uploaded_at` e `processed_at` (UTC, 14:07:06-14:07:08).

### Step 7 - Log

Log group `/aws/lambda/process-upload-metadata`:

```
Saved metadata for: test.txt (122 bytes, text/plain)
REPORT ... Duration: 513.68 ms  Billed Duration: 1058 ms  Memory Size: 128 MB  Max Memory Used: 95 MB  Init Duration: 541.90 ms
```

## Parte 2 - Import CSV con GSI

### Flusso

```
Upload CSV in imports/ (lab14-csv-import-gouthier) --> Lambda csv-importer --> DynamoDB lab14-products (GSI category-price-index)
```

### Step 8 - Tabella con GSI

- Tabella: `lab14-products`, partition key `product_id` (String), on-demand.
- GSI: `category-price-index`

| Nome indice | Partition key | Sort key | Proiezione | Capacita |
|---|---|---|---|---|
| `category-price-index` | `category` (String) | `price` (Number) | All | On-demand |

### Step 9 - Bucket S3 con folder

- Bucket: `lab14-csv-import-gouthier`
- Cartella: `imports/`

### Step 10 - Funzione `csv-importer`

1. legge l'oggetto S3 e lo decodifica (`utf-8`);
2. `csv.DictReader(io.StringIO(content))`;
3. `table.batch_writer()` con `put_item` per riga: `product_id`, `category`, `name`, `price` (`Decimal`), `stock` (`int`);
4. log `Imported {count} products` e risposta 200 `Imported N products`.

### Step 11 - Trigger con filtro

| Nome | Eventi | Filtri | Destinazione |
|---|---|---|---|
| `csv-import-trigger` | All object create events | prefisso `imports/`, suffisso `.csv` | Lambda `csv-importer` |

I file fuori da `imports/` o senza estensione `.csv` non avviano la funzione.

### Step 12 - Test della pipeline

Upload di `products.csv` (243 B) in `imports/`: 1 file, 100% riuscito.

Scan della tabella: 6 prodotti.

| product_id | category | name | price | stock |
|---|---|---|---|---|
| P001 | Electronics | Laptop | 999.99 | 50 |
| P002 | Electronics | Mouse | 29.99 | 200 |
| P003 | Books | Python Coo... | 45 | 100 |
| P004 | Electronics | Keyboard | 79.99 | 150 |
| P005 | Books | AWS in Action | 55 | 75 |
| P006 | Clothing | T-Shirt | 19.99 | 300 |

### Step 13 - Query con GSI

Query su `category-price-index`:

| Test | Partition key (`category`) | Risultato | RCU |
|---|---|---|---|
| Electronics | `Electronics` | 3 item ordinati per prezzo: Mouse 29.99, Keyboard 79.99, Laptop 999.99 | 0,5 |
| Books | `Books` | 2 item: P003 (45), P005 (55) | 0,5 |

## Prove

| # | Prova | Tipo | Esito |
|---|---|---|---|
| 1 | Upload di 3 file in `lab14-uploads-gouthier` | Positiva | 3 righe di metadati in DynamoDB |
| 2 | Upload di `products.csv` in `imports/` | Positiva (trigger con filtro) | 6 prodotti importati |
| 3 | Query GSI per categoria | Positiva | Item della categoria, ordinati per prezzo |

## Conclusioni

1. `head_object` permette di arricchire l'evento S3 con metadati (`ContentType`) non presenti nel payload.
2. I filtri prefisso/suffisso sul trigger evitano invocazioni inutili.
3. Il GSI `category-price-index` abilita query per categoria ordinate per prezzo senza scansionare la tabella.
4. `batch_writer` scrive molte righe riducendo le chiamate a DynamoDB.

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
mkdir -p lab14 && cd lab14

# ================= Parte 1 - Metadati dei file (S3 -> Lambda -> DynamoDB) =================

# Step 1 - Tabella lab14-file-metadata
aws dynamodb create-table --table-name lab14-file-metadata --attribute-definitions AttributeName=file_key,AttributeType=S --key-schema AttributeName=file_key,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab14-file-metadata

# Step 2 - Bucket
aws s3api create-bucket --bucket lab14-uploads-gouthier

# Step 3 - Funzione process-upload-metadata
cat > lambda_function.py <<'EOF'
import json
import urllib.parse
from datetime import datetime, timezone
import boto3

s3 = boto3.client('s3')
table = boto3.resource('dynamodb').Table('lab14-file-metadata')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']
        uploaded_at = record['eventTime']

        head = s3.head_object(Bucket=bucket, Key=key)
        content_type = head.get('ContentType', 'unknown')

        table.put_item(Item={
            'file_key': key,
            'bucket': bucket,
            'size_bytes': size,
            'content_type': content_type,
            'uploaded_at': uploaded_at,
            'processed_at': datetime.now(timezone.utc).isoformat()
        })
        print(f"Saved metadata for: {key} ({size} bytes, {content_type})")

    return {'statusCode': 200, 'body': f'Processed {len(event["Records"])} files'}
EOF
zip -q meta.zip lambda_function.py
aws lambda create-function --function-name process-upload-metadata --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://meta.zip
aws lambda wait function-active-v2 --function-name process-upload-metadata

# Step 4 - Trigger S3 (All object create events)
aws lambda add-permission --function-name process-upload-metadata --statement-id s3-invoke --action lambda:InvokeFunction --principal s3.amazonaws.com --source-arn arn:aws:s3:::lab14-uploads-gouthier --source-account $ACC
FN1=$(aws lambda get-function --function-name process-upload-metadata --query Configuration.FunctionArn --output text)
aws s3api put-bucket-notification-configuration --bucket lab14-uploads-gouthier --notification-configuration "{\"LambdaFunctionConfigurations\":[{\"Id\":\"upload-metadata-trigger\",\"LambdaFunctionArn\":\"$FN1\",\"Events\":[\"s3:ObjectCreated:*\"]}]}"

# Step 5 - Upload di 3 file (json, csv, txt)
echo '{"nome":"test","valore":1}' > data.json
printf 'id,nome\n1,uno\n2,due\n' > list.csv
echo "file di prova" > test.txt
aws s3 cp data.json s3://lab14-uploads-gouthier/
aws s3 cp list.csv  s3://lab14-uploads-gouthier/
aws s3 cp test.txt  s3://lab14-uploads-gouthier/

# Step 6-7 - Verifica nella tabella e nei log
sleep 10
aws dynamodb scan --table-name lab14-file-metadata --query "Items[].[file_key.S,content_type.S,size_bytes.N,uploaded_at.S,processed_at.S]" --output table
aws logs tail /aws/lambda/process-upload-metadata --since 5m

# ================= Parte 2 - Import CSV con GSI =================

# Step 8 - Tabella lab14-products con GSI category-price-index (category + price, proiezione ALL)
aws dynamodb create-table --table-name lab14-products \
  --attribute-definitions AttributeName=product_id,AttributeType=S AttributeName=category,AttributeType=S AttributeName=price,AttributeType=N \
  --key-schema AttributeName=product_id,KeyType=HASH \
  --global-secondary-indexes 'IndexName=category-price-index,KeySchema=[{AttributeName=category,KeyType=HASH},{AttributeName=price,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
  --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab14-products

# Step 9 - Bucket e cartella imports/
aws s3api create-bucket --bucket lab14-csv-import-gouthier
aws s3api put-object --bucket lab14-csv-import-gouthier --key imports/

# Step 10 - Funzione csv-importer
cat > lambda_function.py <<'EOF'
import csv
import io
import urllib.parse
from decimal import Decimal
import boto3

s3 = boto3.client('s3')
table = boto3.resource('dynamodb').Table('lab14-products')

def lambda_handler(event, context):
    count = 0
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        content = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')

        with table.batch_writer() as batch:
            for row in csv.DictReader(io.StringIO(content)):
                batch.put_item(Item={
                    'product_id': row['product_id'],
                    'category': row['category'],
                    'name': row['name'],
                    'price': Decimal(row['price']),
                    'stock': int(row['stock'])
                })
                count += 1
    print(f"Imported {count} products")
    return {'statusCode': 200, 'body': f'Imported {count} products'}
EOF
zip -q csv.zip lambda_function.py
aws lambda create-function --function-name csv-importer --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://csv.zip --timeout 30
aws lambda wait function-active-v2 --function-name csv-importer

# Step 11 - Trigger con filtro prefisso imports/ e suffisso .csv
aws lambda add-permission --function-name csv-importer --statement-id s3-invoke --action lambda:InvokeFunction --principal s3.amazonaws.com --source-arn arn:aws:s3:::lab14-csv-import-gouthier --source-account $ACC
FN2=$(aws lambda get-function --function-name csv-importer --query Configuration.FunctionArn --output text)
aws s3api put-bucket-notification-configuration --bucket lab14-csv-import-gouthier --notification-configuration "{\"LambdaFunctionConfigurations\":[{\"Id\":\"csv-import-trigger\",\"LambdaFunctionArn\":\"$FN2\",\"Events\":[\"s3:ObjectCreated:*\"],\"Filter\":{\"Key\":{\"FilterRules\":[{\"Name\":\"prefix\",\"Value\":\"imports/\"},{\"Name\":\"suffix\",\"Value\":\".csv\"}]}}}]}"

# Step 12 - Upload di products.csv in imports/ e scan
cat > products.csv <<'EOF'
product_id,category,name,price,stock
P001,Electronics,Laptop,999.99,50
P002,Electronics,Mouse,29.99,200
P003,Books,Python Cookbook,45.00,100
P004,Electronics,Keyboard,79.99,150
P005,Books,AWS in Action,55.00,75
P006,Clothing,T-Shirt,19.99,300
EOF
aws s3 cp products.csv s3://lab14-csv-import-gouthier/imports/products.csv
sleep 10
aws dynamodb scan --table-name lab14-products --query "Items[].[product_id.S,category.S,name.S,price.N,stock.N]" --output table

# Step 13 - Query sul GSI (ordinata per prezzo)
aws dynamodb query --table-name lab14-products --index-name category-price-index --key-condition-expression "category = :c" --expression-attribute-values '{":c":{"S":"Electronics"}}' --return-consumed-capacity INDEXES --query "[Items[].[name.S,price.N],ConsumedCapacity]" --output json
aws dynamodb query --table-name lab14-products --index-name category-price-index --key-condition-expression "category = :c" --expression-attribute-values '{":c":{"S":"Books"}}' --query "Items[].[product_id.S,price.N]" --output table
cd ..
```

### Cleanup

```bash
aws s3 rm s3://lab14-uploads-gouthier --recursive && aws s3api delete-bucket --bucket lab14-uploads-gouthier
aws s3 rm s3://lab14-csv-import-gouthier --recursive && aws s3api delete-bucket --bucket lab14-csv-import-gouthier
aws lambda delete-function --function-name process-upload-metadata
aws lambda delete-function --function-name csv-importer
aws dynamodb delete-table --table-name lab14-file-metadata
aws dynamodb delete-table --table-name lab14-products
aws logs delete-log-group --log-group-name /aws/lambda/process-upload-metadata
aws logs delete-log-group --log-group-name /aws/lambda/csv-importer
```
