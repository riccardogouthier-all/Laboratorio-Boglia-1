# Consegna Lab 09 - AWS WAF e Secrets Manager

## WAF
Web ACL `sicurezza09-rg`, creata con Terraform: Regional, `us-east-1`, nessuna risorsa associata (associazioni: 0, screenshot), default action `Allow`.

Regola `osserva-admin`: URI path `starts with` `/admin`, text transformation `NONE`, action `Count`, priority 0.

| Percorso | Corrisponde | Nota |
|---|---|---|
| `/` | no | Count 0 |
| `/admin` | si | Count |
| `/admin/report` | si | Count |
| `/administrator` | si | possibile falso positivo: il confronto e per prefisso |
| `/Admin` | no | confronto case-sensitive |

`Count` osserva senza bloccare: serve a tarare la regola prima di passare a `Block`.

## Secrets Manager
Segreto `sicurezza09/rg`: chiave `aws/secretsmanager`, rotazione e replica disabilitate.

| Versione | Valore | Etichetta |
|---|---|---|
| v1 | `DEMO-NON-VALIDO-v1` | `AWSPREVIOUS` |
| v2 | `DEMO-NON-VALIDO-v2` | `AWSCURRENT` |

(screenshot delle versioni)

Il valore e fittizio: nessun segreto reale.

## Cleanup
Il segreto e in eliminazione pianificata con 7 giorni di recupero, non forzata. Web ACL rimossa con `terraform destroy`.

## Limiti
- Nessuna protezione del traffico reale e stata collaudata (Web ACL senza risorse associate).
- Shield Advanced non attivato.

## Checkpoint
- [x] Web ACL con regola `Count` e 5 esiti attesi motivati
- [x] Segreto con due versioni, `AWSCURRENT`/`AWSPREVIOUS`
- [x] Cleanup dichiarato (segreto in eliminazione pianificata)
- [x] Limiti dichiarati

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
SUF=rg

# ---------- WAF ----------
# Steps 1-13 - Web ACL regionale sicurezza09-SUFFISSO: default Allow, regola osserva-admin (URI path starts with /admin, NONE, Count, priority 0)
cat > rules.json <<'EOF'
[
  {
    "Name": "osserva-admin",
    "Priority": 0,
    "Statement": {
      "ByteMatchStatement": {
        "SearchString": "/admin",
        "FieldToMatch": {"UriPath": {}},
        "TextTransformations": [{"Priority": 0, "Type": "NONE"}],
        "PositionalConstraint": "STARTS_WITH"
      }
    },
    "Action": {"Count": {}},
    "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "osserva-admin"}
  }
]
EOF
aws wafv2 create-web-acl --name sicurezza09-$SUF --scope REGIONAL --region us-east-1 \
  --default-action Allow={} --rules file://rules.json \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=sicurezza09-$SUF
aws wafv2 list-web-acls --scope REGIONAL --region us-east-1 --query "WebACLs[].[Name,Id]" --output table

# Nessuna risorsa associata (associazioni: 0): la Web ACL non protegge traffico reale
WACL_ID=$(aws wafv2 list-web-acls --scope REGIONAL --region us-east-1 --query "WebACLs[?Name=='sicurezza09-$SUF'].Id" --output text)
aws wafv2 list-resources-for-web-acl --web-acl-arn $(aws wafv2 get-web-acl --name sicurezza09-$SUF --scope REGIONAL --id $WACL_ID --region us-east-1 --query WebACL.ARN --output text) --resource-type APPLICATION_LOAD_BALANCER --region us-east-1

# ---------- Secrets Manager ----------
# Steps 14-21 - Segreto sicurezza09/SUFFISSO (chiave aws/secretsmanager, nessuna rotazione/replica), valore v1
aws secretsmanager create-secret --name sicurezza09/$SUF --secret-string '{"password":"DEMO-NON-VALIDO-v1"}' --region us-east-1
# Steps 22-23 - Aggiornare a v2
aws secretsmanager put-secret-value --secret-id sicurezza09/$SUF --secret-string '{"password":"DEMO-NON-VALIDO-v2"}' --region us-east-1
# Step 24 - Versioni: la v2 e AWSCURRENT, la v1 e AWSPREVIOUS
aws secretsmanager list-secret-version-ids --secret-id sicurezza09/$SUF --region us-east-1 --query "Versions[].[VersionId,VersionStages]" --output json
```

Match WAF attesi (osservati dalle metriche Count, nessun traffico reale): `/` no, `/admin` si, `/admin/report` si, `/administrator` si (possibile falso positivo: confronto per prefisso), `/Admin` no (case-sensitive). Non attivare Shield Advanced ne test di carico.

### Cleanup

```bash
LOCK=$(aws wafv2 get-web-acl --name sicurezza09-$SUF --scope REGIONAL --id $WACL_ID --region us-east-1 --query LockToken --output text)
aws wafv2 delete-web-acl --name sicurezza09-$SUF --scope REGIONAL --id $WACL_ID --lock-token $LOCK --region us-east-1
aws secretsmanager delete-secret --secret-id sicurezza09/$SUF --recovery-window-in-days 7 --region us-east-1     # eliminazione pianificata, non forzata
aws secretsmanager describe-secret --secret-id sicurezza09/$SUF --region us-east-1 --query DeletedDate
rm rules.json
```
