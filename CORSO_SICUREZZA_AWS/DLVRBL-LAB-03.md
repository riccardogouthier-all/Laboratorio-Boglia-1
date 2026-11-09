# Consegna Lab 03 - Compliance, KMS e identità

## 1. Trust policy vs permessi
- Trust policy: definisce chi può assumere un ruolo.
- Policy di permesso: definisce quali azioni sono consentite.
- Nota: ruolo lab [visibile, trust policy letta senza modifiche | non visibile, usato caso guidato].

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
aws kms schedule-key-deletion --key-id $KEY_ID --pending-window-in-days 7 --region us-east-1

aws kms describe-key --key-id $KEY_ID --region us-east-1 --query 'KeyMetadata.[KeyState,DeletionDate]' --output text

rm chiaro03.txt cifrato03.b64 cifrato03.bin decifrato03.b64 decifrato03.txt

ls
```