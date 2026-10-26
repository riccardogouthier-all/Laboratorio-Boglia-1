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
| # | Azione | ARN risorsa | Previsto | Ottenuto | Motivo |
|--:|---|---|---|---|---|
| 1 | `s3:GetObject` | `arn:aws:s3:::didattica-esempio/report/a.txt` | `allowed` | _da compilare_ | Allow sul prefisso `report/` |
| 2 | `s3:DeleteObject` | `arn:aws:s3:::didattica-esempio/report/a.txt` | `explicitDeny` | _da compilare_ | Deny sulla cancellazione |
| 3 | `s3:GetObject` | `arn:aws:s3:::didattica-esempio/privato/a.txt` | `implicitDeny` | _da compilare_ | Nessun Allow su `privato/` |
| 4 | `s3:ListBucket` | `arn:aws:s3:::didattica-esempio` | `implicitDeny` | _da compilare_ | Nessun Allow per elencare il bucket |

## Casi MFA (policy MFA, `s3:GetObject` su `report/a.txt`)
| # | `aws:MultiFactorAuthPresent` | Previsto | Ottenuto | Motivo |
|--:|---|---|---|---|
| 5 | `true` | `allowed` | _da compilare_ | Deny condizionale non si applica, Allow consente lettura |
| 6 | `false` | `explicitDeny` | _da compilare_ | Condizione `BoolIfExists` soddisfatta → Deny |
| 7 | chiave omessa | `explicitDeny` | _da compilare_ | `BoolIfExists` tratta chiave assente come match → Deny |

Il valore MFA è simulato: nessun dispositivo MFA reale abilitato o verificato.

## Verifica CLI (facoltativa)
```bash
aws iam simulate-custom-policy --policy-input-list file://policy04.json --action-names s3:GetObject s3:DeleteObject --resource-arns arn:aws:s3:::didattica-esempio/report/a.txt --query 'EvaluationResults[].[EvalActionName,EvalDecision]'
```
```bash
aws iam simulate-custom-policy --policy-input-list file://policy04_mfa.json --action-names s3:GetObject --resource-arns arn:aws:s3:::didattica-esempio/report/a.txt --context-entries ContextKeyName=aws:MultiFactorAuthPresent,ContextKeyValues=false,ContextKeyType=boolean --query 'EvaluationResults[].[EvalActionName,EvalDecision]'
```

## Esecuzione simulazione AWS
- Simulazione AWS effettivamente eseguita: _sì/no_
- Se no (simulatore negato o non raggiungibile): casi valutati manualmente sulla logica di valutazione IAM; limite: decisioni non confermate dal simulatore

## Checkpoint
- [ ] 4 casi base simulati, decisione e motivo registrati
- [ ] 3 casi MFA simulati, decisione e motivo registrati
- [ ] Chiave MFA impostata nel contesto della simulazione, non in Edit resources
- [ ] Previsioni confrontate con risultati
- [ ] Dichiarato se simulazione AWS eseguita
