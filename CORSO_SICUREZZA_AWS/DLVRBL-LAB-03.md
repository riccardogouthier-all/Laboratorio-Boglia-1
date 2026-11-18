# Consegna Lab 03 - Compliance, KMS e identità

## 1. Trust policy vs permessi
- Trust policy: definisce chi può assumere un ruolo.
- Policy di permesso: definisce quali azioni sono consentite.
- Il ruolo del lab si legge, non si modifica: la trust policy si ottiene con `aws iam get-role --role-name LabRole --query Role.AssumeRolePolicyDocument` (vedi procedura CLI). Se il ruolo non è leggibile nel Learner Lab, si usa il caso guidato descritto nel testo del lab.

## 2. Catena di evidenze
- Requisito: proteggere un dato sintetico (conservare il rapporto cifrato e identificare il soggetto che può usare la chiave).
- Controllo: cifratura con chiave KMS customer managed (symmetric, encrypt and decrypt, alias `sicurezza03-SUFFISSO`, us-east-1).
- Evidenza: testo decifrato uguale all'originale (`cmp` exit=0, nessuna differenza).
- Limite: la cifratura non dimostra da sola che l'accesso IAM sia corretto. Non è una certificazione di conformità.

## 3. Prova di integrità
Ciclo encrypt → decrypt su `chiaro03.txt` da CloudShell; confronto riuscito.
Key ID: 6b2bc32e-48be-480b-a0c1-b7c9ece58665

## 4. Stato finale chiave
- Cancellazione pianificata, finestra 7 giorni.
- Stato: PendingDeletion, data: 2026-10-07.
- Non ancora eliminata; non utilizzabile per operazioni crittografiche.
- File locali eliminati.

## CLI
```
KEY_ID=6b2bc32e-48be-480b-a0c1-b7c9ece58665

aws kms encrypt --key-id $KEY_ID --plaintext fileb://chiaro03.txt --region us-east-1 --query CiphertextBlob --output text > cifrato03.b64

base64 -d cifrato03.b64 > cifrato03.bin

aws kms decrypt --ciphertext-blob fileb://cifrato03.bin --region us-east-1 --query Plaintext --output text > decifrato03.b64

base64 -d decifrato03.b64 > decifrato03.txt

cmp chiaro03.txt decifrato03.txt; echo "exit=$?"
```

**Cleanup**
```
aws kms delete-alias --alias-name alias/sicurezza03-$SUF --region us-east-1

aws kms schedule-key-deletion --key-id $KEY_ID --pending-window-in-days 7 --region us-east-1

aws kms describe-key --key-id $KEY_ID --region us-east-1 --query 'KeyMetadata.[KeyState,DeletionDate]' --output text

rm chiaro03.txt cifrato03.b64 cifrato03.bin decifrato03.b64 decifrato03.txt

ls
```

Procedura di esecuzione in CLI Cloudshell:

```bash
export AWS_DEFAULT_REGION=us-east-1
SUF=riccardogouthier

# Step 1-3 - Trust policy del ruolo del lab (sola lettura, nessuna modifica)
aws iam get-role --role-name LabRole --query Role.AssumeRolePolicyDocument

# Step 4-9 - Chiave KMS customer managed: simmetrica, encrypt and decrypt, alias sicurezza03-SUFFISSO
KEY_ID=$(aws kms create-key --key-spec SYMMETRIC_DEFAULT --key-usage ENCRYPT_DECRYPT --description "sicurezza03-$SUF" --region us-east-1 --query KeyMetadata.KeyId --output text)
aws kms create-alias --alias-name alias/sicurezza03-$SUF --target-key-id $KEY_ID --region us-east-1
echo $KEY_ID

# Step 10-11 - Ciclo encrypt -> decrypt e confronto con l'originale
printf '%s' 'rapporto sintetico 03' > chiaro03.txt
aws kms encrypt --key-id $KEY_ID --plaintext fileb://chiaro03.txt --region us-east-1 --query CiphertextBlob --output text > cifrato03.b64
base64 -d cifrato03.b64 > cifrato03.bin
aws kms decrypt --ciphertext-blob fileb://cifrato03.bin --region us-east-1 --query Plaintext --output text > decifrato03.b64
base64 -d decifrato03.b64 > decifrato03.txt
cmp chiaro03.txt decifrato03.txt; echo "exit=$?"      # exit=0: nessuna differenza
```

### Cleanup (Step 13-14)

```bash
aws kms delete-alias --alias-name alias/sicurezza03-$SUF --region us-east-1
aws kms schedule-key-deletion --key-id $KEY_ID --pending-window-in-days 7 --region us-east-1
aws kms describe-key --key-id $KEY_ID --region us-east-1 --query 'KeyMetadata.[KeyState,DeletionDate]' --output text
rm chiaro03.txt cifrato03.b64 cifrato03.bin decifrato03.b64 decifrato03.txt
ls
```

La chiave risulta `PendingDeletion` (finestra di 7 giorni): non è ancora eliminata e non è utilizzabile per operazioni crittografiche.
