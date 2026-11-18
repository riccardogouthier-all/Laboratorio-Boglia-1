# Deliverable Lab 04 - IAM: buone pratiche, MFA e policy JSON

## Configurazione
- Strumento: IAM Policy Simulator (https://policysim.aws.amazon.com/), modalità **Custom**
- Risorsa fittizia: bucket `didattica-esempio` (non esiste, simulatore non esegue operazioni S3)
- Policy base: `AllowReadReports` (Allow `s3:GetObject` su `report/*`) + `DenyDeleteObjects` (Deny `s3:DeleteObject` su `*`)
- Policy MFA: policy base + `DenyReadReportsWithoutMFA` (Deny `s3:GetObject` su `report/*`, condizione `BoolIfExists` `aws:MultiFactorAuthPresent` = `false`)
- Nessun utente, gruppo, ruolo, dispositivo MFA creato o allegato

## Motivazione scelte
- Deny esplicito su `s3:DeleteObject`: prevale su qualsiasi Allow
- Nessun Allow su `privato/` e `ListBucket` → `implicitDeny` (default deny, minimo privilegio)
- `BoolIfExists` + `false`: Deny anche quando la chiave MFA è assente → copre sessioni senza MFA
- Simulatore: verifica policy senza creare risorse né costi

## Policy base (punto 1)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadReports",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::didattica-esempio/report/*"
    },
    {
      "Sid": "DenyDeleteObjects",
      "Effect": "Deny",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::didattica-esempio/*"
    }
  ]
}
```

## Policy MFA (punto 3)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadReports",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::didattica-esempio/report/*"
    },
    {
      "Sid": "DenyDeleteObjects",
      "Effect": "Deny",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::didattica-esempio/*"
    },
    {
      "Sid": "DenyReadReportsWithoutMFA",
      "Effect": "Deny",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::didattica-esempio/report/*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
}
```

## Casi base (policy base)
| # | Azione | ARN risorsa | Valore | Motivo |
|--:|---|---|---|---|
| 1 | `s3:GetObject` | `arn:aws:s3:::didattica-esempio/report/a.txt` | `allowed` | Allow sul prefisso `report/` |
| 2 | `s3:DeleteObject` | `arn:aws:s3:::didattica-esempio/report/a.txt` | `explicitDeny` | Deny sulla cancellazione |
| 3 | `s3:GetObject` | `arn:aws:s3:::didattica-esempio/privato/a.txt` | `implicitDeny` | Nessun Allow su `privato/` |
| 4 | `s3:ListBucket` | `arn:aws:s3:::didattica-esempio` | `implicitDeny` | Nessun Allow per elencare il bucket |

## Casi MFA (policy MFA, `s3:GetObject` su `report/a.txt`)
| # | `aws:MultiFactorAuthPresent` | Valore | Motivo |
|--:|---|---|---|
| 5 | `true` | `allowed` | Deny condizionale non si applica, Allow consente lettura |
| 6 | `false` | `explicitDeny` | Condizione `BoolIfExists` soddisfatta → Deny |
| 7 | chiave omessa | `explicitDeny` | `BoolIfExists` tratta chiave assente come match → Deny |

Il valore MFA è simulato: nessun dispositivo MFA reale abilitato o verificato.

## Verifica CLI (facoltativa)
```bash
aws iam simulate-custom-policy --policy-input-list "$(cat policy04.json)" --action-names s3:GetObject s3:DeleteObject --resource-arns arn:aws:s3:::didattica-esempio/report/a.txt --query 'EvaluationResults[].[EvalActionName,EvalDecision]'
```
```bash
aws iam simulate-custom-policy --policy-input-list "$(cat policy04_mfa.json)" --action-names s3:GetObject --resource-arns arn:aws:s3:::didattica-esempio/report/a.txt --context-entries ContextKeyName=aws:MultiFactorAuthPresent,ContextKeyValues=false,ContextKeyType=boolean --query 'EvaluationResults[].[EvalActionName,EvalDecision]'
```

## Esecuzione simulazione AWS
- Simulazione AWS: non eseguita in questo documento. I 7 casi sono valutati a mano con la logica di valutazione IAM (un `Deny` esplicito prevale su qualsiasi `Allow`; senza `Allow` vale il rifiuto implicito).
- Limite: le decisioni non sono confermate dal simulatore. I comandi per confermarle sono nella procedura CLI qui sotto.

## Checkpoint
- [x] 4 casi base simulati, decisione e motivo registrati
- [x] 3 casi MFA simulati, decisione e motivo registrati
- [x] Chiave MFA impostata nel contesto della simulazione, non in Edit resources
- [ ] Previsioni confrontate con risultati del simulatore (da fare eseguendo i comandi della procedura CLI)
- [x] Dichiarato se simulazione AWS eseguita

Procedura di esecuzione in CLI Cloudshell:

Il lab usa l'IAM Policy Simulator; da CloudShell lo stesso esito si ottiene con `aws iam simulate-custom-policy` (nessuna risorsa creata, nessun costo).

```bash
export AWS_DEFAULT_REGION=us-east-1

# Policy base (punto 1)
cat > policy04.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "AllowReadReports", "Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::didattica-esempio/report/*"},
    {"Sid": "DenyDeleteObjects", "Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "arn:aws:s3:::didattica-esempio/*"}
  ]
}
EOF

# Policy MFA (punto 3)
cat > policy04_mfa.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "AllowReadReports", "Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::didattica-esempio/report/*"},
    {"Sid": "DenyDeleteObjects", "Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "arn:aws:s3:::didattica-esempio/*"},
    {"Sid": "DenyReadReportsWithoutMFA", "Effect": "Deny", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::didattica-esempio/report/*",
     "Condition": {"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}}}
  ]
}
EOF

# Casi base 1-4
sim() { aws iam simulate-custom-policy --policy-input-list "$(cat $1)" --action-names $2 --resource-arns $3 "${@:4}" --query 'EvaluationResults[].[EvalActionName,EvalResourceName,EvalDecision]' --output text; }
sim policy04.json s3:GetObject    arn:aws:s3:::didattica-esempio/report/a.txt     # allowed
sim policy04.json s3:DeleteObject arn:aws:s3:::didattica-esempio/report/a.txt     # explicitDeny
sim policy04.json s3:GetObject    arn:aws:s3:::didattica-esempio/privato/a.txt    # implicitDeny
sim policy04.json s3:ListBucket   arn:aws:s3:::didattica-esempio                  # implicitDeny

# Casi MFA 5-7 (chiave MFA nel contesto della simulazione)
sim policy04_mfa.json s3:GetObject arn:aws:s3:::didattica-esempio/report/a.txt --context-entries ContextKeyName=aws:MultiFactorAuthPresent,ContextKeyValues=true,ContextKeyType=boolean    # allowed
sim policy04_mfa.json s3:GetObject arn:aws:s3:::didattica-esempio/report/a.txt --context-entries ContextKeyName=aws:MultiFactorAuthPresent,ContextKeyValues=false,ContextKeyType=boolean   # explicitDeny
sim policy04_mfa.json s3:GetObject arn:aws:s3:::didattica-esempio/report/a.txt                                                                                                         # chiave omessa: explicitDeny
```

Se il ruolo del Learner Lab non permette `iam:SimulateCustomPolicy`, usare il Policy Simulator in console (modalità Custom) e dichiarare la valutazione manuale. Cleanup: `rm policy04.json policy04_mfa.json`.
