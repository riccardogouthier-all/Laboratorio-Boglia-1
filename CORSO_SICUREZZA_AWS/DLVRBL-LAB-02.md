# Consegna 02 - Regioni e crittografia dei dati

## Zone (us-east-1)

Comando: 
```
aws ec2 describe-availability-zones --region us-east-1 --query 'AvailabilityZones[].[ZoneName,ZoneId,State]' --output table
```

| Zone name  | Zone ID  | State     |
|------------|----------|-----------|
| us-east-1a | use1-az2 | available |
| us-east-1b | use1-az4 | available |
| us-east-1c | use1-az6 | available |
| us-east-1d | use1-az1 | available |
| us-east-1e | use1-az3 | available |
| us-east-1f | use1-az5 | available |

## Configurazione S3

- Bucket: `sicurezza02-riccardogouthier`
- Regione: `us-east-1`
- Object Ownership: `BucketOwnerEnforced` (ACL disabilitate)
- Block Public Access: `BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets` = `true`
- Versioning: non abilitato
- Default encryption: SSE-S3 (`AES256`)
- Oggetto: `rapporto.txt`, testo sintetico ("Rapporto manutenzione sintetico"), 32 byte

## Prova di lettura

Cifratura a riposo (`head-object`):

```
{
    "Encryption": "AES256",
    "Size": 32
}
```

Download autenticato: `download: s3://sicurezza02-riccardogouthier/rapporto.txt to ./scaricato.txt` riuscito con credenziali della sessione.

Confronto contenuto: `sha256sum rapporto.txt scaricato.txt` -> hash identici

Accesso pubblico (`get-public-access-block`): tutte e 4 le opzioni `true`.

## Conclusioni

1. **Posizione**: oggetto in `us-east-1`. Zone name e Zone ID sono coppie distinte; Zone ID (es. `us-east-1a` = `use1-az2`) identifica la zona fisica in modo stabile, il Zone name puo mappare zone diverse tra account.
2. **Cifratura**: `ServerSideEncryption: AES256` = SSE-S3, protegge i dati a riposo. Non limita i lettori gia autorizzati: chi ha permessi di lettura riceve il contenuto in chiaro.
3. **Accesso**: bucket privato, Block Public Access completo; lettura solo con credenziali autenticate, download riuscito e contenuto coincidente con l'originale.


## CLI

```
  SUF=tuosuffisso
  aws ec2 describe-availability-zones --region us-east-1 --query 'AvailabilityZones[].[ZoneName,ZoneId,State]' --output table
  aws s3api create-bucket --bucket sicurezza02-$SUF --region us-east-1
  aws s3api put-bucket-ownership-controls --bucket sicurezza02-$SUF --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'
  aws s3api put-public-access-block --bucket sicurezza02-$SUF --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-encryption --bucket sicurezza02-$SUF --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
  echo "Rapporto manutenzione sintetico" > rapporto.txt
  aws s3 cp rapporto.txt s3://sicurezza02-$SUF/rapporto.txt
  aws s3api head-object --bucket sicurezza02-$SUF --key rapporto.txt --region us-east-1 --query '{Encryption:ServerSideEncryption,Size:ContentLength}'
  aws s3 cp s3://sicurezza02-$SUF/rapporto.txt scaricato.txt
  sha256sum rapporto.txt scaricato.txt
  aws s3api get-public-access-block --bucket sicurezza02-$SUF
```

**Cleanup**

```
  aws s3 rm s3://sicurezza02-$SUF/rapporto.txt
  aws s3 ls s3://sicurezza02-$SUF/
  aws s3 rb s3://sicurezza02-$SUF
  aws s3api head-bucket --bucket sicurezza02-$SUF
  rm rapporto.txt scaricato.txt
```
