# Laboratorio 09 - Sicurezza IAM con DynamoDB e Secrets Manager

Autore: Riccardo Gouthier (Gruppo 2). Corrisponde alla Parte B del "Lab 08-09".

## Scenario

Lambda `secure-reader` che legge un utente da DynamoDB e carica un segreto da Secrets Manager, con validazione dell'input e permessi IAM minimi (least privilege).

## Step 6 - Tabella DynamoDB

- Tabella: `lab09-users`
- Partition key: `user_id` (String)
- Modalità capacità: On-demand
- Creata il 21 settembre 2026, 17:17 (UTC+02:00), cioè 15:17 UTC

## Step 7 - Dati di test

| user_id | email | name |
|---|---|---|
| u001 | alice@example.com | Alice |
| u002 | bob@example.com | Bob |

## Step 8 - Funzione `secure-reader`

Comportamento:

- legge `user_id` dall'evento e lo valida;
- `GetItem` sulla tabella; se l'utente non esiste risponde 404;
- carica il segreto da Secrets Manager;
- risposta 200 con `user`, `secret_loaded: true` e `secret_key_present` (verifica che la chiave `demo_token` sia nel segreto, senza esporne il valore);
- log JSON strutturati (`status: success` / `action: get_user`, `status: error`);
- in caso di eccezione: log dell'errore e risposta 500 `Internal server error`.

## Step 9 - Variabili d'ambiente

| Chiave | Valore |
|---|---|
| `APP_SECRET_NAME` | `lab09/app-config` |
| `TABLE_NAME` | `lab09-users` |

## Step 10 - Segreto

- Secrets Manager: segreto `lab09/app-config`
- Creato il 21 settembre 2026, 15:28:52 UTC

## Step 11 - Test

Evento di test: `hello-world` (è il nome del template predefinito della console; il contenuto è l'evento JSON con `user_id` descritto in tabella).

| # | Input | Tipo | Risposta |
|---|---|---|---|
| 1 | `user_id` = `u001` | Positiva | 200, utente Alice, `secret_loaded: true`, `secret_key_present: true` |
| 2 | `user_id` = `999` (inesistente) | Negativa (deve dare errore) | 404 `User not found` |
| 3 | `user_id` = `"'; DROP TABLE users;--"` | Negativa (input malevolo) | 400 `Invalid user_id format` |
| 4 | evento vuoto `{}` | Negativa (campo mancante) | 400 `user_id is required` (verificato eseguendo la procedura: `not user_id` è il primo controllo) |

Il caso 2 usa `999`; con un id valido ma inesistente come `u999` il risultato è lo stesso (404), perché il formato è alfanumerico. Il test 3 non è una vera SQL injection: DynamoDB non usa SQL. Verifica solo che la validazione del formato respinga caratteri come apice, punto e virgola e spazio prima di arrivare al database.

## Step 12 - Azioni IAM minime richieste (5 azioni)

| # | Azione | Risorsa |
|---|---|---|
| 1 | `dynamodb:GetItem` | tabella `lab09-users` |
| 2 | `secretsmanager:GetSecretValue` | segreto `lab09/app-config` |
| 3 | `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` | log della funzione |

## Conclusioni

1. Le credenziali non stanno nel codice: il segreto è letto a runtime da Secrets Manager e non viene mai restituito in chiaro.
2. La validazione del formato di `user_id` blocca input malevoli (input con caratteri non ammessi -> 400).
3. Il ruolo della funzione deve avere solo le cinque azioni elencate (`dynamodb:GetItem`, `secretsmanager:GetSecretValue`, `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`), ciascuna limitata alla propria risorsa.
4. Il `LabRole` del Learner Lab è molto più ampio di queste cinque azioni: funziona per il lab ma non rispetta il minimo privilegio. In un account reale la funzione avrebbe un ruolo dedicato con solo la policy dello Step 12 (vedi `least-privilege.json` nella procedura CLI, documentale perché nel Learner Lab non si crea un ruolo dedicato).

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
mkdir -p lab09 && cd lab09

# Step 6 - Tabella lab09-users
aws dynamodb create-table --table-name lab09-users --attribute-definitions AttributeName=user_id,AttributeType=S --key-schema AttributeName=user_id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab09-users

# Step 7 - Dati di test
aws dynamodb put-item --table-name lab09-users --item '{"user_id":{"S":"u001"},"name":{"S":"Alice"},"email":{"S":"alice@example.com"}}'
aws dynamodb put-item --table-name lab09-users --item '{"user_id":{"S":"u002"},"name":{"S":"Bob"},"email":{"S":"bob@example.com"}}'

# Step 10 - Segreto in Secrets Manager
aws secretsmanager create-secret --name lab09/app-config --secret-string '{"demo_token":"token-123"}'

# Step 8 - Funzione secure-reader
cat > lambda_function.py <<'EOF'
import json
import os
import boto3

TABLE_NAME = os.environ.get('TABLE_NAME', 'lab09-users')
REGION = os.environ.get('AWS_REGION', 'us-east-1')
APP_SECRET_NAME = os.environ.get('APP_SECRET_NAME', 'lab09/app-config')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)
secrets_client = boto3.client('secretsmanager', region_name=REGION)

def get_app_secret():
    response = secrets_client.get_secret_value(SecretId=APP_SECRET_NAME)
    return json.loads(response['SecretString'])

def lambda_handler(event, context):
    user_id = event.get('user_id')

    if not user_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'user_id is required'})}

    # Input validation: solo alfanumerici e trattini
    if not all(c.isalnum() or c == '-' for c in user_id):
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid user_id format'})}

    try:
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item')

        if not item:
            return {'statusCode': 404, 'body': json.dumps({'error': 'User not found'})}

        secret = get_app_secret()

        print(json.dumps({'action': 'get_user', 'user_id': user_id, 'status': 'success', 'secret_loaded': True}))

        return {
            'statusCode': 200,
            'body': json.dumps({
                'user': item,
                'secret_loaded': True,
                'secret_key_present': 'demo_token' in secret
            })
        }
    except Exception as e:
        print(json.dumps({'action': 'get_user', 'user_id': user_id, 'status': 'error', 'error': str(e)}))
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}
EOF
zip -q function.zip lambda_function.py
aws lambda create-function --function-name secure-reader --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://function.zip
aws lambda wait function-active-v2 --function-name secure-reader

# Step 9 - Variabili d'ambiente
aws lambda update-function-configuration --function-name secure-reader --environment "Variables={TABLE_NAME=lab09-users,APP_SECRET_NAME=lab09/app-config}"
aws lambda wait function-updated-v2 --function-name secure-reader

# Step 11 - Test: positivo, inesistente, senza user_id, injection
aws lambda invoke --function-name secure-reader --cli-binary-format raw-in-base64-out --payload '{"user_id":"u001"}' out.json && cat out.json; echo
aws lambda invoke --function-name secure-reader --cli-binary-format raw-in-base64-out --payload '{"user_id":"999"}' out.json && cat out.json; echo
aws lambda invoke --function-name secure-reader --cli-binary-format raw-in-base64-out --payload '{}' out.json && cat out.json; echo
aws lambda invoke --function-name secure-reader --cli-binary-format raw-in-base64-out --payload "{\"user_id\":\"'; DROP TABLE users;--\"}" out.json && cat out.json; echo

# Step 12 - Policy least-privilege (documentale: nel Learner Lab si usa LabRole)
ACC=$(aws sts get-caller-identity --query Account --output text)
cat > least-privilege.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": "dynamodb:GetItem", "Resource": "arn:aws:dynamodb:us-east-1:$ACC:table/lab09-users"},
    {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": "arn:aws:secretsmanager:us-east-1:$ACC:secret:lab09/app-config-*"},
    {"Effect": "Allow", "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], "Resource": "arn:aws:logs:us-east-1:$ACC:log-group:/aws/lambda/secure-reader:*"}
  ]
}
EOF
cat least-privilege.json
cd ..
```

### Cleanup

```bash
aws lambda delete-function --function-name secure-reader
aws dynamodb delete-table --table-name lab09-users
aws secretsmanager delete-secret --secret-id lab09/app-config --force-delete-without-recovery     # senza finestra di recupero: con --recovery-window-in-days 7 il nome resta bloccato e un nuovo create-secret fallisce
aws logs delete-log-group --log-group-name /aws/lambda/secure-reader
```
