# Laboratorio 11 - API CRUD con Lambda Authorizer

Autore: Riccardo Gouthier. Regione `us-east-1`, settembre 2026.

## Scenario

API REST per gestire utenti (CRUD su DynamoDB) con un Lambda authorizer che protegge le operazioni di scrittura tramite token.

## Flusso

```
Client --(Authorization: Bearer ...)--> API Gateway (crud-api) --> Lambda simple-authorizer (Allow/Deny)
                                              |
                                              +--> Lambda crud-users --> DynamoDB lab11-users
```

## Step 1 - Tabella DynamoDB

- Tabella: `lab11-users`
- Partition key: `user_id` (String)
- Modalità capacità: On-demand

## Step 2 - Funzione CRUD `crud-users`

| Operazione | Comportamento | Risposta |
|---|---|---|
| `list_users` | `scan` con `Limit=50` | 200 `{users: [...]}` |
| `create_user(body)` | Richiede `name` (altrimenti 400 `name is required`); `user_id` = `str(uuid.uuid4())[:8]`; `email` opzionale (default `''`); `put_item` | 201 con l'item creato |
| `delete_user(user_id)` | `delete_item` con chiave `user_id` | 200 `User {user_id} deleted` |
| `response(status_code, body)` | Costruisce la risposta con `HEADERS` e `json.dumps(body)` | - |

## Step 3 - Lambda authorizer `simple-authorizer`

```python
def lambda_handler(event, context):
    token = event.get('authorizationToken', '')
    method_arn = event.get('methodArn', '')
    # Resource ampio (tutti i metodi dello stage): con la cache a 300 s la stessa policy deve valere per POST e DELETE
    resource = '/'.join(method_arn.split('/')[:2]) + '/*'

    if token == 'Bearer my-secret-token-2025':
        effect = 'Allow'
    else:
        effect = 'Deny'

    return {
        'principalId': 'user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }
```

Nota: il token è un valore di prova del laboratorio, non una credenziale reale.

## Step 4 - API Gateway `crud-api`

| Risorsa | Metodi |
|---|---|
| `/users` | `GET`, `POST` |
| `/users/{id}` | `GET`, `DELETE` |

Integrazione: Lambda proxy verso `crud-users`. API ID `ox5hmvvvu4`, stage `dev`.

## Step 5 - Configurazione authorizer

| Parametro | Valore |
|---|---|
| Nome | `token-auth` (ID `cvnrgz`) |
| Lambda function | `simple-authorizer` (us-east-1) |
| Lambda event payload | Token |
| Token source | `Authorization` |
| Token validation | None |
| Authorization caching | 300 secondi |

Authorizer `token-auth` assegnato ai metodi `POST /users` e `DELETE /users/{id}`; API ridistribuita (deploy) dopo la modifica.

## Step opzionale - Prova negativa

Chiamate `POST` / `DELETE` senza header `Authorization: Bearer my-secret-token-2025` restituiscono un errore di autorizzazione: **401 Unauthorized** se manca l'header `Authorization`, **403 Forbidden** se il token è presente ma l'authorizer risponde `Deny` (token sbagliato). Il codice esatto va annotato eseguendo i due casi (nella procedura CLI i comandi stampano il codice HTTP).

## Test finale

`POST` da Postman con token e body `{"name": "Alice"}`:

```
curl -X POST 'https://ox5hmvvvu4.execute-api.us-east-1.amazonaws.com/dev/users' \
  -H 'Authorization: Bearer my-secret-token-2025' \
  -H 'Content-Type: application/json' \
  -d '{"name": "Alice"}'
```

Poi `GET /users`: **200 OK**, 165 ms, 424 B:

```json
{
  "users": [
    { "email": "", "name": "Alice", "user_id": "a4d0f299" }
  ]
}
```

## Prove

| # | Prova | Tipo | Esito atteso |
|---|---|---|---|
| 1 | `POST /users` con token valido | Positiva | 201, utente creato |
| 2 | `GET /users` dopo il POST | Positiva | 200, elenco con Alice |
| 3 | `POST` / `DELETE` senza token | Negativa | 401 (header assente) o 403 (token sbagliato) |
| 4 | `DELETE /users/{id}` con token | Positiva | 200 `User {id} deleted` (verificato eseguendo la procedura; poi `GET /users/{id}` dà 404) |
| 5 | `GET /users/{id}` | Da verificare | la tabella delle operazioni di `crud-users` non include una lettura per id: il risultato dipende dal codice della funzione e va annotato dopo la prova |

## Conclusioni

1. L'authorizer protegge solo le operazioni di scrittura; le letture restano pubbliche.
2. Il risultato dell'authorizer viene messo in cache 300 s: una modifica del token può non essere immediata. C'è anche un rischio: con `Resource` uguale al solo `methodArn` della richiesta, la policy in cache vale solo per quel metodo e percorso. Provato eseguendo la procedura con questa versione: `DELETE /users/{id}` con token valido, subito dopo un `POST /users` con lo stesso token, ha dato `403` (`no identity-based policy allows the execute-api:Invoke action`). Per questo il codice costruisce un `Resource` più ampio (`arn:aws:execute-api:us-east-1:ACCOUNT:API_ID/dev/*`); l'alternativa è la cache a 0 s.
3. Un token statico nel codice va bene solo per il laboratorio; in produzione servono JWT/Cognito e segreti gestiti.

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
ACC=$(aws sts get-caller-identity --query Account --output text)
mkdir -p lab11 && cd lab11

# Step 1 - Tabella lab11-users
aws dynamodb create-table --table-name lab11-users --attribute-definitions AttributeName=user_id,AttributeType=S --key-schema AttributeName=user_id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab11-users

# Step 2 - Funzione crud-users
cat > lambda_function.py <<'EOF'
import json
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('lab11-users')

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
}

def lambda_handler(event, context):
    method = event['httpMethod']
    path_params = event.get('pathParameters') or {}

    try:
        if method == 'GET' and 'id' in path_params:
            return get_user(path_params['id'])
        elif method == 'GET':
            return list_users()
        elif method == 'POST':
            body = json.loads(event.get('body', '{}'))
            return create_user(body)
        elif method == 'DELETE' and 'id' in path_params:
            return delete_user(path_params['id'])
        else:
            return response(405, {'error': 'Method not allowed'})
    except Exception as e:
        return response(500, {'error': str(e)})

def get_user(user_id):
    result = table.get_item(Key={'user_id': user_id})
    item = result.get('Item')
    if not item:
        return response(404, {'error': 'User not found'})
    return response(200, item)

def list_users():
    result = table.scan(Limit=50)
    return response(200, {'users': result.get('Items', [])})

def create_user(body):
    if 'name' not in body:
        return response(400, {'error': 'name is required'})
    item = {
        'user_id': str(uuid.uuid4())[:8],
        'name': body['name'],
        'email': body.get('email', '')
    }
    table.put_item(Item=item)
    return response(201, item)

def delete_user(user_id):
    table.delete_item(Key={'user_id': user_id})
    return response(200, {'message': f'User {user_id} deleted'})

def response(status_code, body):
    return {'statusCode': status_code, 'headers': HEADERS, 'body': json.dumps(body)}
EOF
zip -q crud.zip lambda_function.py
aws lambda create-function --function-name crud-users --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://crud.zip
aws lambda wait function-active-v2 --function-name crud-users

# Step 3 - Lambda authorizer simple-authorizer (token di prova del laboratorio)
cat > lambda_function.py <<'EOF'
def lambda_handler(event, context):
    token = event.get('authorizationToken', '')
    method_arn = event.get('methodArn', '')
    # Resource ampio (tutti i metodi dello stage): con la cache a 300 s la stessa policy deve valere per POST e DELETE
    resource = '/'.join(method_arn.split('/')[:2]) + '/*'

    if token == 'Bearer my-secret-token-2025':
        effect = 'Allow'
    else:
        effect = 'Deny'

    return {
        'principalId': 'user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }
EOF
zip -q auth.zip lambda_function.py
aws lambda create-function --function-name simple-authorizer --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://auth.zip
aws lambda wait function-active-v2 --function-name simple-authorizer
CRUD_ARN=$(aws lambda get-function --function-name crud-users --query Configuration.FunctionArn --output text)
AUTH_ARN=$(aws lambda get-function --function-name simple-authorizer --query Configuration.FunctionArn --output text)

# Step 4 - API crud-api: /users (GET, POST) e /users/{id} (GET, DELETE)
API_ID=$(aws apigateway create-rest-api --name crud-api --endpoint-configuration types=REGIONAL --query id --output text)
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/'].id" --output text)
USERS_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part users --query id --output text)
ID_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $USERS_ID --path-part '{id}' --query id --output text)

# Step 5 - Authorizer token-auth (header Authorization, cache 300 s)
aws lambda add-permission --function-name simple-authorizer --statement-id apigw-authorizer --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:$ACC:$API_ID/authorizers/*"
AUTHZ_ID=$(aws apigateway create-authorizer --rest-api-id $API_ID --name token-auth --type TOKEN --authorizer-uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$AUTH_ARN/invocations --identity-source method.request.header.Authorization --authorizer-result-ttl-in-seconds 300 --query id --output text)

URI=arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$CRUD_ARN/invocations
# GET /users e GET /users/{id}: pubblici
aws apigateway put-method --rest-api-id $API_ID --resource-id $USERS_ID --http-method GET --authorization-type NONE
aws apigateway put-method --rest-api-id $API_ID --resource-id $ID_ID --http-method GET --authorization-type NONE --request-parameters method.request.path.id=true
# POST /users e DELETE /users/{id}: protetti dall'authorizer
aws apigateway put-method --rest-api-id $API_ID --resource-id $USERS_ID --http-method POST --authorization-type CUSTOM --authorizer-id $AUTHZ_ID
aws apigateway put-method --rest-api-id $API_ID --resource-id $ID_ID --http-method DELETE --authorization-type CUSTOM --authorizer-id $AUTHZ_ID --request-parameters method.request.path.id=true
for M in "$USERS_ID GET" "$USERS_ID POST" "$ID_ID GET" "$ID_ID DELETE"; do
  set -- $M
  aws apigateway put-integration --rest-api-id $API_ID --resource-id $1 --http-method $2 --type AWS_PROXY --integration-http-method POST --uri $URI
done
aws lambda add-permission --function-name crud-users --statement-id apigw-crud --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:$ACC:$API_ID/*/*/users*"

# Step 6 - Deploy stage dev e test
aws apigateway create-deployment --rest-api-id $API_ID --stage-name dev
BASE=https://$API_ID.execute-api.us-east-1.amazonaws.com/dev
curl -s $BASE/users; echo                                                       # lista vuota
curl -s -o /dev/null -w "senza token: %{http_code}\n" -X POST $BASE/users -d '{"name":"Alice"}'   # 401/403
curl -s -X POST $BASE/users -H "Authorization: Bearer my-secret-token-2025" -H "Content-Type: application/json" -d '{"name":"Alice"}'; echo
curl -s $BASE/users; echo                                                       # lista con Alice
USER_ID=$(curl -s $BASE/users | jq -r '.users[0].user_id')   # non UID: in bash è una variabile di sola lettura
curl -s -o /dev/null -w "DELETE senza token: %{http_code}\n" -X DELETE $BASE/users/$USER_ID        # 401 (header assente)
curl -s -o /dev/null -w "DELETE token sbagliato: %{http_code}\n" -X DELETE $BASE/users/$USER_ID -H "Authorization: Bearer sbagliato"   # 403
curl -s -X DELETE $BASE/users/$USER_ID -H "Authorization: Bearer my-secret-token-2025"; echo             # 200 "User ... deleted"
curl -s -o /dev/null -w "GET /users/{id}: %{http_code}\n" $BASE/users/$USER_ID                         # da annotare
cd ..
```

### Cleanup

```bash
aws apigateway delete-rest-api --rest-api-id $API_ID
aws lambda delete-function --function-name crud-users
aws lambda delete-function --function-name simple-authorizer
aws dynamodb delete-table --table-name lab11-users
aws logs delete-log-group --log-group-name /aws/lambda/crud-users
aws logs delete-log-group --log-group-name /aws/lambda/simple-authorizer
```
