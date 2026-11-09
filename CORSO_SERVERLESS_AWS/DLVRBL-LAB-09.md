# Laboratorio 09 - Sicurezza IAM con DynamoDB e Secrets Manager

Autore: Riccardo Gouthier (Gruppo 2). Corrisponde alla Parte B del "Lab 08-09".

## Scenario

Lambda `secure-reader` che legge un utente da DynamoDB e carica un segreto da Secrets Manager, con validazione dell'input e permessi IAM minimi (least privilege).

## Step 6 - Tabella DynamoDB

- Tabella: `lab09-users`
- Partition key: `user_id` (String)
- Modalita capacita: On-demand
- Creata il 21 settembre 2026, 17:17 (UTC+02:00)

## Step 7 - Dati di test

| user_id | email | name |
|---|---|---|
| u001 | alice@example.com | Alice |
| u002 | bob@exam... | Bob |

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

Evento di test: `hello-world`.

| # | Input | Tipo | Risposta |
|---|---|---|---|
| 1 | `user_id` = `u001` | Positiva | 200, utente Alice, `secret_loaded: true`, `secret_key_present: true` |
| 2 | `user_id` = `999` (inesistente) | Negativa (deve dare errore) | 404 `User not found` |
| 3 | `user_id` = `"'; DROP TABLE users;--"` | Negativa (injection) | 400 `Invalid user_id format` |

## Step 12 - Azioni IAM minime richieste

| # | Azione | Risorsa |
|---|---|---|
| 1 | `dynamodb:GetItem` | tabella `lab09-users` |
| 2 | `secretsmanager:GetSecretValue` | segreto `lab09/app-config` |
| 3 | `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` | log della funzione |

## Conclusioni

1. Le credenziali non stanno nel codice: il segreto e letto a runtime da Secrets Manager e non viene mai restituito in chiaro.
2. La validazione del formato di `user_id` blocca input malevoli (test SQL injection -> 400).
3. Il ruolo della funzione deve avere solo le tre azioni elencate, ciascuna limitata alla propria risorsa.
