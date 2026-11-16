# Consegna 01 — Fondamenti di sicurezza

## Scenario

Un **tecnico** carica rapporti in **S3**. Un **analista** legge i rapporti da S3. Un **responsabile** autorizza la cancellazione dei rapporti. Un'applicazione su **EC2** elabora i rapporti. Attualmente una credenziale condivisa rende difficile attribuire le operazioni ai singoli attori.

## Responsabilità

| Componente | Responsabile | Controllo | Evidenza |
|---|---|---|---|
| Edifici | AWS | Controllo fisico e ambientale | Documentazione AWS (data center) |
| Host fisico | AWS | Hardware e virtualizzazione fisica | Modello di responsabilità condivisa AWS |
| Guest OS EC2 | Cliente | Patching e hardening del sistema operativo | Piano aggiornamenti |
| Libreria applicativa | Cliente | Aggiornamento dipendenze | Versione installata / changelog |
| Accesso ai rapporti | Cliente | Permessi minimi su S3 | Test: lettura consentita, cancellazione negata |
| Classificazione dati | Cliente | Etichetta dati sintetici/riservati | Presente nella consegna |
| Configurazione rete | Cliente | Regole coerenti col flusso tecnico → archivio → analista | Diagramma di flusso |
| Credenziali/sessioni | Cliente | Identità distinguibili (no credenziali condivise) | Log attribuibile per identità |

## Flusso dati

```
Tecnico --(upload)  -->   Archivio S3 --(read)    -->     Analista
                                ^
                                |
                        Responsabile (delete, autorizzato)
                                ^
                                |
                        Applicazione EC2 (elaborazione)
```

## Confini di fiducia

1. **Identità → AWS**: ogni identità (tecnico, analista, responsabile, app EC2) attraversa un confine di fiducia verso i servizi AWS; richiede autenticazione e autorizzazione IAM distinte per ruolo.
2. **Applicazione → S3**: l'applicazione EC2 attraversa un confine di fiducia verso il bucket S3; richiede permessi minimi e ruolo IAM dedicato (no credenziali condivise/hardcoded).

## Controlli

1. **Divulgazione**: accesso in lettura a S3 limitato ai soli prefissi/oggetti necessari (least privilege).
2. **Cancellazione**: operazione DeleteObject consentita esclusivamente all'identità del responsabile.
3. **Mancata attribuzione**: eliminazione delle credenziali condivise; tracciamento delle operazioni per identità/sessione distinguibile (es. CloudTrail per utente/ruolo IAM).

## Prove (positive e negative)

| # | Prova | Tipo | Esito atteso |
|---|---|---|---|
| 1 | Lettore autorizzato legge un rapporto previsto | Positiva (lettura) | Accesso consentito |
| 2 | Lettore non autorizzato tenta lettura fuori perimetro | Negativa (lettura) | Accesso negato |
| 3 | Responsabile cancella un oggetto di test | Positiva (cancellazione) | Cancellazione riuscita |
| 4 | Analista tenta di cancellare lo stesso oggetto | Negativa (cancellazione) | Cancellazione negata |
| 5 | Log/evento mostra identità che ha eseguito l'operazione | Positiva (attribuzione) | Identità univoca tracciata |
| 6 | Operazione con credenziale condivisa | Negativa (attribuzione) | Classificata come controllo non accettabile |

## Nota

Nessuna risorsa AWS creata. Nessuna credenziale reale presente in questo documento.

Procedura di esecuzione in CLI Cloudshell:

Il laboratorio non richiede risorse AWS: la consegna si compila in locale. Da CloudShell si puo creare lo scheletro del documento e raccogliere l'identita con cui si opera (utile alla prova di attribuzione).

```bash
export AWS_DEFAULT_REGION=us-east-1

# Identita della sessione: e il dato che permette di attribuire le operazioni a un singolo attore
aws sts get-caller-identity

# Scheletro di consegna01.md con le otto componenti della responsabilita condivisa
cat > consegna01.md <<'EOF'
# Consegna 01 - Fondamenti di sicurezza

## Scenario
Tecnico carica rapporti in S3; analista li legge; responsabile autorizza la cancellazione; app EC2 li elabora.

## Responsabilita
| # | Componente | Responsabile | Controllo | Evidenza |
|--:|---|---|---|---|
| 1 | Edifici (data center) | AWS | Controllo fisico e ambientale | Documentazione di conformita AWS |
| 2 | Host fisico | AWS | Hardware e hypervisor | Modello di responsabilita condivisa |
| 3 | Guest OS su EC2 | Cliente | Patching e hardening | Piano di aggiornamento |
| 4 | Libreria applicativa | Cliente | Aggiornamento dipendenze | Versione installata / changelog |
| 5 | Accesso ai rapporti | Cliente | Permessi minimi su S3 | Lettura consentita, cancellazione negata all'analista |
| 6 | Classificazione dati | Cliente | Etichetta "sintetici" | Etichetta nella consegna |
| 7 | Configurazione di rete | Cliente | Regole coerenti con il flusso | Diagramma |
| 8 | Credenziali e sessioni | Cliente | Identita distinte | Log attribuibile |
EOF
cat consegna01.md

# (Opzionale) prova di attribuzione: ultimi eventi della propria identita in CloudTrail
aws cloudtrail lookup-events --max-results 5 --query "Events[].[EventTime,EventName,Username]" --output table
```

Le sei prove (positive/negative per lettura, cancellazione e attribuzione) sono descritte nel deliverable; non c'e nulla da cancellare (nessuna risorsa creata). Eliminare `consegna01.md` se contiene dati non sintetici.
