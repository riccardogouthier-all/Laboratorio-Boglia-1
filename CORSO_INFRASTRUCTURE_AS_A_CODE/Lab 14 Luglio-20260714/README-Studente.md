# L08 — Lo state e il lavoro in squadra

**Mattinata**: 2 ore di teoria, poi 2 ore di laboratorio (5 tappe).
Questo file è la guida del **laboratorio**: il codice di ogni tappa è già scritto e commentato. Voi dovete **capirlo**, adattarlo (i nomi!) e lanciarlo.

> 🚫 **Niente `terraform destroy` fino alla fine della giornata.** La stessa infrastruttura serve per tutte e 5 le tappe.

---

## Prima di iniziare

1. **Credenziali** del Learner Lab in `~/.aws/credentials` (**AWS Details → AWS CLI → Show**)
   → quando vedete `ExpiredToken`, ricopiatele. Succederà, a tutti, ed è normale.
2. **Terraform ≥ 1.11**: `terraform -version` (serve per il lock nativo su S3)
3. Region: **`us-east-1`** (o `us-west-2`). Mai altre.

---

## TAPPA 1 — Guardare dentro lo state (15')

Cartella `lab-state/`, dentro il `main.tf` di **`01-state/`** (col **vostro** nome di bucket: dev'essere unico su tutto AWS).

```bash
terraform init
terraform apply                            # yes
terraform state list                       # l'elenco: cosa c'è nell'inventario
terraform state show aws_s3_bucket.dati    # la scheda di UNA risorsa
```

Poi aprite **`terraform.tfstate`** in VS Code e trovate:

- `"serial"` → il contatore delle modifiche
- `"lineage"` → la carta d'identità dello state
- `"name": "dati"` e `"id": "its-iac-..."` → **il legame fra il nome nel codice e l'ID vero su AWS**. È l'unico posto al mondo dove quel legame esiste.

---

## TAPPA 2 — Il drift: rompete e guardate (20')

1. **Console AWS** → S3 → il vostro bucket → **Properties → Tags**: cambiate `Corso` in `pippo` e **aggiungete** un tag nuovo (es. `urgente = si`)
2. `terraform plan` → **leggete bene cosa propone**
3. `terraform plan -refresh-only` → cosa cambia rispetto a prima?
4. `terraform apply` → tornate in console e guardate i tag: **chi ha vinto?**

<details><summary>Cosa dovevate vedere (apritelo dopo aver provato)</summary>

```
~ tags = {
    ~ "Corso"   = "pippo" -> "ACA"     # rimette il valore del CODICE
    - "urgente" = "si" -> null          # CANCELLA il tag aggiunto a mano
  }
```

- **`plan`** = "ecco cosa **farò** per rimettere tutto come dice il codice"
- **`plan -refresh-only`** = "ecco cosa **è cambiato** là fuori" — e basta, non propone di correggerlo

**Il codice è la verità.** Chi "sistema al volo in console" vede il proprio lavoro evaporare al prossimo apply: ecco perché in azienda la console si usa in sola lettura.
</details>

---

## TAPPA 3 — Lo state su S3 e il lock (35')

### Parte 1 — il bucket dello state (bootstrap)

Cartella **nuova e separata** `00-state-bucket/` (codice in **`03-backend/00-state-bucket/`**): crea il bucket che ospiterà lo state, con **versioning**, cifratura e blocco degli accessi pubblici.

```bash
terraform init && terraform apply     # segnatevi il nome esatto del bucket
```

> **L'uovo e la gallina**: questo progetto tiene il **suo** state in locale — non può mettere lo state dentro il bucket che sta creando. È normale, non è un baco. In azienda si fa esattamente così.
> Il **versioning** è il paracadute: se lo state si corrompe, tornate alla versione di ieri.

### Parte 2 — migrare lo state

Tornate in `lab-state/` e aggiungete il file `backend.tf` (da **`03-backend/`**), scrivendoci **il vostro** bucket di state:

```bash
terraform init -migrate-state
# "Do you want to copy existing state to the new backend?"  -->  yes
```

> ⚠️ Se rispondete **no**, il backend parte **vuoto** e Terraform si dimentica di tutto. **Rispondete yes.**

Verificate:

```bash
ls -la                 # il terraform.tfstate locale è vuoto
terraform state list   # funziona ancora: ora lo legge da S3
terraform plan         # No changes
```

In console S3, dentro il bucket di state, c'è l'oggetto `lab/terraform.tfstate`. **È lì che vive adesso.** Un collega che clona il repo e fa `init` vede le stesse identiche risorse.

### Parte 3 — il lock (due terminali)

| | |
|---|---|
| **Terminale 1** | `terraform apply` → fermatevi al prompt `Enter a value:` e **NON rispondete** |
| **Terminale 2** | (stessa cartella, basta una seconda tab) `terraform plan` |

<details><summary>Cosa dovevate vedere</summary>

```
Error: Error acquiring the state lock
  Operation: OperationTypeApply
  Who:       mario@portatile
```

Il lucchetto ce l'ha il terminale 1: **lo prende all'inizio dell'apply** e lo tiene finché non finisce — anche mentre aspetta il vostro `yes`. In azienda quel **Who** è il collega da andare a cercare.

`terraform force-unlock <ID>` esiste, ma si usa **solo** se l'altra operazione è morta davvero (crash, terminale chiuso). Strapparlo a un apply vivo corrompe lo state.
</details>

Poi rispondete `yes` (o `Ctrl+C`) nel terminale 1 e rilanciate il plan nel 2: riparte.

---

## TAPPA 4 — Variabili e locals (20')

Copiate `variables.tf` e `terraform.tfvars` da **`04-variabili/`** nella cartella del lab. Poi nel `main.tf`:

- il nome hardcoded → `var.bucket_name`
- i tag scritti a mano → `local.common_tags`

```bash
terraform plan                              # deve uscire pulito (o cambiare solo i tag)
terraform plan -var="environment=collaudo"  # prova cattiva: cosa succede?
```

<details><summary>Cosa dovevate vedere</summary>

La **validation** vi ferma con **il messaggio che avete scritto voi**, al `plan`, **prima** che Terraform tocchi qualsiasi cosa su AWS.

E se il plan propone di **distruggere e ricreare** il bucket, avete cambiato il **nome**: su AWS il nome di un bucket non è modificabile a caldo. Rimettetelo identico nel `tfvars`.

Se invece il plan è **pulito**: avete cambiato il **codice** senza cambiare la **realtà**. Si chiama **refactoring**, e il `plan` è il vostro test di regressione.
</details>

**Bonus** (in fondo al `main.tf` dei materiali, commentato): il `for_each`, cioè **una risorsa scritta una volta e creata N volte**. In CloudFormation non si poteva fare.

---

## TAPPA 5 — Il primo modulo (25')

Copiate la cartella `modules/bucket/` da **`05-moduli/`** dentro il vostro lab e **leggetela**: sono 3 file, 15 righe in tutto (`variables.tf` = gli input, `main.tf` = la resource, `outputs.tf` = cosa restituisce).

Nel `main.tf` del root: togliete la vecchia `resource` e mettete **due** blocchi `module` — `bucket_dati` (quello di sempre) e `bucket_log` (nuovo).

```bash
terraform init      # OBBLIGATORIO dopo aver aggiunto un module
terraform plan
```

**Il plan vuole DISTRUGGERE il vostro bucket. Non fate apply.** Perché?

<details><summary>La spiegazione, e la cura</summary>

Perché è cambiato l'**indirizzo**, non la risorsa:

```
PRIMA:  aws_s3_bucket.dati
DOPO:   module.bucket_dati.aws_s3_bucket.this
```

Per lo state sono **due risorse diverse** → destroy + create.

La cura è il blocco `moved` (lo trovate già scritto in fondo al `main.tf` dei materiali):

```hcl
moved {
  from = aws_s3_bucket.dati
  to   = module.bucket_dati.aws_s3_bucket.this
}
```

Rifate il plan: **0 to destroy**. Il bucket non viene toccato — cambia solo la sua etichetta nell'inventario.

*In azienda, questo blocco è ciò che separa un refactoring pulito da un database di produzione distrutto alle 3 di notte.*
</details>

---

## Finito prima? → Officina

I lab ufficiali HashiCorp: vedi **`Guida-Officina-Terraform.md`**.
Se ieri eravate assenti (o non è filato liscio), partite dal percorso **Get Started — AWS**: 6 tutorial, quasi tutti interattivi **nel browser**, ~40 minuti.

---

## PRIMA DI ANDARE VIA — l'ordine conta

```bash
# 1. PRIMA il progetto del lab
terraform destroy

# 2. POI il bucket dello state
cd 00-state-bucket && terraform destroy
```

Se lo fate al contrario, **cancellate lo state** e vi restano **risorse orfane** su AWS che continuano a costare. Il bucket di state, avendo il versioning, va prima svuotato ("Empty" da console).

---

## Pronto soccorso

| Errore | Cosa fate |
|---|---|
| `ExpiredToken` / `InvalidClientTokenId` | credenziali scadute → ricopiatele da AWS Details |
| `BucketAlreadyExists` | il nome del bucket è globale su tutto AWS → cambiatelo |
| `Error: Module not installed` | avete aggiunto un `module` e non avete rifatto `terraform init` |
| `Error acquiring the state lock` | alla Tappa 3 è quello che **volete** vedere. Altrove: un terminale è morto tenendo il lock → `terraform force-unlock <ID>` |
| `BucketNotEmpty` (sul destroy) | svuotate il bucket da console, oppure `force_destroy = true` |
| **Il plan vuole distruggere qualcosa che non ho toccato** | **fermatevi e chiamate il docente.** Alla Tappa 5 è normale (è l'esercizio). Altrove, no. |

> Terraform scrive errori lunghi ma leggibili: leggete **l'ultima riga** del blocco `Error`, non la prima.
