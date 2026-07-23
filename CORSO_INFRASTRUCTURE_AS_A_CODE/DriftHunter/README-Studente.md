# LAB L12 — DriftHunter: leggi il piano, dai la caccia al drift

**Obiettivo:** padroneggiare le due cose che rendono una pipeline **d'infrastruttura** diversa da una pipeline **d'applicazione** (quella già vista in Automation):

1. **leggere il `terraform plan`** e riconoscere cosa è sicuro e cosa è una bomba;
2. **il drift** — quando il cloud si allontana dal codice — trovarlo e ricomporlo.

Motore: **Terraform CLI sul tuo portatile** (come L07/L08) + qualche click nella console AWS. Niente pipeline da montare: qui si lavora sullo *stato* dell'infrastruttura.

> ⏱️ **2 ore piene.** Ambiente: il **tuo** Learner Lab (us-east-1) + Terraform CLI locale. State **locale** (lab individuale). A fine lab: **`terraform destroy`**.

---

## 🧰 Preflight (10 min)
```bash
terraform version              # >= 1.5
aws sts get-caller-identity    # le STS del Learner Lab in ~/.aws/credentials (come L07/L08)
cd terraform
terraform init                 # scarica il provider aws (state LOCALE, nessun backend)
```
> STS scadute più tardi? (`ExpiredToken`) → rigenera `~/.aws/credentials` da *AWS Details → AWS CLI: Show*.

---

## PART 1 · Deploy + esplora lo stato (15 min)
```bash
terraform plan     # 5 risorse: 1 SG "web" + 1 bucket + 3 blocchi di hardening
terraform apply    # 'yes'  ->  "Apply complete! Resources: 5 added"
```
Ora **guarda dentro lo stato** — è la "memoria" di Terraform:
```bash
terraform state list                       # l'elenco di cosa Terraform gestisce
terraform state show aws_security_group.web # gli attributi reali (id sg-..., vpc_id...)
```
Codice e cloud sono **allineati**. Da qui in poi li facciamo divergere — di proposito.

---

## PART 2 · Leggi il piano (30 min) — il simbolo conta
Fai **una modifica alla volta** al `main.tf`, lancia `terraform plan`, **leggi il simbolo**, classifica. NON applicare le pericolose; **rimetti com'era** prima di passare alla successiva.

I quattro simboli (da L07): `+` crea · `~` modifica sul posto · `-` distrugge · `-/+` **sostituisce** (distrugge e ricrea).

| # | Modifica | Simbolo (verificato) | Verdetto |
|---|----------|----------------------|----------|
| 1 | Aggiungi `CostCenter = "campus"` in `common_tags` | `~ update in-place` · *0 to add, 2 to change* | ✅ sicuro |
| 2 | Cambia il **nome** del bucket | `-/+ ... forces replacement` · *4 to add, 4 to destroy* | 💣 **perdita dati (a cascata!)** |
| 3 | Cambia la **description** del SG | `-/+ ... forces replacement` · *1 to add, 1 to destroy* | ⚠️ campo immutabile |
| 4 | Rinomina la risorsa `...web` → `...frontend` | `-` + `+` (destroy+create) | ⚠️ è solo un **rename** |

**#2 è la trappola:** il nome del bucket è *immutabile* → Terraform lo **distrugge e ricrea**, e siccome i 3 blocchi di hardening puntano al bucket, si portano dietro pure loro (**4 risorse** distrutte). Su dati veri = disastro. Si legge nel `plan` **prima**.

**#4 — il rename:** il `plan` propone destroy+create, ma tu volevi solo cambiare nome nel codice. La cura (da L08) — dì a Terraform "è la stessa risorsa":
```hcl
moved {
  from = aws_security_group.web
  to   = aws_security_group.frontend
}
```
Con `moved{}` il plan torna a **`0 to add, 0 to change, 0 to destroy`**. Poi rimetti tutto com'era.

---

## PART 3 · Drift Hunter (30 min) — il codice è la verità
**L'hotfix delle 2 di notte.** Qualcuno apre una porta a mano in console.

1. **Crea il drift (console):** EC2 → *Security Groups* → `drifthunter-web` → *Edit inbound rules* → aggiungi **RDP 3389** da `0.0.0.0/0` → Save.
2. **Smaschera:**
   ```bash
   terraform plan     # (fa il refresh dal cloud da solo)
   ```
   Terraform vuole **rimuovere** la 3389: non è nel codice → per lui non esiste. Vedrai `~ ingress ... - from_port = 3389` e `Plan: 0 to add, 1 to change, 0 to destroy`. **Il codice è la verità.**
3. **La decisione — riconcilia o adotta?**
   - **Riconcilia (il codice vince, default):**
     ```bash
     terraform apply   # -> "Modifications complete": la 3389 sparisce
     ```
   - **Adotta (la regola serviva davvero):** aggiungila al `main.tf`, poi:
     ```bash
     terraform plan            # niente più drift...
     checkov -d . --config-file .checkov.yaml   # ...ma CKV_AWS_25 FAIL: RDP aperto al mondo!
     ```
     Adottare un drift *cattivo* nel codice lo rende **visibile al gate**: da porta dimenticata a decisione esplicita.

> Vuoi solo vedere le differenze col reale, senza proporre modifiche? `terraform plan -refresh-only`.

---

## PART 4 · Il guardiano — automatizza la caccia (15 min)
Il drift l'hai trovato **a mano**. Falla trovare a uno **script**. Nel pacchetto c'è `drift-check.sh`:
```bash
./drift-check.sh
# ✅ Nessun drift: codice e cloud sono allineati.        (exit 0)
```
Ricrea il drift (riapri la 3389 in console) e rilancialo:
```bash
./drift-check.sh
# ⚠️  DRIFT RILEVATO — qualcuno ha toccato l'infrastruttura a mano: ...   (exit 2)
```
Dentro fa un `terraform plan -detailed-exitcode` (exit **0**=ok · **2**=drift · **1**=errore). È il cuore del "guardiano": in produzione lo fai girare **schedulato** (vedi `drift-check.yml`, la versione GitHub Actions, nella challenge).

---

## PART 5 · Adottare senza distruggere: import (15 min)
Un collega ha creato **da zero in console** un bucket con dati. Vuoi gestirlo con Terraform. Non lo riscrivi e applichi (lo ricreerebbe / conflitto): lo **importi**.
```bash
# nel main.tf aggiungi il blocco vuoto della risorsa:
#   resource "aws_s3_bucket" "legacy" { bucket = "nome-esistente" }
terraform import aws_s3_bucket.legacy nome-esistente   # -> "Import successful!"
terraform state list        # ora compare aws_s3_bucket.legacy
terraform plan              # ti dice cosa allineare, SENZA -/+
```
`import` (o il blocco `import {}` dichiarativo di L08) porta l'esistente sotto controllo senza distruggerlo. È la mossa da senior.

---

## 🧹 Cleanup + autovalutazione (5 min)
```bash
terraform destroy    # 'yes' — non lasciare risorse accese sul lab
```
**Sei a posto se…**
- leggi un piano e distingui `~` (sicuro) da `-/+` (sostituzione = possibile perdita dati);
- hai creato un drift in console e l'hai **smascherato** con `terraform plan` e con `drift-check.sh`;
- sai spiegare **riconcilia vs adotta** e perché il codice è la fonte di verità;
- sai perché si usa `import` e non "riscrivo e applico".

## 🆘 Troubleshooting
- **`ExpiredToken`/`InvalidClientTokenId`** → STS del lab scadute: rigenera `~/.aws/credentials`.
- **il plan non vede il drift** → salvato in console? stessa region `us-east-1`? (il plan fa il refresh).
- **vuole distruggere per un rename** → campo immutabile o cambio d'indirizzo → `moved{}`.
- **`no default VPC`** → nel Learner Lab c'è; se manca, avvisa il docente.

## 🏆 CHALLENGE (compito) — il guardiano schedulato
`drift-check.sh` lo lanci tu. Il file `drift-check.yml` lo fa girare **ogni notte** in GitHub Actions e **apre una issue** se trova drift (exit 2). Gira in cloud → serve **state remoto** (S3, L08) + i 3 secret STS. Montalo, sposta `drift-check.yml` in `.github/workflows/`, e lancialo a mano (*Run workflow*) per provarlo.
