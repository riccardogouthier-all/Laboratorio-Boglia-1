# Consegna Lab 05 - SCP e Access Analyzer (modello locale)

## Ambito
Esercizio svolto in locale: AWS Organizations e IAM Access Analyzer non sono autorizzati nel Learner Lab, quindi non è stata creata nessuna risorsa cloud e non ci sono screenshot della console. Gli identificativi sono fittizi.

## Gerarchia
```
root (FullAWSAccess)
 └─ OU Produzione (FullAWSAccess + SCP Deny s3:DeleteObject)
     └─ account Fabbrica (FullAWSAccess)
```
Il ruolo applicativo ha una policy IAM che consente `s3:GetObject` e `s3:DeleteObject` su `arn:aws:s3:::rapporti-demo/*`.

## Matrice delle decisioni

### Con la SCP Deny attiva
| Azione | Esito | Motivo |
|---|---|---|
| `s3:GetObject` | consentito | IAM lo permette, la SCP non lo nega |
| `s3:DeleteObject` | negato esplicitamente | Deny della SCP prevale sull'Allow IAM |
| `s3:PutObject` | negato implicitamente | nessun Allow IAM |

### Senza la SCP Deny
| Azione | Esito | Motivo |
|---|---|---|
| `s3:GetObject` | consentito | policy IAM |
| `s3:DeleteObject` | consentito | policy IAM |
| `s3:PutObject` | negato implicitamente | nessun Allow IAM |

Cambia soltanto `Delete`. `FullAWSAccess` è un limite, non una concessione: le SCP non assegnano permessi, restringono quelli che IAM può dare.

## Finding Access Analyzer (modello)
| Finding | Problema | Correzione | Prova positiva | Prova negativa |
|---|---|---|---|---|
| A | Accesso del partner troppo ampio | Limitare il partner al prefisso `export/*` | Il partner legge in `export/` | Il partner non legge fuori da `export/` |
| B | Lettura anonima non approvata | Rimuovere l'accesso anonimo, mantenere Block Public Access | - | Una richiesta anonima non legge |

## Limite delle evidenze
Per provare un accesso realmente avvenuto servono log reali (CloudTrail, log di accesso S3) e l'esito di Access Analyzer. Qui il modello è locale: dimostra la logica di valutazione, non lo stato di un account reale.

## Checkpoint
- [x] Gerarchia root -> OU -> account descritta
- [x] Matrice con e senza SCP, differenza limitata a `Delete`
- [x] Finding A e B con correzione e prove positiva/negativa
- [x] Dichiarato che nessuna risorsa cloud è stata creata

Procedura di esecuzione in CLI Cloudshell:

Organizations e Access Analyzer non sono autorizzati nel Learner Lab: nessuna risorsa viene creata. La valutazione IAM + SCP si modella in locale con il simulatore delle policy (la SCP Deny si valuta come policy aggiuntiva con `Deny`).

```bash
export AWS_DEFAULT_REGION=us-east-1

# Policy IAM del ruolo applicativo: Get e Delete su rapporti-demo
cat > iam-ruolo.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObject","s3:DeleteObject"],"Resource":"arn:aws:s3:::rapporti-demo/*"}]}
EOF

# SCP della OU Produzione (letta, non distribuita)
cat > scp-ou.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"s3:DeleteObject","Resource":"*"}]}
EOF

sim() { aws iam simulate-custom-policy --policy-input-list "$@" --action-names s3:GetObject s3:DeleteObject s3:PutObject --resource-arns arn:aws:s3:::rapporti-demo/a.txt --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output table; }

echo "== Con SCP Deny attiva =="    ; sim "$(cat iam-ruolo.json)" "$(cat scp-ou.json)"   # Get allowed, Delete explicitDeny, Put implicitDeny
echo "== Senza SCP Deny =="         ; sim "$(cat iam-ruolo.json)"                       # Get allowed, Delete allowed, Put implicitDeny
```

Finding A e B (accesso partner troppo ampio, lettura anonima) sono modelli locali con identificativi fittizi:

```bash
# Finding A - correzione: partner limitato a export/*
cat > partner-corretta.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:GetObject","Resource":"arn:aws:s3:::rapporti-demo/export/*"}]}
EOF
for K in export/a.txt interno/b.txt; do
  aws iam simulate-custom-policy --policy-input-list "$(cat partner-corretta.json)" --action-names s3:GetObject --resource-arns arn:aws:s3:::rapporti-demo/$K --query 'EvaluationResults[].[EvalResourceName,EvalDecision]' --output text
done     # export/a.txt allowed (prova positiva), interno/b.txt implicitDeny (prova negativa)
```

Limite: per provare un accesso realmente avvenuto servono CloudTrail, log di accesso S3 e Access Analyzer. Se `iam:SimulateCustomPolicy` è negata nel lab, dichiarare la valutazione manuale. Cleanup: `rm iam-ruolo.json scp-ou.json partner-corretta.json`.
