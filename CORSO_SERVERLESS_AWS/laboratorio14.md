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
