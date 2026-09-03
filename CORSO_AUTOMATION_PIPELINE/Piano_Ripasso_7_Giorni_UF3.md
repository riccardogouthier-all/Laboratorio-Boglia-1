# Piano di ripasso — UF3 Automation & Pipeline con AWS
### 7 giorni per rimetterti in pari prima di ricominciare

Prima di entrare nel dettaglio, un paio di cose che mi sembra utile dirti come se fossi seduto accanto a te con il materiale aperto.

Le nove lezioni non sono nove blocchi indipendenti: raccontano *una storia sola* che si costruisce un pezzo alla volta. La L01 ti dà la mappa (perché si automatizza, cos'è una pipeline). Le L02-L03 aprono il primo stadio di quella mappa, il Source. La L04 apre il secondo, il Build. La L05 ricollega tutto dentro uno strumento vero (GitHub Actions) perché l'AWS Academy spesso è in coda o ha permessi IAM limitati. L'approfondimento AI e il deep dive MCP aggiungono uno strato sopra la pipeline che ormai sai leggere. E la L06 (Eredità) è l'esame generale: prende tutto quello che hai imparato e te lo fa usare su un caso vero, sporco, con un cliente che telefona.

Per questo il ripasso funziona meglio se lo fai **nell'ordine cronologico**: ogni giorno presuppone il vocabolario del giorno prima. Se salti un giorno, il giorno dopo farà più fatica a "agganciarsi".

Ogni giornata è pensata per **45-75 minuti**, divisi così: prima rileggi e ti riappropri dei concetti (io ti spiego il *perché*, non solo il *cosa*), poi fai una piccola azione pratica — anche solo mentale o sulla tastiera per 10 minuti — perché queste sono materie che si fissano rifacendole, non solo rileggendole. Chiudi con un self-check: se rispondi a quelle domande senza guardare gli appunti, sei a posto.

---

## GIORNO 1 — L01: Da ClickOps a Pipeline
### Il perché di tutto il resto

Questa è la lezione fondativa, quella che regge — come dice il tuo stesso materiale — tutte le altre 38 ore dell'unità formativa. Se la ripassi bene, tutto quello che segue avrà uno scheletro dove appoggiarsi.

**Il concetto di fondo: DevOps non è uno strumento, è un cambio di responsabilità.**
Storicamente Dev scrive codice e lo "butta oltre il muro", Ops lo fa girare e si arrangia se qualcosa va storto. Quando qualcosa si rompe in produzione, parte il ping-pong delle colpe. DevOps abbatte quel muro: stesso team, stesso obiettivo, e — punto centrale — **automazione al posto dell'eroismo manuale**. Non è "essere più bravi e più attenti": è togliere di mezzo i passaggi manuali che generano l'errore.

Per tenerlo a mente, usa l'acronimo **CALMS**, che è la bussola di tutto il corso:
- **C**ulture — niente muri, responsabilità condivisa
- **A**utomation — se lo fai a mano due volte, automatizzalo (è il cuore dell'UF3)
- **L**ean — passi piccoli, rilasci frequenti
- **M**easurement — se non lo misuri non lo migliori (da qui nasce DORA)
- **S**haring — la conoscenza è del team, non di una persona sola (ti ritornerà identico, come problema del cliente, nella L06)

**Continuous Integration vs Continuous Delivery vs Continuous Deployment — la distinzione che confonde tutti.**
CI (Continuous Integration) significa che ogni modifica viene integrata spesso e verificata in automatico con build+test: scopri i problemi in minuti, non a fine mese. CD ha due facce e qui sta il trabocchetto:
- **Continuous Delivery**: il codice che ha passato i test è *sempre pronto* al rilascio, ma l'ultimo passo lo fa un umano che clicca "Approva".
- **Continuous Deployment**: stessa pipeline, ma non c'è nessun bottone umano — il codice che passa i test va in produzione da solo.

La cosa da ricordare è che è **la stessa identica pipeline**: cambia solo se c'è o non c'è un gate umano prima della produzione. Questo dettaglio ti tornerà utile identico nella L06, quando costruirai l'approvazione manuale prima del deploy in produzione.

**Anatomia di una pipeline**: Source (il codice cambia) → Build (compila/impacchetta) → Test (verifica automatica) → Deploy (va in ambiente). Ogni fase si chiama *stage*, l'evento che fa partire tutto è il *trigger*. Regola d'oro: se uno stage fallisce, la pipeline si ferma lì — niente codice rotto arriva più avanti.

**Le 4 metriche DORA**, lo standard di settore per dire quanto un team è bravo a rilasciare:
1. Deployment Frequency — ogni quanto rilasci
2. Lead Time for Changes — da commit a produzione, quanto tempo passa
3. Change Failure Rate — % di rilasci che causano un guasto
4. Time to Restore (MTTR) — quando si rompe, quanto ci metti a rimetterlo in piedi

Il dato controintuitivo, e te lo dico perché è il tipo di cosa che spesso viene chiesta a un colloquio o in verifica: **gli Elite performer rilasciano più spesso *e* si rompono meno**. Non è un paradosso magico: rilasci piccoli e frequenti significano che ogni singolo cambiamento è piccolo, si capisce in fretta e si annulla in fretta se va male. È l'esatto contrario dell'istinto naturale ("rilasciamo di rado così rischiamo meno"), che in realtà produce release enormi, difficili da capire e da annullare.

**La cassetta degli attrezzi AWS (suite Code\*)**: CodeCommit (Source) → CodeBuild (Build/Test) → CodeDeploy (Deploy), orchestrati da CodePipeline, con CodeArtifact come magazzino delle dipendenze e CloudWatch come occhi su tutto. Il punto che nel quiz lampo prende in castagna quasi tutti: **CodePipeline non compila e non testa niente da solo** — è il direttore d'orchestra, non l'orchestrale. È lui che chiama CodeBuild per compilare e CodeDeploy per rilasciare.

### Cosa rifare con le mani
Riprova a memoria il LAB-0: crea un bucket S3 con hosting statico abilitato, scrivi (o riscrivi) `deploy.sh` con un `aws s3 sync . s3://tuobucket --delete`, lancialo, modifica una riga della pagina e rilancialo. Se il tempo lo permette, aggiungi il "test gate" (Extra L1): un controllo con `grep` prima del sync che blocca il deploy se manca qualcosa nel file — è il tuo primo, minuscolo, gate di qualità, e concettualmente è identico ai gate che costruirai in grande nella L06.

### Self-check di fine giornata
- Sapresti spiegare a qualcuno la differenza tra Continuous Delivery e Continuous Deployment senza usare la parola "automatico" due volte a caso?
- Perché gli Elite performer DORA hanno *meno* incidenti pur rilasciando *più* spesso?
- Se ti chiedessero "qual è il servizio che orchestra tutto?" sapresti rispondere subito CodePipeline, e spiegare perché non è lui a compilare?

---

## GIORNO 2 — L02 + L03: Git, teoria e pratica insieme
### Il posto dove il codice ha una memoria

Qui il corso apre il primo stage della pipeline vista ieri: il Source. E lo fa in due tempi — prima la teoria pura (L02, niente computer), poi le mani in pasta su tre piattaforme diverse (L03).

**Perché serve il version control, prima di tutto.**
Il problema che Git risolve è quello — molto umano — dei file `progetto_finale_v2_DEFINITIVO.zip`: copiare cartelle e rinominarle non risponde a domande semplici come "qual è la versione buona?", "chi ha cambiato cosa?", "come torno indietro di tre modifiche?". Git risponde a queste domande in modo automatico e affidabile, tenendo *tutta la storia* del progetto, non solo l'ultimo stato.

**Perché ti serve *soprattutto* in un percorso AWS.**
Questo è il punto che il tuo materiale chiama GitOps, e che riappare identico nella L06: la tua infrastruttura, scritta come CloudFormation o Terraform, è un file di testo. E un file di testo dentro Git ottiene gratis tre cose enormi: storia (chi ha cambiato cosa e quando), revisione (una pull request prima che qualcosa entri), rollback (torni a una versione precedente in un comando). Senza Git, l'infrastruttura come codice perde metà del suo valore.

**Il meccanismo interno**: Git lavora con tre "alberi" — la working directory (dove modifichi i file), la staging area (una sala d'attesa dove scegli *cosa* mettere nel prossimo commit) e il repository vero e proprio (la storia già registrata). Poi ci sono i branch (linee di sviluppo parallele) e il merge (che le riunisce). Quando due modifiche toccano la stessa riga, nasce un conflitto, che va risolto a mano.

**I tre strumenti a confronto — la trappola lessicale.**
GitHub, GitLab e CodeCommit sono tre modi diversi di ospitare *lo stesso* Git. Cambia il vocabolario, non la sostanza:

| Concetto | GitHub | GitLab | CodeCommit |
|---|---|---|---|
| Proporre una modifica | Pull Request | Merge Request | Pull Request |
| Chi lo gestisce | Microsoft | self-host o SaaS | AWS |

Nel quiz di verifica della L02 questa è letteralmente una delle domande: "Merge Request è il termine di quale piattaforma?" → GitLab. Se te lo chiedono in altre forme, il principio è sempre lo stesso: sotto ogni piattaforma batte lo stesso Git.

**Sicurezza — la regola che non si negozia.**
Le credenziali non vanno *mai* nel repository. Un dettaglio che vale la pena fissare bene perché torna in modo drammatico nella L06 (il caso delle credenziali FTP di Marco): **Git non dimentica**. Anche se cancelli un file con un segreto dentro, quel segreto resta nella cronologia per sempre. L'unico rimedio vero non è "rimuovere il file", è "considerare il segreto compromesso e cambiarlo".

### Cosa rifare con le mani
Il modo migliore di fissare questa lezione è ripetere per intero il ciclo `init → branch → commit → push → Pull Request → review → merge`, magari su un repository giocattolo su GitHub. Se ti avanza tempo, prova a creare volontariamente un conflitto (modifica la stessa riga su due branch diversi) e risolvilo: è un esercizio che vale più di dieci minuti di teoria.

### Self-check di fine giornata
- Sai spiegare la differenza tra Git e GitHub in una frase?
- A cosa serve la staging area, e perché non si commit direttamente dalla working directory?
- Perché un segreto committato per errore "resta compromesso" anche dopo averlo cancellato dal file?
- Sapresti motivare, con una frase da manager più che da tecnico, perché l'IaC ha bisogno di Git?

---

## GIORNO 3 — L04: CodeBuild & buildspec
### Il secondo stadio: dal codice grezzo all'artefatto pronto

Ieri hai chiuso il Source. Oggi il corso apre il Build: la macchina temporanea che prende il tuo codice, lo testa, e — solo se tutto va bene — lo impacchetta in qualcosa che si può distribuire.

**Il principio guida della lezione, ed è importante interiorizzarlo perché regge tutta la parte pratica della L06**: *build once, deploy many*. Si costruisce il pacchetto una volta sola, e quello stesso pacchetto (l'artefatto) viene promosso da un ambiente all'altro senza mai essere ricompilato. Se lo ricompili per ogni ambiente, non stai "promuovendo" niente: stai costruendo due cose diverse e sperando che si comportino uguale. È esattamente l'errore che nella L06 la perizia del cliente scopre nel processo di Marco.

**Come funziona CodeBuild in pratica**: definisci un progetto con una sorgente (dove sta il codice), un ambiente (un'immagine container con i tool che ti servono), un service role (i permessi con cui la build può leggere/scrivere risorse AWS) e una destinazione per gli artifact. Il progetto avvia un container pulito, esegue i comandi, produce l'artefatto, e poi *sparisce* — paghi al minuto, non un server sempre acceso.

**Il file `buildspec.yml` e le sue fasi**: è qui che dici a CodeBuild cosa fare, in quattro fasi in sequenza:
- `install` — installa le dipendenze
- `pre_build` — controlli preliminari (per esempio, lint)
- `build` — la build vera, compilazione o generazione
- `post_build` — passi finali, notifiche, pulizia

Più la sezione `artifacts`, che dice quali file del risultato vanno impacchettati e passati allo stage successivo.

**Il punto pedagogico più importante di questa lezione**: "il fix minore, non serve testare" sono, letteralmente, ultime parole famose. Prima di questa lezione il tuo merge passava anche se il progetto era rotto — nessuno lo verificava davvero al momento dell'arrivo. Con CodeBuild nel mezzo, questo cambia: **codice rotto = niente artefatto**, punto. È il primo vero "cancello" (gate) che incontri nel corso, e la parola gate diventerà centrale nella L06.

**Il metodo di debug**, che ti servirà ogni volta che una build si rompe (e si romperà, oggi come in produzione): fatti sempre tre domande, in quest'ordine — in quale fase è morta la build? qual è l'ultimo comando eseguito prima dell'errore? cosa dice *esattamente* il messaggio di errore? Il log ha quasi sempre già la risposta, il problema è che spesso lo si legge di fretta.

Gli errori tipici che vedrai (e che nella L06 ritroverai spesso in versione "checkov"): `AccessDenied` (il service role non ha il permesso giusto), `YAML_FILE_ERROR` (un TAB al posto di uno spazio nell'indentazione — YAML è molto permaloso), `command not found` (un tool che manca nell'immagine), artefatto vuoto (la `base-directory` è sbagliata), `npm ci` che fallisce (manca `package-lock.json`).

### Cosa rifare con le mani
Scrivi da zero, senza copiare, un `buildspec.yml` con le quattro fasi per un progetto Node.js immaginario (install: `npm ci`; pre_build: un linter; build: `npm test` e `npm run build`; artifacts: la cartella `dist/`). Non deve essere perfetto: l'esercizio serve a fissare la struttura nella mano, non solo negli occhi.

### Self-check di fine giornata
- Sapresti spiegare "build once, deploy many" con un esempio concreto di cosa succede se lo violi?
- Elenca a memoria le quattro fasi del buildspec, in ordine.
- Se una build fallisce con `command not found`, qual è la causa più probabile e dove la sistemi?

---

## GIORNO 4 — L05: CI con GitHub Actions
### Colmare l'attesa dell'AWS Academy con uno strumento vero

Questa lezione nasce da un problema molto pratico che probabilmente hai vissuto tu stesso: l'AWS Academy a volte richiede tempo o ha permessi IAM limitati nel Learner Lab. GitHub Actions ti permette di costruire e far girare una pipeline CI *reale*, oggi, gratis sui repository pubblici, senza aspettare nessuno.

**Il vocabolario di un workflow Actions**: evento (`on:`, per esempio `push` o `pull_request`) → job (un gruppo di step che gira su un runner) → step (un singolo comando o azione) → action (un blocco riutilizzabile, tipo `actions/checkout`). Un *runner* è una macchina virtuale effimera che GitHub ti presta per la durata del job, poi la butta via — concettualmente identico al container temporaneo di CodeBuild che hai visto ieri, solo con un altro nome.

**Un `ci.yml` tipico** fa questo, in sequenza: `checkout` (scarica il codice), `setup-node` (prepara l'ambiente), poi `npm ci` (installa dipendenze bloccate dal lockfile — te lo ritroverai identico, parola per parola, nella L06 come rimedio a una delle vulnerabilità della perizia), `npm test`, `npm run build`, e infine `upload-artifact` per conservare il risultato.

**Il cuore pratico della lezione**: rompi un test di proposito e guarda cosa succede alla Pull Request. Questo è il momento in cui la CI smette di essere teoria e diventa qualcosa che *senti*: un check rosso sulla PR che dice, senza ambiguità, "questo codice non entra". È lo stesso identico meccanismo — required status checks + branch protection — che nella L06 diventa il modo con cui blindi `main` una volta per tutte.

**La mappa 1:1 che ti conviene memorizzare bene**, perché è il tipo di traduzione che un esaminatore ama chiedere:

| Concetto | buildspec (L04) | GitHub Actions | CodePipeline |
|---|---|---|---|
| dove gira | container CodeBuild | runner GitHub | orchestratore |
| fasi | install/pre_build/build/post_build | steps | stage |
| output | artifacts | upload-artifact | artifact store S3 |

Il messaggio implicito, e vale la pena tenerlo a mente: il buildspec che hai scritto ieri **si riusa identico** quando la pipeline gira su AWS vero — non stai imparando due mestieri diversi, stai imparando lo stesso mestiere con due nomi diversi per gli stessi pezzi.

### Cosa rifare con le mani
Se hai un account GitHub, crea un repository di prova con un progetto Node minimo, scrivi un `ci.yml` da zero seguendo la sequenza sopra, fallo girare, poi rompi volontariamente un test e osserva il badge diventare rosso sulla Pull Request. Se non hai tempo per il setup completo, almeno riscrivi il file `ci.yml` a mano su un foglio o in un editor, senza guardare l'esempio.

### Self-check di fine giornata
- Elenca a memoria la sequenza evento→job→step→action con un esempio per ciascuno.
- Perché un check rosso su una PR è più forte di "un collega che controlla a occhio"? (Suggerimento: pensa a cosa succede il venerdì sera quando nessuno guarda.)
- Prova a fare a voce la traduzione buildspec↔Actions↔CodePipeline per almeno tre concetti.

---

## GIORNO 5 — Approfondimento: la Pipeline Aumentata (AI nel CI/CD)
### Dove entra l'intelligenza artificiale, e chi resta responsabile

Questo modulo non è un corso "a parte": è, letteralmente, il livello successivo della stessa pipeline che hai costruito nei quattro giorni precedenti. Ogni pezzo che hai scritto a mano — il workflow, la review di una PR, il fix quando la build si rompe — oggi qualcuno prova a farlo fare all'AI. Il filo rosso della lezione, dichiarato esplicitamente, è una domanda sola: **chi tiene il guinzaglio?**

**La scala L0→L3**, che ti conviene avere chiara perché è lo scheletro concettuale di tutta la giornata:
- **L0 — Copilota**: l'AI suggerisce codice mentre scrivi, tu decidi riga per riga.
- **L1 — Revisore**: l'AI commenta una Pull Request, evidenzia problemi, ma non decide.
- **L2 — Medico**: l'AI diagnostica un fallimento di build (per esempio con un job che gira solo `if: failure()`) e propone una fix, ma non la applica da sola.
- **L3 — Agente**: l'AI agisce con più autonomia (apre issue, propone PR), ma — punto fermo del modulo — **merge su main e deploy in produzione restano sempre una decisione umana**.

**I due rischi di sicurezza specifici da conoscere bene**, perché sono il tipo di domanda che compare spesso in un quiz o in un colloquio:
- **Slopsquatting**: un attaccante registra un pacchetto con il nome esatto che un'AI "allucina" quando genera codice (un nome plausibile ma inesistente). Se il tuo processo di build non ha un lockfile bloccato (`npm ci`, non `npm install` — ricordi la L04?), rischi di installare quel pacchetto-fantasma.
- **Prompt injection**: se dai a un agente accesso sia a segreti sia a input non fidati (per esempio il testo di una issue scritta da un utente esterno), quell'input può contenere istruzioni nascoste che spingono l'agente a esfiltrare i segreti. Ecco perché — regola pratica — `echo "${{ secrets.X }}"` in un workflow è pericoloso: stampa il segreto in chiaro nel log.

**Le due basi pratiche della "Parte 2 · Fare"**: come si parla bene a un'AI (un buon prompt di codice dà contesto, compito, vincoli e output atteso — non basta "sistemalo"), e perché vale la pena far scrivere i test all'AI: non per pigrizia, ma perché tende a coprire casi limite a cui tu non avevi pensato. Attenzione però al controesempio dato nel quiz: un test con dentro solo `assert.ok(true)` passa sempre e non verifica assolutamente niente — un test inutile è peggio di nessun test, perché dà una falsa sicurezza.

Un ultimo concetto sottile ma reale: la **review fatigue**. Se un'AI commenta *ogni singola cosa* su ogni PR, le persone smettono di leggere i commenti — l'eccesso di segnalazioni uccide l'attenzione tanto quanto la loro assenza.

### Cosa rifare con le mani
Rifai il quiz di 12 domande della lezione senza guardare prima le soluzioni, cronometrandoti: è un buon modo per capire dove hai ancora dei buchi. Se un paio di risposte ti mettono in difficoltà, torna a rileggere solo quella sezione specifica invece di tutto il modulo.

### Self-check di fine giornata
- Spiega la scala L0→L3 con un esempio concreto per ciascun livello.
- Cos'è lo slopsquatting, e con cosa ti proteggi tu (lo hai già visto in un'altra lezione)?
- Perché "merge su main" non è mai una decisione che si delega, qualunque sia il livello di autonomia dell'agente?

---

## GIORNO 6 — Giornata Lab Guidati + Deep Dive MCP
### Mettere le mani su strumenti più avanzati

Questa giornata unisce due materiali più "esplorativi": la giornata di laboratorio libero (tre track a scelta: Actions avanzati, IaC/container/sicurezza, AI/MCP) e il deep dive su MCP, che è probabilmente il pezzo concettualmente più nuovo di tutto il ripasso.

**Cos'è MCP, in una frase che vale la pena avere pronta**: è uno standard aperto, creato da Anthropic e presentato il 25 novembre 2024, che collega un'AI a dati e strumenti sempre nello stesso modo — la metafora ufficiale è "la USB-C per l'intelligenza artificiale". Prima di MCP, ogni AI parlava con ogni strumento in modo diverso; con MCP scrivi un server una volta e funziona con qualsiasi AI compatibile. Tecnicamente gira su messaggi JSON-RPC 2.0, un'idea presa in prestito dal Language Server Protocol usato dagli editor di codice.

**Perché non è una moda passeggera**: nell'arco di un anno è stato adottato da OpenAI (ChatGPT desktop, marzo 2025), Microsoft (Semantic Kernel/Azure OpenAI, marzo 2025), Google DeepMind (aprile 2025), fino alla donazione alla Linux Foundation nel dicembre 2025. Quando un protocollo tecnico viene adottato da tutti i grandi competitor e poi donato a una fondazione neutrale, è un segnale forte che è diventato infrastruttura, non un esperimento di un'azienda sola.

**Il concetto tecnico da fissare bene: Tool vs Resource.**
- Un **Tool** *ha un effetto*: cambia qualcosa nel mondo (scrive un file, apre una issue, cancella un utente).
- Una **Resource** è in *sola lettura*: espone dati senza modificarli.

Nel quiz finale della lezione questa distinzione viene testata esplicitamente con l'esempio `cancella_utente(id)` — la risposta è Tool, proprio perché ha un effetto irreversibile, e questo ti porta dritto al tema successivo.

**stdio vs HTTP**: stdio è un processo locale, semplice e privato, perfetto per imparare (ed è quello che probabilmente hai usato tu nel lab); HTTP è pensato per scenari remoti o di produzione, dove il server MCP non gira sulla tua macchina.

**Il decoratore `@mcp.tool()` e la docstring**: registrare una funzione Python con `@mcp.tool()` la espone come strumento che l'AI può chiamare. Lo schema degli argomenti (quali parametri accetta, di che tipo) viene generato automaticamente dai type hint della funzione — non lo scrivi tu a mano, MCP lo deduce.

**Sicurezza — lo stesso guinzaglio della lezione precedente, applicato agli strumenti**: privilegio minimo (esponi solo gli strumenti necessari, mai un "tool tuttofare" che fa tutto), approvazione umana per le azioni che contano davvero, e fidati solo di server MCP di terze parti di cui conosci la provenienza — un server gira sul tuo computer con i tuoi permessi, non è un sito web sandboxato.

### Cosa rifare con le mani
Se hai già completato un lab GitHub Skills, riprova a rifarlo a mente passo passo, spiegandoti perché ogni passaggio serve. Se hai il tempo e l'ambiente pronto, scrivi un piccolo server MCP con due strumenti finti (per esempio "conta le parole di un testo" e "tira un dado") e osserva come lo schema degli argomenti viene generato da solo dai type hint — è un esercizio che chiarisce il concetto meglio di qualunque rilettura.

### Self-check di fine giornata
- Spiega MCP a qualcuno che non lo conosce usando solo la metafora della USB-C, poi aggiungi il dettaglio tecnico (JSON-RPC 2.0).
- Tool o Resource per una funzione che legge lo stato di una build senza modificarlo? E per una che riavvia un deploy?
- Perché "privilegio minimo" nel contesto MCP è lo stesso principio IAM che conosci da altre unità formative?

---

## GIORNO 7 — L06: Eredità, Perizia e Pipeline (il capstone)
### Dove tutto il corso confluisce in un caso vero

Questa è la lezione più lunga e più densa, e non a caso: è pensata come una vera commessa professionale, con un cliente (Giulio Genti, presidente della Fondazione ITS ICT Piemonte) che ti telefona, un sistema esistente che nessuno osa toccare, e sei ore per capirlo, giudicarlo, migliorarlo e automatizzarlo. Quasi ogni concetto delle sei lezioni precedenti ricompare qui, applicato con le mani.

**Il principio guida, prima ancora della tecnica: migliorare non vuol dire rifare.**
Quando erediti un sistema che funziona, la tentazione è buttarlo e ricominciare come lo avresti fatto tu. È quasi sempre la risposta sbagliata: mesi in cui il cliente non vede niente, si riscoprono a una a una le ragioni (magari buone) delle scelte strane fatte da chi c'era prima, si perdono i casi limite già risolti, e tutto il rischio si concentra nel giorno del passaggio. La domanda giusta non è "come lo avrei fatto io" ma "qual è il prossimo cambiamento più piccolo che riduce di più il rischio?".

**Le cinque lenti della perizia** — sono, letteralmente, il Well-Architected Framework che hai visto in Architettura (UF1), tradotto in italiano e applicato a un sistema vero:
- **Affidabilità**: cosa succede quando qualcosa si rompe, e come si torna indietro?
- **Sicurezza**: chi può fare cosa, e chi non dovrebbe poterlo fare?
- **Costi**: quanto costa, e si riesce a dire a chi attribuirlo?
- **Operabilità**: chi lo manda in produzione, come, e cosa succede se quella persona è in ferie?
- **Evolvibilità**: quanto costa cambiare qualcosa domani?

**Come si scrive una constatazione che serve davvero**, ed è una formula da avere pronta parola per parola: **fatto → conseguenza → rimedio**. "Il bucket è configurato male" è un'opinione inutile; "la bucket policy consente `s3:*` a `Principal: "*"`" è un fatto verificabile; "chiunque su internet può modificare o cancellare le pagine del portale" è la conseguenza in linguaggio da cliente; "rimuovere la policy pubblica, riattivare il blocco degli accessi pubblici, pubblicare solo dalla pipeline" è il rimedio, un'azione concreta non un desiderio vago.

**Gravità (tre livelli, non cinque) incrociata con lo sforzo**: BLOCCANTE (rischio di perdere dati, soldi o reputazione — si sistema adesso), SERIO (non brucia ma prima o poi fa male — va in piano con una data), DA SISTEMARE (scomodo ma non pericoloso). Il quadrante che distingue un professionista da un principiante è quello "gravità bassa + sforzo alto": lì la scelta giusta è spesso *non fare nulla*, e scriverlo per iscritto, con il perché.

**Il vocabolario di pipeline che ormai conosci, ma qui si mette tutto insieme**: stadio (blocco del nastro, in GitHub Actions è un job), azione (il singolo comando, in Actions uno step — lo stesso di ieri), artefatto (il pacchetto che passa da uno stadio al successivo, esattamente il "build once, deploy many" della L04), transizione (il permesso di passare avanti, automatico se i controlli sono verdi o bloccato in attesa di un umano — la differenza Delivery/Deployment della L01, applicata concretamente).

**Gate vs audit, un distinguo che spesso in verifica viene chiesto in modo insidioso**: un audit ti dice come stai ma non blocca niente (è un consiglio, e i consigli si ignorano); un gate ha i denti — se è rosso, non si passa. Nella pipeline della L06 troverai *entrambi* per lo stesso strumento (checkov): un audit informativo con `--soft-fail` e un gate vero con la lista di regole del capitolato.

**I cinque gate concreti che monta la lezione**: struttura (il codice IaC c'è ancora?), applicazione (`npm ci`/`npm test`/`npm run build`, gli stessi comandi della L04-L05), segreti (niente password o chiavi nel repo — la stessa regola d'oro della L02, qui diventata uno script grep + checkov), sintassi IaC (`cfn-lint`/`terraform validate`), policy IaC (checkov con una regola scritta apposta per il capitolato del cliente, `CKV_ITS_1` sul tag Owner).

**Shift-left**: più tardi trovi un problema, più costa sistemarlo (sul tuo portatile: 1× · in una pull request: 5× · in collaudo: 20× · in produzione: 100×+). Da qui la scelta pratica: i gate girano sulla pull request, non dopo il merge.

**Branch protection non è il tuo buon senso, è una regola del repository**: puoi avere la CI più bella del mondo, ma se si può ancora fare push diretto su `main` non hai un gate, hai un suggerimento. Questo collega direttamente al checkpoint pratico che hai già visto nella L05 (il check rosso sulla PR) — qui diventa una configurazione vera: Settings → Branches → Require status checks to pass.

**L'approvazione umana**, con lo stesso spirito della distinzione Delivery/Deployment della L01: il nastro si ferma, aspetta una persona, e chi approva è registrato (nome e ora) nella cronologia — è la parte che piace agli auditor. Attenzione al rischio esplicito segnalato dal materiale: se chi approva non sa cosa sta approvando, hai solo aggiunto attesa, non sicurezza — l'approvazione diventa un timbro vuoto.

**Rollback: due strade, non una, e l'ordine conta.**
- **Ripubblicare l'artefatto precedente** — veloce (minuti), la mossa giusta mentre l'incidente è in corso ("fermi il sangue"). Limite: il codice sbagliato resta ancora in `main`, quindi se qualcuno rilascia di nuovo, il problema torna.
- **Annullare il commit** (`git revert`) — più lento, passa da tutti i gate, ma "cura la ferita": la storia di `main` torna sana e il problema non può ripresentarsi da solo.

In un incidente vero **si fanno entrambe, in questo ordine**: prima ripubblichi, poi reverti.

**Le quattro domande DORA**, di nuovo — ma questa volta non in teoria: le misuri davvero sul tuo portale, con numeri veri, alla fine della giornata di laboratorio.

**Il caso della "pipeline bugiarda"** — vale la pena ricordarlo perché è un esempio molto concreto di un principio importante: una pipeline verde su tutta la linea può comunque produrre un sito rotto, se nessun gate verifica *l'artefatto pubblicato* invece che solo il codice sorgente. `npm test` dice che le funzioni si comportano bene, non che il sito generato contenga davvero i corsi. Da qui nasce lo **smoke test**: non prova tutto, prova solo che "il fumo non esca" — il minimo sindacale dopo ogni deploy.

**Le richieste del cliente (CR-1, CR-2, CR-3)** sono un piccolo mondo a sé che vale la pena ripassare separatamente, perché mostrano tre situazioni diverse: CR-1 è la richiesta banale che dimostra il valore di tutto il lavoro fatto (da "venerdì, se c'è Marco" a "dieci minuti, chiunque"); CR-2 è una decisione di architettura che nessun controllo automatico può prendere al posto tuo; CR-3 è un no professionale, che si scrive sempre con tre parti — rischio, costo, alternativa — mai un no secco.

### Cosa rifare, come esercizio finale di tutta la settimana
Prova a fare a voce, come se stessi davvero presentando la demo finale di tre minuti descritta nel materiale: elenca tre constatazioni tipo (una gravissima, una sottile, una che decidi consapevolmente di rimandare, con il perché), poi i cinque gate della pipeline nell'ordine in cui girano, poi le due strade di rollback e quando useresti l'una o l'altra, infine le quattro metriche DORA applicate a questo caso specifico.

### Self-check di fine giornata (e di fine settimana)
- Recita a memoria la formula fatto→conseguenza→rimedio con un esempio a tua scelta.
- Spiega la differenza tra un audit e un gate con l'esempio di checkov usato in due modalità diverse nello stesso progetto.
- Perché si ripubblica *prima* di revertire, e non il contrario?
- Rileggi la tabella "Prima e dopo" del materiale (pag. 127) e la tabella di traduzione GitHub Actions↔AWS (pag. 128): sono il punto in cui tutte e nove le lezioni della settimana si ricongiungono in un'unica immagine.

---

## Una nota finale sul metodo

Nei giorni 2, 4 e 6 la parte "tastiera" pesa quanto quella "rilettura": sono le lezioni pratiche, e su quelle il rischio concreto è illudersi di sapere qualcosa solo perché la formula suona familiare quando la rileggi. Se un giorno hai poco tempo, taglia la rilettura ma non l'esercizio pratico — è quello che fissa davvero.

Se vuoi, per uno di questi sette giorni posso prepararti anche un quiz interattivo o delle flashcard da usare come verifica finale — dimmi solo su quale giornata vuoi concentrarti per primo.
