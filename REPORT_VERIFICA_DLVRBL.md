# Verifica DLVRBL-LAB vs testi dei laboratori — stato attuale

Fonti confrontate (repo `its-javadizavieh`, cartella `labs/`):

- Sicurezza AWS: sorgenti 01-11, DLVRBL 01-10 (**manca il DLVRBL del lab 11 Backup e ripristino**)
- VM Reti Storage: sorgenti 01-13, DLVRBL 1-11 (**mancano i DLVRBL dei lab 12 Bilanciamento/IAM e 13 CloudTrail/CloudWatch**)
- Serverless: sorgenti 01-18 (08 e 09 sono un solo file), DLVRBL 01-18 (tutti coperti)

Criteri: (1) il DLVRBL contiene tutte le informazioni tecniche per rifare il lab; (2) italiano e contenuto sembrano scritti da uno studente che padroneggia il tema.

Dopo la prima verifica sono stati corretti tutti i punti risolvibili senza un account AWS. Restano i punti che richiedono l'esecuzione sul Learner Lab o dati dello studente (ID reali, output osservati).

## Giudizio sintetico

| Corso | Completezza tecnica | Impronta "studente competente" |
|---|---|---|
| Serverless | Alta. Calcoli, costi, CORS, `jq`, break-even e classificazione RAEE corretti; restano prove da eseguire (lab 09, 11, 12, 14, 17, 18) | Alta nei lab 06-18; accenti e frasi sistemati nei lab 01-05 |
| Sicurezza | Alta. Aggiunti step 9 (lab 01), schemi VPN/Direct Connect (07), motivazioni A-D (08), controlli motivati (09), schede e responsabili per caso (10) | Media-alta. Restano alcune evidenze solo dichiarate (non osservate) |
| VM Reti Storage | Media-alta. Cleanup completi e autonomi, nomi coerenti, scelta Storage Gateway motivata | Media. I lab 1-7 restano con valori illustrativi finché non si esegue il Learner Lab |

## Cosa è stato corretto

### Trasversale
- Accenti ripristinati in tutti i DLVRBL (perché, già, più, può, parole in -ità, "è", "né", "sì").
- Segnaposto `sì/no`, `<...>`, "(screenshot)", riferimenti a "PDF di svolgimento" e a `0. Lab tutti.sh` sostituiti con testo onesto (valore ricavabile dal comando, oppure "da confermare dopo l'esecuzione"). Nessun valore è stato inventato.
- Cleanup resi autonomi: nessun DLVRBL rimanda più a "cleanup finale di un altro lab" senza fornire i comandi.
- Checkpoint che dichiaravano cose non provate sono stati spuntati solo se la cosa è descritta nel documento; gli altri restano `[ ]`.
- Frasi meta o fuori tono riscritte (Sic 05, VM 1, VM 5, VM 8).

### Sicurezza AWS
| Lab | Correzione |
|---|---|
| 01 | Step 9 aggiunto (due ambiguità corrette, simulazione perdita credenziale lettore, impatto residuo). Diagramma del flusso rifatto. La revisione con il collega resta da svolgere. |
| 03 | Nota sul ruolo del lab riscritta; cleanup del primo blocco CLI elimina anche l'alias. |
| 04 | Dichiarato che la simulazione AWS non è stata eseguita (valutazione manuale); checkbox aggiornate. |
| 05 | Frase sugli screenshot riscritta; accenti. |
| 06 | Spiegazione di NACL deny di default e ordine delle regole; sezione per annotare gli ID creati; cleanup autonomo. |
| 07 | Aggiunti due schemi di collegamento (VPN, Direct Connect); cleanup autonomo; accenti. |
| 08 | Motivazione dei casi A-D; "(screenshot)" tolto; cleanup autonomo. |
| 09 | Esiti WAF dichiarati come dedotti (nessun traffico, quindi `Count` a 0); sezione "scelta motivata dei controlli" (Count/Block, Secrets Manager, Shield). |
| 10 | Regione nelle schede G1/G2; priorità motivata; tempi motivati; tabella responsabile / prova di chiusura / rischio residuo per V1-V4. |

### VM Reti Storage
| Lab | Correzione |
|---|---|
| 1 | Blocchi PowerShell e bash separati; riga SSH corretta; checkpoint e nota coerenti (valori illustrativi dichiarati). |
| 2 | Cleanup con attese (`wait`), snapshot eliminato; key pair e SG conservati per il lab 3. |
| 3 | ASG `demo-asg-web` in tutti i comandi; cleanup chiaro; deregistrazione delle istanze originali scritta con comandi. |
| 4 | Cleanup con comandi; tabella dei CIDR non più incollata nei commenti con tab sbagliati. |
| 5 | Cleanup completo (rotta blackhole, route table pubblica, IGW); configurazione SSH idempotente; blocco SSH non più taggato `bash`. |
| 6 | Cleanup con ripristino della NACL precedente; ID NACL annotato nella variabile `OLD_NACL`. |
| 7 | ID istanza ricavato dal tag; device `/dev/nvme1n1` su t3; segnaposto tolti. |
| 8 | Frase sgrammaticata riscritta; cleanup con comandi. |
| 9 | Scelta Storage Gateway motivata su uno scenario (Tape Gateway) con alternative; AZ presa dall'istanza di destinazione; cleanup del bucket con versioni. |
| 10 | Cleanup completo; controllo con `lsblk`/`blkid` prima di formattare; nota su `xfs` contro `ext4` del lab 7; affermazione "riverificato dopo riavvio" tolta. |
| 11 | Cleanup di rete completo (NAT, route table, IGW, subnet, VPC); accenti. |

### Serverless
| Lab | Correzione |
|---|---|
| 01 | Ufficio `-60%`; `SW_UFFICIO=0.60` (lo script produce 399.920 kWh / 468.480 kWh / 117,1 t); trimestre 91,25 giorni. |
| 02 | Classificazione RAEE separata (raggruppamenti italiani R1-R5 e categorie Allegato III); stima 350 kWh tolta; 0,21 $ spiegato come costo senza free tier. |
| 03 | Tabelle costi rifatte con voci che sommano ai totali (~142 / ~106 / <1 $); `awk` che calcola. |
| 04 | Break-even rifatto in us-east-1 con DynamoDB e scomposizione per voce (~17 M richieste/mese); serie Calculator e Sintesi spiegate. |
| 05 | `pymysql.MySQLError`; colonna rischio compilata; punti 12-15 (IAM minimo, `conn.close()` in `finally`, timeout, scrittura non atomica); codice corretto aggiornato. |
| 06 | Conclusione 128 contro 256 MB; output "Hello, Mario!"; nota sul ritorno a freddo dopo inattività. |
| 07 | Riga `REPORT` senza `...`; conclusione 3 corretta (cold start anche dopo inattività e scale-out); cleanup dichiarato necessario; nota su `utcnow()`. |
| 08 | Soglia dell'allarme coerente (`> 0`); `Insufficient data` spiegato; 256→512 MB e costo reale commentati; avviso su `namePrefix: []`. |
| 09 | Quarto test `{}` (atteso 400, da eseguire); cinque azioni IAM; formulazione su "injection" corretta; confronto con `LabRole`; `bob@example.com`. |
| 10 | Passo 6b CORS (metodo `OPTIONS` MOCK, redeploy, prova del preflight); conclusione corretta; runtime, TLS, stage e descrizione commentati. |
| 11 | Comando `curl` al posto del blocco non valido; 401 contro 403 spiegati; rischio cache 300 s con `Resource=methodArn`; comandi per DELETE e GET per id. |
| 12 | TTL 60 s, prova di cache hit, metriche `CacheHitCount`/`CacheMissCount`, Service Map X-Ray; 403 spiegato; stage variable `dev`; disabilitazione cache nel cleanup. |
| 13 | Testo dell'errore `Float types are not supported`; "altre tre operazioni". |
| 14 | Prova negativa del filtro S3 (comandi e atteso); nota su `unquote_plus`; chiarito che DynamoDB Streams non è usato. |
| 15 | Passi per completare la prova TTL e per il ripristino PITR. |
| 17 | `Cause` fuorviante segnalata; limiti dei retry osservati; comando per leggere la cronologia. |
| 18 | `jq` corretto (`results`, attesa `Complete`); verifica stato `ALARM`; cleanup di log group e bucket SAM; test locale dichiarato non eseguito. |

## Ancora da fare (richiede AWS o dati dello studente)

- Eseguire le procedure CLI e sostituire i valori illustrativi con quelli osservati: VM 1-7 (ID, IP, status check, tempi), VM 9-11 (ID), Sicurezza 04 (simulatore), Sicurezza 06 (ID risorse).
- Completare le prove descritte ma non eseguite: Serverless 09 (test `{}`), 11 (DELETE, GET per id, 401 e 403), 12 (cache hit e metriche), 14 (prova negativa del filtro), 17 (2-3 retry ed esaurimento), 18 (GET/404, `ALARM`, query Logs Insights), 15 (scadenza TTL e ripristino PITR).
- Verificare con il Pricing Calculator le cifre ricalcolate a mano in Serverless 03 e 04.
- Scambio con un collega (Sicurezza 01 step 9).
- Allegare gli screenshot o i log citati nei DLVRBL dove servono come evidenza.
- DLVRBL mancanti: Sicurezza 11, VM 12 e 13 (se fanno parte della consegna).
- Terraform: i lab Sicurezza 06-10 dichiarano "creato con Terraform" e un `terraform destroy` con 36 risorse. Il lab non lo richiede e il codice non è nel repo: allegarlo o indicare che la procedura CLI è equivalente. Nei DLVRBL VM 8-11 la dicitura è stata sostituita da quella reale (AWS CLI).

## Limiti di questa verifica

- Sorgenti VM 2-11 e Serverless 03-18 letti solo nelle prime parti (obiettivo, scenario, step, output): checkpoint finali e troubleshooting non confrontati riga per riga.
- Nessun comando AWS eseguito. Le correzioni agli script (Serv 01, 03, 04, 18; VM 3, 5, 6) derivano da lettura e calcolo a mano; solo i numeri di Serv 01 e le cifre di Serv 03 e 04 sono stati ricalcolati con `awk`.
- I prezzi usati (us-east-1) sono quelli pubblici noti al momento della verifica e vanno ricontrollati.
- Il testo dell'Allegato III (6 categorie dal 15/08/2018) in Serv 02 viene da conoscenza, non da una fonte riverificata.
- Gli screenshot citati nei DLVRBL non sono presenti nel repo: i valori "osservati" non sono verificabili.

## Verifica eseguita su AWS Learner Lab (17-18/11/2026)

Le procedure CLI dei DLVRBL sono state eseguite su un account Learner Lab (us-east-1), blocco per blocco, con uno screenshot per passo in `CORSO_*/screenshots-<corso>/lab-N/` (immagini PNG dei comandi e dell'output reale, più i log `log-*.txt`). Eseguiti: Sicurezza 1-10, VM Reti Storage 1-11, Serverless 1-18 (i lab 1, 3, 4 e 5 sono calcoli e controlli locali). Tutte le risorse sono state eliminate; restano solo un segreto e una chiave KMS in cancellazione pianificata (lab Sicurezza).

Limiti: gli screenshot non sono schermate della console AWS ma output di terminale; alcuni lab (Serverless 15-17, Sicurezza 1-5) hanno un solo screenshot per blocco perché la procedura non ha commenti di passo; la prova di scadenza TTL e il ripristino PITR (Serverless 15) e la prova X-Ray Service Map (Serverless 12, `AccessDenied`) non sono stati completati.

### Difetti trovati e corretti nei DLVRBL
| Lab | Problema osservato | Correzione |
|---|---|---|
| Sicurezza 04, 05 | `--policy-input-list file://...` dà `InvalidInput` | `"$(cat file)"` |
| Sicurezza 07 | l'evento CloudTrail compare dopo 3-10 minuti | attesa e nota |
| Sicurezza 09 | `SearchString` WAF non valida in chiaro (`Invalid base64`) | valore base64 |
| Sicurezza 10 | `Service.AdditionalInfo.sample` restituisce `None` | `Service.AdditionalInfo.Value` |
| VM 1 | `sleep 30` insufficiente prima del `curl` | ciclo di retry |
| VM 2 | target `initial` subito dopo la creazione dell'ALB | `wait target-in-service`; aggiunta prova di health check |
| VM 3 | tempo di sostituzione ASG "alcuni minuti" | circa 2 s per il lancio, 1-3 min per `healthy` |
| VM 8 | blocco di eliminazione del bucket eseguito come passo normale | intestazione `### Cleanup` |
| VM 10 | nome DNS EFS generico non risolto; SSM asincrono; cleanup lascia la subnet 1b | `az=` con `until`, `ssm wait`, eliminazione subnet |
| Serverless 02, 14 | l'upload subito dopo la notifica S3 non genera l'evento | attesa di 45 s |
| Serverless 08 | payload 1.000.000 di iterazioni, tabella calcolata con 100.000 | payload 100000 |
| Serverless 09 | segreto non ricreabile dopo `--recovery-window-in-days 7`; test `{}` non verificato | `--force-delete-without-recovery`; test verificato (400) |
| Serverless 11 | `UID` è sola lettura in bash; `DELETE` con token valido dopo `POST` dà 403 (policy in cache solo per `methodArn`) | `USER_ID`; `Resource` con wildcard |
| Serverless 12 | `--patch-operations` in sintassi abbreviata fallisce con le virgole; deploy ravvicinati (`TooManyRequests`); `prod` e cache non pronti subito | formato JSON, pause, attesa `cacheClusterStatus` |
| Serverless 18 | `delete-bucket` del bucket SAM fallisce (`BucketNotEmpty`, versioning) | eliminazione di versioni e delete marker |

### Da decidere o confermare
- Nomi di bucket (`sicurezza02-riccardogouthier`, `lab07-trigger-gouthier`, `lab14-*-gouthier`, `lab15-lifecycle-riccardogouthier`): mantenuti nei DLVRBL perché derivano da test passati dello studente; nei test di verifica è stato aggiunto un suffisso perché risultavano già occupati.
- Serverless 06: il DLVRBL riporta ora sia il rilevamento studente sia il rilevamento di verifica (a caldo a 128 MB: 13,61 ms contro 1,63 ms).
- Terraform: citato in Sicurezza 06-10 senza codice nel repository; si aggiunge solo se un laboratorio lo richiede esplicitamente.
- Sicurezza 11, VM 12 e 13: in corso di esecuzione a cura dello studente (in attesa).
