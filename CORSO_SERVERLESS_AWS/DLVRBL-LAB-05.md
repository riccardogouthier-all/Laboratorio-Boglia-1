# Laboratorio 05 - Limitazioni Serverless e Best Practice

Lavoro di gruppo (Gruppo 2: Matteo Ninotti / Riccardo Gouthier / Ivan Cioffi).

## Scenario

Un collega ha scritto una Lambda per elaborare ordini e-commerce. Il codice funziona ma viola diverse best practice. Compito: code review e proposte di miglioramento.

## Step 1 - Codice analizzato

Lambda Python (`lambda_handler`) che:

- importa `boto3`, `json`, `os`, `pandas`, `numpy` (questi ultimi due inutilizzati);
- definisce `DB_PASSWORD = "SuperSecret123!"` nel sorgente;
- crea client e tabella DynamoDB (`orders`) dentro l'handler;
- legge `order_id` e `amount` da `event['body']` senza validazione;
- scrive su DynamoDB salvando nell'item anche `db_password`;
- importa `pymysql` a meta handler e si connette a RDS con password in chiaro;
- esegue `INSERT INTO orders VALUES ('{order_id}', {amount})` costruita con f-string;
- non gestisce errori e restituisce sempre `{'statusCode': 200, 'body': 'OK'}`.

## Step 2 - Problemi individuati

| # | Problema | Soluzione | Categoria | Rischio |
|---|---|---|---|---|
| 1 | Credenziali hardcoded: `DB_PASSWORD` nel sorgente, visibile a chiunque acceda al repository | Rimuoverla dal codice; leggerla da un servizio dedicato (es. Secrets Manager) | Sicurezza | Alto |
| 2 | Password salvata in DynamoDB: `db_password` scritto come attributo dell'item | Non salvare mai credenziali nei dati | Sicurezza | Alto |
| 3 | Librerie inutilizzate (`pandas`, `numpy`) | Rimuovere gli import: aumentano dimensione del package e tempo di cold start senza utilita | Performance | Basso |
| 4 | Init di client DynamoDB e connessione DB dentro l'handler: eseguiti a ogni invocazione | Portarli fuori dall'handler: vengono eseguiti solo alla creazione del container e riutilizzati per 5-15 min | Performance | - |
| 5 | Nessuna validazione dell'input (`order_id`, `amount`) | Validare presenza, tipo e formato prima di usarli; insieme alla query in chiaro espone a SQL injection | Sicurezza | - |
| 6 | Query SQL costruita con f-string (in chiaro) | Evitare la concatenazione di input nella query (query parametrizzata) | Sicurezza | - |
| 7 | Nessuna gestione errori nell'inizializzazione/connessione al DB (nessun fallback) | `try: ... except` attorno alla connessione | Affidabilita | - |
| 8 | Nessuna gestione errori sulla query MySQL | `try: ... except MySQLdb.Error` | Affidabilita | - |
| 9 | Il `return` non tiene conto degli errori (sempre 200 `OK`) | Restituire status code coerenti con l'esito | Affidabilita | - |
| 10 | `import pymysql` a meta codice | Spostare gli import in cima al file per chiarezza | Stile | Basso |
| 11 | Nessun log su CloudWatch | Usare il modulo `logging` | Osservabilita | - |

Nota: categoria e rischio sono riportati come nel documento di gruppo per i punti 1-3; per gli altri la categoria e dedotta, il rischio non era indicato.

## Conclusioni

1. Priorita alta: eliminare credenziali hardcoded e password nel DB (punti 1-2).
2. Spostare l'inizializzazione fuori dall'handler sfrutta il riuso dei container Lambda.
3. Validazione input + query sicure + gestione errori + logging rendono la funzione sicura e diagnosticabile.

Procedura di esecuzione in CLI Cloudshell:

Code review della Lambda del collega: si ricrea il file, si individuano i problemi con `grep` e si prepara la versione corretta.

```bash
mkdir -p lab05 && cd lab05

# 1) Codice originale (con i difetti)
cat > lambda_bad.py <<'EOF'
import boto3, json, os
import pandas as pd
import numpy as np

DB_PASSWORD = "SuperSecret123!"

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('orders')
    body = json.loads(event['body'])
    order_id = body['order_id']
    amount = body['amount']
    table.put_item(Item={'order_id': order_id, 'amount': amount, 'db_password': DB_PASSWORD})
    import pymysql
    conn = pymysql.connect(host=os.environ['DB_HOST'], user='admin', password=DB_PASSWORD, database='shop')
    cur = conn.cursor()
    cur.execute(f"INSERT INTO orders VALUES ('{order_id}', {amount})")
    conn.commit()
    return {'statusCode': 200, 'body': 'OK'}
EOF

# 2) Audit dei problemi
grep -nE 'PASSWORD|password' lambda_bad.py          # credenziali hardcoded / salvate nei dati
grep -nE '^import (pandas|numpy)' lambda_bad.py     # librerie inutilizzate
grep -nE 'execute\(f"' lambda_bad.py                # SQL con f-string (injection)
grep -nE '^\s+import ' lambda_bad.py                # import dentro l'handler
grep -c 'try:' lambda_bad.py                        # 0 = nessuna gestione errori
grep -c 'logging' lambda_bad.py                     # 0 = nessun log

# 3) Versione corretta
cat > lambda_good.py <<'EOF'
import json, logging, os
import boto3
import pymysql

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Init fuori dall'handler: riusati tra le invocazioni
table = boto3.resource('dynamodb').Table('orders')
secrets = boto3.client('secretsmanager')

def get_db_password():
    return json.loads(secrets.get_secret_value(SecretId=os.environ['DB_SECRET'])['SecretString'])['password']

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body') or '{}')
        order_id = str(body.get('order_id', ''))
        amount = body.get('amount')
        if not order_id.isalnum() or not isinstance(amount, (int, float)):
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid input'})}

        table.put_item(Item={'order_id': order_id, 'amount': str(amount)})   # nessuna credenziale nei dati

        conn = pymysql.connect(host=os.environ['DB_HOST'], user=os.environ['DB_USER'],
                               password=get_db_password(), database='shop')
        with conn.cursor() as cur:
            cur.execute("INSERT INTO orders VALUES (%s, %s)", (order_id, amount))   # query parametrizzata
        conn.commit()
        logger.info("Order %s saved", order_id)
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    except Exception:
        logger.exception("Order processing failed")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}
EOF

python3 -m py_compile lambda_good.py && echo "sintassi OK"
cd ..
```

Nota: la versione corretta e un esempio da review; non viene deployata (richiede un'istanza RDS).
