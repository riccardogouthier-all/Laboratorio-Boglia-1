# Officina Terraform — i lab ufficiali HashiCorp

Come per CloudFormation avevamo **cfn101**, per Terraform c'è la palestra ufficiale HashiCorp: gratuita, sempre aggiornata, ed è **la stessa che si usa per preparare la certificazione Terraform Associate**.

👉 **<https://developer.hashicorp.com/terraform/tutorials>**

---

## Prima di partire — leggete queste 4 righe

| | |
|---|---|
| 🟢 **"Interactive"** | Terminale **dentro il browser**: niente installazioni e **non consuma i crediti del Learner Lab**. Può chiedervi un account HashiCorp gratuito. |
| ⚪ **Gli altri** | Girano con la **vostra CLI** + il Learner Lab. |
| 🔴 **Da saltare** | Tutto ciò che parla di **HCP Terraform** / Terraform Cloud (`cloud-migrate`, `cloud-state-api`): serve un altro account e **non è il nostro backend** — noi usiamo S3. |

### ⚠️ Le due trappole (ve le risparmio io)

1. **REGION.** Diversi tutorial partono in `us-east-2`, che nel **Learner Lab non è consentita**. Prima di lanciare l'apply, aprite il `terraform.tfvars` (o il `main.tf`) e mettete `region = "us-east-1"` (oppure `us-west-2`). Se un tutorial vi dice *"confirm your AWS CLI region"*, la vostra è **us-east-1**.
2. **Il tutorial "Import Terraform configuration" gira su DOCKER, non su AWS.** Serve Docker installato sul portatile. Se non ce l'avete, saltatelo: l'import su AWS lo abbiamo già fatto in aula (LAB A step 3).

E poi le solite: credenziali del Learner Lab che scadono (`ExpiredToken` → ricopiatele) e **`terraform destroy` alla fine di ogni tutorial**.

---

## COMPITO — questi quattro (~65 minuti)

Coprono esattamente quello che abbiamo fatto in aula.

| # | Tutorial | Durata | Perché |
|---|---|---|---|
| 1 | **[Manage resource drift](https://developer.hashicorp.com/terraform/tutorials/state/resource-drift)** | 12' | Create un'EC2, la modificate a mano con la AWS CLI, e riconciliate. **È il LAB A step 2** — con in più `-refresh-only` e l'import di un security group. ⚠️ **cambiate la region in `us-east-1`** |
| 2 | **[Manage resources in Terraform state](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)** | 24' | `state list`, `state show`, `state mv`, `state rm`: la chirurgia sullo state, fatta bene. ⚠️ **region** |
| 3 | 🟢 **[Build and use a local module](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)** | 15' | Scrivete un modulo che crea un bucket S3 per un sito statico. **È il LAB D.** Interattivo: gira nel browser |
| 4 | **[Use configuration to move resources](https://developer.hashicorp.com/terraform/tutorials/modules/move-config)** | 14' | Il blocco `moved` per spostare risorse dentro i moduli **senza distruggerle**. **È la soluzione del LAB D** |

---

## Se volete andare oltre

**Moduli** — <https://developer.hashicorp.com/terraform/tutorials/modules>

- 🟢 **[Use registry modules in configuration](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)** (12') — il modulo VPC ufficiale: una VPC completa in ~15 righe. Interattivo
- 🟢 **[Refactor monolithic configuration](https://developer.hashicorp.com/terraform/tutorials/modules/organize-configuration)** (18') — spezzare un progetto monolitico in moduli e directory
- **[Module creation — recommended pattern](https://developer.hashicorp.com/terraform/tutorials/modules/pattern-module-creation)** (17') — come si progetta un modulo che gli altri useranno davvero

**State** — <https://developer.hashicorp.com/terraform/tutorials/state>

- **[Use refresh-only mode](https://developer.hashicorp.com/terraform/tutorials/state/refresh)** (10') — la drift detection "pura", senza correzioni
- **[Manage resource lifecycle](https://developer.hashicorp.com/terraform/tutorials/state/resource-lifecycle)** (8') — `prevent_destroy`, `create_before_destroy`, `ignore_changes`: è il **DeletionPolicy** di CloudFormation
- **[Develop configuration with the console](https://developer.hashicorp.com/terraform/tutorials/state/console)** (13') — `terraform console`: provare le espressioni prima di scriverle
- **[Troubleshoot Terraform](https://developer.hashicorp.com/terraform/tutorials/state/troubleshooting-workflow)** (17') — leggere gli errori e fare debug con `TF_LOG`
- **[Target resources](https://developer.hashicorp.com/terraform/tutorials/state/resource-targeting)** (20') — `-target`: il bisturi, da usare con giudizio

**Recupero della L07** — <https://developer.hashicorp.com/terraform/tutorials/aws-get-started>
Se lunedì eravate assenti o non è filato liscio: è il percorso "Get Started with AWS" completo (install → build → change → destroy → variables → outputs).

**Certificazione** — sullo stesso sito c'è la collection **Certification Prep** per la *Terraform Associate*.

---

## Regole della casa

1. **`terraform destroy` a fine di ogni tutorial.** I crediti del Learner Lab sono vostri.
2. **Region `us-east-1` o `us-west-2`.** Sempre. Se il tutorial dice altro, cambiatelo.
3. **Niente HCP Terraform**: se vi chiede di fare login su `app.terraform.io`, avete sbagliato tutorial (o dovete scegliere la tab *"Terraform Community Edition"*).
4. Se un tutorial vuole creare **ruoli IAM**: nel Learner Lab non si può → usate `LabRole`, oppure fatelo nella versione 🟢 Interactive.
5. Quando un comando non torna: **leggete l'ultima riga dell'errore**, non la prima.
