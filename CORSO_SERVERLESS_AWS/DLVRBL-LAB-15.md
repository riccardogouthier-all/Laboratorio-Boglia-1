# Laboratorio 15 - DynamoDB TTL, backup e lifecycle S3

Autore: Riccardo Gouthier. Regione `us-east-1`, 12 novembre 2026.

## Scenario

Gestione del ciclo di vita dei dati: sessioni utente con scadenza automatica (TTL) su DynamoDB, protezione con backup on-demand e Point-in-Time Recovery (PITR), archiviazione a costo ridotto su S3 con regola di lifecycle.

## Parte 1 - DynamoDB con TTL

### Flusso

```
Lambda insert-sessions --put_item--> DynamoDB lab15-sessions (TTL su expires_at)
```

### Step 1 - Tabella con dati di sessione

- Tabella: `lab15-sessions`
- Partition key: `session_id` (String), nessuna sort key, nessun indice
- Modalità capacità: On-demand (`PAY_PER_REQUEST`)
- Stato: `Active`, Deletion protection: Off

### Step 2 - Abilitare il TTL

- Attributo TTL: `expires_at` (Number, epoch in secondi)
- Stato TTL: `On`; elementi eliminati nelle ultime 24 ore: 0

Il TTL elimina in background gli item il cui `expires_at` è nel passato. La cancellazione non è istantanea: DynamoDB la esegue normalmente entro alcune ore dalla scadenza (fino a 48 ore).

### Step 3 - Funzione `insert-sessions`

Runtime Python 3.12, ruolo `LabRole`. Calcola `now = int(time.time())` e inserisce 3 sessioni con `put_item`:

| session_id | user_id | expires_at |
|---|---|---|
| `sess-001` | `alice` | `now + 60` (1 minuto) |
| `sess-002` | `bob` | `now + 3600` (1 ora) |
| `sess-003` | `charlie` | `now + 86400` (1 giorno) |

Risposta: 200 `Created 3 sessions` con `current_epoch`. Log per ogni sessione: `Created session {id}, expires in {n}s`.

### Step 4 - Osservare il TTL in azione

Scan eseguita il 12 novembre 2026 alle 12:20:55 (UTC+01:00): 3 item restituiti, 3 scansionati, efficienza 100%, 2 RCU consumate.

| session_id | created_at | expires_at | user_id |
|---|---|---|---|
| `sess-003` | 1794482152 | 1794568552 | `charlie` |
| `sess-001` | 1794482152 | 1794482212 | `alice` |
| `sess-002` | 1794482152 | 1794485752 | `bob` |

`sess-001` è scaduta dopo 60 secondi (`1794482212`) ma al momento della scan è ancora presente: la tabella la considera scaduta, ma la cancellazione fisica avviene in differita.

## Parte 2 - Backup e PITR

### Step 5 - Backup on-demand e PITR

| Funzione | Configurazione | Stato |
|---|---|---|
| Backup on-demand | `sessions-backup-test` | `Available` |
| PITR | Abilitato (`PointInTimeRecoveryEnabled=true`) | `On`, periodo di recupero 35 giorni |

Il primo punto di ripristino disponibile è il 12 novembre 2026, 12:17:36 (UTC+01:00). Il backup on-demand è una copia a un istante preciso; il PITR permette di ripristinare la tabella a qualsiasi secondo entro 35 giorni.

## Parte 3 - Lifecycle S3

### Step 6 - Regola di lifecycle

- Bucket: `lab15-lifecycle-riccardogouthier` con 2 oggetti di test (`test1.txt`, `test2.txt`)
- Regola: `archive-old-files`, stato `Enabled`, ambito intero bucket (nessun prefisso, nessun filtro per tag o dimensione)

| Giorno | Azione |
|---|---|
| 0 | Oggetto caricato (Standard) |
| 30 | Transizione a `STANDARD_IA` |
| 90 | Transizione a `GLACIER` (Glacier Flexible Retrieval) |
| 365 | Scadenza (eliminazione) |

Nessuna azione definita per le versioni non correnti (il bucket non ha versioning).

## Prove

| # | Prova | Tipo | Esito |
|---|---|---|---|
| 1 | Invocazione `insert-sessions` e scan della tabella | Positiva | 3 sessioni salvate con `expires_at` diversi |
| 2 | Scan dopo la scadenza di `sess-001` | Osservazione | Item ancora presente: cancellazione TTL differita |
| 3 | Backup on-demand e PITR | Positiva | Backup `Available`, PITR `On` |
| 4 | Lettura regola lifecycle | Positiva | Transizioni a 30/90 giorni, scadenza a 365 |

## Conclusioni

1. Il TTL è gratuito e automatico, ma non è un timer preciso: per logica applicativa con scadenza esatta serve un filtro su `expires_at` in lettura.
2. Backup on-demand e PITR sono complementari: il primo conserva uno stato scelto, il secondo copre errori recenti.
3. Il lifecycle S3 riduce i costi spostando gli oggetti verso classi più economiche con l'invecchiamento; le transizioni non sono osservabili nel lab perché richiedono 30 giorni.
4. Limite: la scadenza fisica di `sess-001` e le transizioni lifecycle non sono state attese e non sono provate.
5. Per completare la prova del TTL: rieseguire la scan dopo qualche ora (fino a 48 ore) e controllare che `sess-001` sia sparita (`aws dynamodb get-item --table-name lab15-sessions --key '{"session_id":{"S":"sess-001"}}'` deve restituire un output vuoto), oppure filtrare in lettura con `expires_at > now`. Il PITR e il backup non sono stati ripristinati: il ripristino (`restore-table-to-point-in-time`) crea una tabella nuova e va eliminata dopo la verifica.

Procedura di esecuzione in CLI Cloudshell:

Eseguire nel bucket/tabella già usati dal deliverable (nome bucket: `lab15-lifecycle-riccardogouthier`).

```bash
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
```

### Cleanup

```bash
aws dynamodb delete-backup --backup-arn $BK_ARN
aws dynamodb update-continuous-backups --table-name lab15-sessions --point-in-time-recovery-specification PointInTimeRecoveryEnabled=false
aws dynamodb delete-table --table-name lab15-sessions
aws lambda delete-function --function-name insert-sessions
aws s3 rm s3://$BUCKET --recursive && aws s3api delete-bucket --bucket $BUCKET
aws logs delete-log-group --log-group-name /aws/lambda/insert-sessions
```
