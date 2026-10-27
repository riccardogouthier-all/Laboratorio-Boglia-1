# Laboratorio 10 - API Gateway REST con Lambda

Autore: Riccardo Gouthier. Regione `us-east-1`, data 18 settembre 2026.

## Scenario

Esporre una Lambda tramite una REST API di API Gateway (risorsa `/hello`, metodo GET), testarla dalla console e dal browser, verificare le intestazioni CORS.

## Flusso

```
Client --GET /hello?name=...--> API Gateway (student-api) --proxy--> Lambda api-hello
```

## Step 1 - Creazione Lambda

- Funzione: `api-hello`
- Runtime: Python 3.14, package Zip

## Step 2 - Creazione API

| Parametro | Valore |
|---|---|
| Nome | `student-api` |
| Descrizione | api di prova per il lab 10 Java Serverless |
| ID | `ja4wdab3x9` |
| Protocollo | REST |
| Endpoint type | Regional |
| Security policy | TLS_1_0 |
| Creata | 2026-09-18 |

## Step 3 - Risorsa e metodo

- Risorsa: `/hello`
- Metodo: `GET`, integrazione Lambda proxy (verso `api-hello`)
- Authorization: NONE; API key required: False

## Step 4 - Test in console

Richiesta `/hello?name=Riccardo`:

| Campo | Valore |
|---|---|
| Status | 200 |
| Latenza | 269 ms |
| Body | `{"message": "Hello, Riccardo!", "method": "GET", "path": "/hello"}` |
| Header risposta | `Access-Control-Allow-Origin: *`, `Content-Type: application/json` |

## Step 5 - Deploy API

- Stage: `Lab-10-Serverless`
- URL: `https://ja4wdab3x9.execute-api.us-east-1.amazonaws.com/Lab-10-Serverless/hello?name=Student`
- Risposta dal browser: `{"message": "Hello, Student!", "method": "GET", "path": "/hello"}`

## Step 6 - CORS

Verifica da DevTools (Network) su `hello?name=Riccardo`:

| Campo | Valore |
|---|---|
| Request method | GET |
| Status | 200 OK |
| `Access-Control-Allow-Origin` | `*` |
| `Content-Type` | `application/json` |
| `Content-Length` | 66 |

## Conclusioni

1. Con l'integrazione proxy la Lambda controlla status, header e body della risposta.
2. L'header `Access-Control-Allow-Origin: *` presente nella risposta consente le chiamate cross-origin dal browser.
3. Le modifiche a metodi e risorse diventano attive solo dopo il deploy su uno stage.
