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
