# Deliverable Lab 08 - S3: versioning e lifecycle

## Obiettivo
Bucket S3 con versioning attivo e regola di lifecycle, verificando che sovrascrittura ed eliminazione non causino perdita definitiva dei dati.

## Configurazione
- Regione `us-east-1`. Il bucket e la sua configurazione sono stati creati con AWS CLI, perché la SCP del Learner Lab nega a Terraform la lettura dell'object lock
- Bucket: `demo-vm-reti-storage-rg-2026`, Block all public access attivo, Bucket Versioning `Enabled`

## Versioni di `report.txt`
| Versione | Stato | Dimensione | Version ID |
|---|---|---|---|
| v1 (contenuto originale) | non corrente | 32 byte | `IJqxHGvTWQvpo7Hh2ILOFg8Ns4sm.wT9` |
| v2 (sovrascritta) | corrente | 56 byte | `0nswNgv4owWsEfmozDMfrEMLOiIz4FP6` |

## Lifecycle
Regola `demo-lifecycle-standard-ia`:
- ambito: intero bucket
- azione: transizione delle versioni non correnti a Standard-IA dopo 30 giorni
- la transizione non viene attesa: contano 30 giorni dalla perdita di corrente, e i file sotto 128 KB non transitano con il comportamento predefinito

## Eliminazione e recupero
- Eliminando `report.txt`, con "Show versions" attivo compare il delete marker `BS9QzPa_O7074w8c4985rnGdhzJVxxF_` e le due versioni restano presenti
- Rimuovendo solo il delete marker, `report.txt` torna visibile e leggibile; contenuto: `report v2 - contenuto modificato dopo la sovrascrittura`

## Motivazione scelte
- Versioning: la sovrascrittura crea una nuova versione, la vecchia resta recuperabile
- Delete marker: l'eliminazione semplice non cancella i dati; il recupero e togliere il marker
- Lifecycle su versioni non correnti: contiene i costi delle versioni vecchie senza toccare quella corrente

## Evidenza
| # | Elemento | Evidenza sintetica |
|--:|---|---|
| 1 | Bucket | `demo-vm-reti-storage-rg-2026`, versioning `Enabled`, accesso pubblico bloccato |
| 2 | Versioni | v1 32 byte non corrente, v2 56 byte corrente |
| 3 | Lifecycle | `demo-lifecycle-standard-ia`, non correnti -> Standard-IA a 30 giorni |
| 4 | Delete marker | `BS9QzPa_O7074w8c4985rnGdhzJVxxF_`, due versioni ancora presenti |
| 5 | Recupero | marker rimosso, `report.txt` leggibile (v2) |

## Screenshot e log
Cartella: `screenshots-vm-reti-storage/lab-8/`

- `log-lab-8.txt`
- `passo-02.png`
- `passo-03.png`
- `passo-04.png`
- `passo-05.png`
- `passo-06.png`
- `passo-07.png`
- `passo-08.png`
- `passo-09.png`

## Checkpoint
- [x] Versioning attivo e due versioni distinte
- [x] Delete marker osservato, nessuna perdita dei dati
- [x] Recupero verificato rimuovendo il marker
- [x] Lifecycle configurato (transizione non attesa, dichiarato)
- [x] Cleanup descritto in questo documento (sezione Cleanup)

## Cleanup
- Bucket conservato per il Lab 09
- Eliminazione finale a fine percorso: si rimuovono tutte le versioni e tutti i delete marker, poi il bucket (comandi nella sezione "Cleanup" in fondo).

## Nota metodologica
Version ID e delete marker sono valori osservati. La transizione lifecycle non è provata: richiede 30 giorni.

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
BUCKET=demo-vm-reti-storage-rg-2026

# Step 1 - Bucket con Block all public access
aws s3api create-bucket --bucket $BUCKET
aws s3api put-public-access-block --bucket $BUCKET --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Step 2 - Versioning Enabled
aws s3api put-bucket-versioning --bucket $BUCKET --versioning-configuration Status=Enabled
aws s3api get-bucket-versioning --bucket $BUCKET
sleep 15    # propagazione della prima abilitazione

# Step 3 - Prima versione di report.txt
echo "report v1 - contenuto originale" > report.txt
aws s3api put-object --bucket $BUCKET --key report.txt --body report.txt --query VersionId --output text

# Step 4 - Sovrascrittura: seconda versione
echo "report v2 - contenuto modificato dopo la sovrascrittura" > report.txt
aws s3api put-object --bucket $BUCKET --key report.txt --body report.txt --query VersionId --output text
aws s3api list-object-versions --bucket $BUCKET --prefix report.txt --query "Versions[].{VersionId:VersionId,IsLatest:IsLatest,Size:Size}"

# Versione precedente: scaricarla e confrontare il contenuto
V1=$(aws s3api list-object-versions --bucket $BUCKET --prefix report.txt --query "Versions[?IsLatest==\`false\`].VersionId | [0]" --output text)
aws s3api get-object --bucket $BUCKET --key report.txt --version-id $V1 report-v1.txt > /dev/null && cat report-v1.txt

# Step 5 - Lifecycle: versioni non correnti a Standard-IA dopo 30 giorni, ambito intero bucket
cat > lifecycle.json <<'EOF'
{
  "Rules": [
    {
      "ID": "demo-lifecycle-standard-ia",
      "Status": "Enabled",
      "Filter": {},
      "NoncurrentVersionTransitions": [
        {"NoncurrentDays": 30, "StorageClass": "STANDARD_IA"}
      ]
    }
  ]
}
EOF
aws s3api put-bucket-lifecycle-configuration --bucket $BUCKET --lifecycle-configuration file://lifecycle.json
aws s3api get-bucket-lifecycle-configuration --bucket $BUCKET

# Step 6 - Eliminazione semplice: crea un delete marker, le versioni restano
aws s3api delete-object --bucket $BUCKET --key report.txt
aws s3api list-object-versions --bucket $BUCKET --prefix report.txt --query "{Versions:Versions[].VersionId,DeleteMarkers:DeleteMarkers[].VersionId}"
aws s3 ls s3://$BUCKET/        # report.txt non compare più nella vista normale

# Step 7 - Recupero: rimuovere solo il delete marker
DM=$(aws s3api list-object-versions --bucket $BUCKET --prefix report.txt --query "DeleteMarkers[?IsLatest==\`true\`].VersionId | [0]" --output text)
aws s3api delete-object --bucket $BUCKET --key report.txt --version-id $DM
aws s3 cp s3://$BUCKET/report.txt - 
```

Il bucket resta per il Lab 09.

### Cleanup (a fine percorso)

Eliminazione finale: prima tutte le versioni e i delete marker, poi il bucket.

```bash
aws s3api list-object-versions --bucket $BUCKET --query "Versions[].[Key,VersionId]" --output text | while read K V; do aws s3api delete-object --bucket $BUCKET --key "$K" --version-id "$V" > /dev/null; done
aws s3api list-object-versions --bucket $BUCKET --query "DeleteMarkers[].[Key,VersionId]" --output text | while read K V; do aws s3api delete-object --bucket $BUCKET --key "$K" --version-id "$V" > /dev/null; done
aws s3api delete-bucket --bucket $BUCKET
```
