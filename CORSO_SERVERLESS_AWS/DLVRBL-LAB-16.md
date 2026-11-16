# Laboratorio 16 - Step Functions: workflow di elaborazione ordini

Autore: Riccardo Gouthier. Regione `us-east-1`, 12 novembre 2026.

## Scenario

Un workflow Step Functions orchestra tre funzioni Lambda per elaborare un ordine: validazione, sconto condizionale e conferma.

## Flusso

```
Start -> ValidateOrder -> CheckAmount (Choice)
                              |-- total > 100 --> ApplyDiscount --+
                              |-- Default ---------------------------> ConfirmOrder -> Success
```

## Step 1 - Funzioni Lambda

Runtime Python 3.12, ruolo `LabRole`:

| Funzione | Comportamento |
|---|---|
| `validate-order` | Se `total <= 0` solleva `ValueError("Invalid order total: ...")`, altrimenti restituisce `status: validated` |
| `apply-discount` | Sconto del 10%: `total` ridotto, restituisce `original_total`, `discount`, `status: discounted` |
| `confirm-order` | Restituisce `status: confirmed` e il messaggio `Order {id} confirmed. Total: {total} EUR` |

Le tre funzioni risultano nella lista Lambda (`validate-order`, `apply-discount`, `confirm-order`), tutte Python 3.12.

## Step 2 - State machine `order-processor`

- Tipo: Standard, stato `Active`, ruolo `LabRole`, X-Ray disattivato
- Creata il 12 novembre 2026, 12:33:21 (UTC+01:00)
- Integrazione `arn:aws:states:::lambda:invoke` con `OutputPath: $.Payload`

| Stato | Tipo | Transizione |
|---|---|---|
| `ValidateOrder` | Task (Lambda) | -> `CheckAmount` |
| `CheckAmount` | Choice | `$.total > 100` -> `ApplyDiscount`; altrimenti (Default) -> `ConfirmOrder` |
| `ApplyDiscount` | Task (Lambda) | -> `ConfirmOrder` |
| `ConfirmOrder` | Task (Lambda) | -> `Success` |
| `Success` | Succeed | fine |

## Step 3 - Ordine piccolo

Input `{"order_id":"ORD-001","total":50}` (esecuzione `exec-ord-001`):

- Stato: `Succeeded`, durata 0,733 s, 6 transizioni
- Percorso: `ValidateOrder` -> `CheckAmount` -> `ConfirmOrder` -> `Success`
- `ApplyDiscount` non eseguito (tratteggiato nel grafo): 50 non supera 100

## Step 4 - Ordine grande

Input `{"order_id":"ORD-002","total":200}` (esecuzione `exec-ord-002`):

- Stato: `Succeeded`, durata 0,678 s, 7 transizioni (una in piu: `ApplyDiscount`)
- Percorso: `ValidateOrder` -> `CheckAmount` -> `ApplyDiscount` -> `ConfirmOrder` -> `Success`

## Step 5 - Errore

Input `{"order_id":"ORD-003","total":-10}` (esecuzione `exec-ord-003`):

- Stato: `Failed`, durata 0,167 s, 3 transizioni
- Errore: `ValueError` nello stato `ValidateOrder`
- Causa: `Invalid order total: -10`, con stack trace di `lambda_function.py` riga 8
- `CheckAmount` e gli stati successivi non vengono eseguiti

Il workflow non ha un `Catch`: l'errore della Lambda propaga e fa fallire l'intera esecuzione.

## Riepilogo esecuzioni

| Esecuzione | Input `total` | Percorso | Esito | Durata | Transizioni |
|---|---|---|---|---|---|
| `exec-ord-001` | 50 | senza sconto | Succeeded | 0,733 s | 6 |
| `exec-ord-002` | 200 | con sconto | Succeeded | 0,678 s | 7 |
| `exec-ord-003` | -10 | fallisce in `ValidateOrder` | Failed (`ValueError`) | 0,167 s | 3 |

## Prove

| # | Prova | Tipo | Esito |
|---|---|---|---|
| 1 | Ordine da 50 | Positiva | Ramo Default, nessuno sconto |
| 2 | Ordine da 200 | Positiva | Ramo `$.total > 100`, `ApplyDiscount` eseguito |
| 3 | Ordine da -10 | Negativa | `ValueError`, esecuzione `Failed` |

## Conclusioni

1. Lo stato `Choice` instrada l'esecuzione in base ai dati: la soglia `> 100` decide se applicare lo sconto.
2. Il grafo di esecuzione mostra visivamente gli stati percorsi (verde), saltati (tratteggiati) e falliti (rosso).
3. Senza `Retry`/`Catch` un errore applicativo termina subito il workflow: gestione degli errori affrontata nel Lab 17.

Procedura di esecuzione in CLI Cloudshell:

Le funzioni Lambda sono create con la CLI; la state machine usa lo stesso ASL mostrato in console (Workflow Studio).

```bash
export AWS_DEFAULT_REGION=us-east-1
ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text)
echo $ROLE_ARN

mkdir -p lab16 && cd lab16

cat > validate.py <<'EOF'
import json

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)

    if total <= 0:
        raise ValueError(f"Invalid order total: {total}")

    return {
        'order_id': order_id,
        'total': total,
        'status': 'validated'
    }
EOF

cat > discount.py <<'EOF'
import json

def lambda_handler(event, context):
    total = event['total']
    discount = total * 0.1  # 10% discount
    new_total = round(total - discount, 2)

    return {
        'order_id': event['order_id'],
        'original_total': total,
        'discount': round(discount, 2),
        'total': new_total,
        'status': 'discounted'
    }
EOF

cat > confirm.py <<'EOF'
import json

def lambda_handler(event, context):
    return {
        'order_id': event['order_id'],
        'total': event['total'],
        'status': 'confirmed',
        'message': f"Order {event['order_id']} confirmed. Total: {event['total']} EUR"
    }
EOF

for p in "validate validate-order" "discount apply-discount" "confirm confirm-order"; do
  set -- $p
  cp $1.py lambda_function.py
  zip -q $1.zip lambda_function.py
  aws lambda create-function --function-name $2 --runtime python3.12 --role $ROLE_ARN --handler lambda_function.lambda_handler --zip-file fileb://$1.zip --query "[FunctionName,Runtime,State]" --output text
  aws lambda wait function-active-v2 --function-name $2
done
cd ..
aws lambda list-functions --query "Functions[?starts_with(FunctionName,'validate-')||starts_with(FunctionName,'apply-')||starts_with(FunctionName,'confirm-')].[FunctionName,Runtime]" --output table

REGION=us-east-1
ACC=$(aws sts get-caller-identity --query Account --output text)
VAL=arn:aws:lambda:$REGION:$ACC:function:validate-order
DIS=arn:aws:lambda:$REGION:$ACC:function:apply-discount
CON=arn:aws:lambda:$REGION:$ACC:function:confirm-order

cat > order-processor.asl.json <<EOF
{
  "Comment": "Order processor",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$VAL", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "CheckAmount"
    },
    "CheckAmount": {
      "Type": "Choice",
      "Choices": [
        {"Variable": "\$.total", "NumericGreaterThan": 100, "Next": "ApplyDiscount"}
      ],
      "Default": "ConfirmOrder"
    },
    "ApplyDiscount": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$DIS", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "ConfirmOrder"
    },
    "ConfirmOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "$CON", "Payload.\$": "\$"},
      "OutputPath": "\$.Payload",
      "Next": "Success"
    },
    "Success": {"Type": "Succeed"}
  }
}
EOF

SM_ARN=$(aws stepfunctions create-state-machine --name order-processor --definition file://order-processor.asl.json --role-arn $ROLE_ARN --type STANDARD --query stateMachineArn --output text)
echo $SM_ARN
aws stepfunctions describe-state-machine --state-machine-arn $SM_ARN --query "[name,status,type]" --output text

EX1=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-001 --input '{"order_id":"ORD-001","total":50}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX1 --query "[status,output]" --output text

aws stepfunctions get-execution-history --execution-arn $EX1 --query "events[?type=='TaskStateEntered'||type=='ChoiceStateEntered'].[id,type,stateEnteredEventDetails.name]" --output table

EX2=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-002 --input '{"order_id":"ORD-002","total":200}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX2 --query "[status,output]" --output text
aws stepfunctions get-execution-history --execution-arn $EX2 --query "events[?type=='TaskStateEntered'||type=='ChoiceStateEntered'].[id,type,stateEnteredEventDetails.name]" --output table

EX3=$(aws stepfunctions start-execution --state-machine-arn $SM_ARN --name exec-ord-003 --input '{"order_id":"ORD-003","total":-10}' --query executionArn --output text)
sleep 5
aws stepfunctions describe-execution --execution-arn $EX3 --query "[status,error,cause]" --output text
```

### Cleanup

```bash
aws stepfunctions delete-state-machine --state-machine-arn $SM_ARN
for f in validate-order apply-discount confirm-order; do aws lambda delete-function --function-name $f; done
```
