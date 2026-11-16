# Laboratorio 13 - DynamoDB: Lambda CRUD su ordini

Autore: Riccardo Gouthier. Regione `us-east-1`, 26 ottobre 2026.

## Scenario

Tabella DynamoDB di ordini con chiave composta (cliente + data) e Lambda `orders-crud` che esegue GetItem, Query, Scan e creazione ordine.

## Step 1 - Tabella DynamoDB

- Tabella: `lab13-orders`
- Partition key: `customer_id` (String)
- Sort key: `order_date` (String)
- Modalita capacita: On-demand

## Step 2 - Dati inseriti dalla console

| customer_id | order_date | product | quantity | total |
|---|---|---|---|---|
| C001 | 2025-01-15 | Laptop | 1 | 999.99 |
| C001 | 2025-02-20 | Mouse | 2 | 49.98 |
| C001 | 2025-03-10 | Keyboard | 1 | 79.99 |
| C002 | 2025-01-22 | Monitor | 1 | 349.99 |
| C002 | 2025-03-05 | Webcam | 1 | 89.99 |

Scan di verifica: 5 elementi restituiti.

## Step 3 - Funzione Lambda `orders-crud`

| Operazione | Implementazione |
|---|---|
| GetItem | lettura per chiave (`customer_id` + `order_date`) |
| `query_orders` | `Key('customer_id').eq(customer_id)`; con prefisso data aggiunge `& Key('order_date').begins_with(prefix)` |
| `create_order` | `table.put_item(Item=item)`, risposta 201 `Order created` |
| `scan_orders` | `table.scan(Limit=50)` |
| `response` | `json.dumps(body, default=str)` |

## Step 4 - Test delle operazioni

| # | Operazione | Input | Risultato | Duration | Billed |
|---|---|---|---|---|---|
| 1 | GetItem | `C001`, `2025-01-15` | 200, Laptop, quantita 1, totale 999.99 | 303,35 ms | 851 ms (Init 547,19 ms) |
| 2 | Query gennaio | `C001`, prefisso `2025-01` | 200, 1 ordine (Laptop), `count` 1 | 255,65 ms | 256 ms |
| 3 | Query tutti | `C001` | 200, 3 ordini (Laptop, Mouse, Keyboard), `count` 3 | 52,44 ms | 53 ms |
| 4 | Scan | - | 200, 5 ordini, `count` 5 | 49,75 ms | 50 ms |

## Step 5 - Creare un nuovo ordine

Problema: `create_order` non accetta numeri decimali (boto3 non scrive i `float` in DynamoDB, serve `Decimal`). Correzione in `create_order`:

```python
from decimal import Decimal

def create_order(event):
    item = json.loads(json.dumps(event['item']), parse_float=Decimal)
    table.put_item(Item=item)
    return response(201, {'message': 'Order created', 'item': item})
```

Le altre due operazioni (GetItem, Query, Scan) erano corrette senza modifiche.

Test dopo la correzione:

- Item: `customer_id` `C003`, `order_date` `2025-04-01`, `product` `Headphones`, `quantity` 1, `total` 59.99
- Risposta: 201 `Order created`
- Duration 311,26 ms, Billed 811 ms, Init Duration 499,54 ms (cold start)

## Prove

| # | Prova | Tipo | Esito |
|---|---|---|---|
| 1 | GetItem con chiave completa | Positiva (lettura) | Item restituito |
| 2 | Query per cliente con prefisso data | Positiva (query) | Solo gli ordini di gennaio |
| 3 | Scan della tabella | Positiva (scan) | 5 ordini |
| 4 | Creazione ordine con `total` decimale | Negativa -> Positiva | Prima fallisce, dopo `Decimal` 201 |

## Conclusioni

1. Query e GetItem usano la chiave (efficienti); Scan legge tutta la tabella e va limitato (`Limit=50`).
2. `begins_with` sulla sort key permette filtri per periodo (es. un mese) senza scansione.
3. DynamoDB richiede `Decimal` per i numeri non interi.
4. Il cold start pesa nelle prime invocazioni (Init ~500 ms), non nelle successive.

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
mkdir -p lab13 && cd lab13

# Step 1 - Tabella con chiave composta (cliente + data)
aws dynamodb create-table --table-name lab13-orders \
  --attribute-definitions AttributeName=customer_id,AttributeType=S AttributeName=order_date,AttributeType=S \
  --key-schema AttributeName=customer_id,KeyType=HASH AttributeName=order_date,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab13-orders

# Step 2 - Dati di test
put() { aws dynamodb put-item --table-name lab13-orders --item "{\"customer_id\":{\"S\":\"$1\"},\"order_date\":{\"S\":\"$2\"},\"product\":{\"S\":\"$3\"},\"quantity\":{\"N\":\"$4\"},\"total\":{\"N\":\"$5\"}}"; }
put C001 2025-01-15 Laptop   1 999.99
put C001 2025-02-20 Mouse    2 49.98
put C001 2025-03-10 Keyboard 1 79.99
put C002 2025-01-22 Monitor  1 349.99
put C002 2025-03-05 Webcam   1 89.99
aws dynamodb scan --table-name lab13-orders --select COUNT          # atteso: 5

# Step 3 - Funzione orders-crud (con Decimal per i numeri, correzione dello Step 5)
cat > lambda_function.py <<'EOF'
import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb').Table('lab13-orders')

def lambda_handler(event, context):
    action = event.get('action')
    if action == 'get':
        return get_order(event['customer_id'], event['order_date'])
    if action == 'query':
        return query_orders(event['customer_id'], event.get('date_prefix'))
    if action == 'create':
        return create_order(event)
    if action == 'scan':
        return scan_orders()
    return response(400, {'error': 'unknown action'})

def get_order(customer_id, order_date):
    item = table.get_item(Key={'customer_id': customer_id, 'order_date': order_date}).get('Item')
    return response(200, item) if item else response(404, {'error': 'Order not found'})

def query_orders(customer_id, prefix=None):
    cond = Key('customer_id').eq(customer_id)
    if prefix:
        cond = cond & Key('order_date').begins_with(prefix)
    items = table.query(KeyConditionExpression=cond)['Items']
    return response(200, {'orders': items, 'count': len(items)})

def create_order(event):
    item = json.loads(json.dumps(event['item']), parse_float=Decimal)
    table.put_item(Item=item)
    return response(201, {'message': 'Order created', 'item': item})

def scan_orders():
    items = table.scan(Limit=50)['Items']
    return response(200, {'orders': items, 'count': len(items)})

def response(status_code, body):
    return {'statusCode': status_code, 'body': json.dumps(body, default=str)}
EOF
zip -q function.zip lambda_function.py
aws lambda create-function --function-name orders-crud --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip
aws lambda wait function-active-v2 --function-name orders-crud

# Step 4 - Test delle operazioni
inv() { aws lambda invoke --function-name orders-crud --cli-binary-format raw-in-base64-out --payload "$1" out.json > /dev/null; cat out.json; echo; }
inv '{"action":"get","customer_id":"C001","order_date":"2025-01-15"}'
inv '{"action":"query","customer_id":"C001","date_prefix":"2025-01"}'
inv '{"action":"query","customer_id":"C001"}'
inv '{"action":"scan"}'

# Step 5 - Nuovo ordine con totale decimale
inv '{"action":"create","item":{"customer_id":"C003","order_date":"2025-04-01","product":"Headphones","quantity":1,"total":59.99}}'
aws dynamodb get-item --table-name lab13-orders --key '{"customer_id":{"S":"C003"},"order_date":{"S":"2025-04-01"}}'

# Righe REPORT (Duration, Billed Duration, Init Duration)
aws logs filter-log-events --log-group-name /aws/lambda/orders-crud --filter-pattern REPORT --query "events[].message" --output text
cd ..
```

### Cleanup

```bash
aws lambda delete-function --function-name orders-crud
aws dynamodb delete-table --table-name lab13-orders
aws logs delete-log-group --log-group-name /aws/lambda/orders-crud
```
