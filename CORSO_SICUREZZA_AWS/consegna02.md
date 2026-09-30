# Consegna 02
## Zone
| Zone name | Zone ID |
| us-east-1a | <ID reale> |
| us-east-1b | <ID reale> |
## Configurazione S3
bucket, regione, ACL disabilitate, BPA attivo, versioning off, SSE-S3
## Prova di lettura
head-object output; download autenticato OK; hash uguali
## Conclusioni
1. Posizione: oggetto in us-east-1; Zone ID = identificatore fisico stabile tra account, Zone name mappato per account.
2. Cifratura: SSE-S3 (AES256) protegge dati a riposo; non limita lettori autorizzati.
3. Accesso: bucket privato; lettura solo con credenziali autenticate.