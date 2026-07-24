# LAB L13 — Governance & FinOps: metti in ordine, e sotto controllo la spesa

Fin qui hai imparato a **costruire** e **operare** l'infrastruttura. Oggi le due cose che servono quando il parco cresce:

1. **Governance** — imporre uno **standard** e tenere l'ordine (moduli + policy + documentazione);
2. **FinOps** — vedere e controllare i **costi** con l'IaC, *prima* di spendere.

Motore: **Terraform CLI** + `terraform-docs`, `checkov`, `infracost`. Learner Lab (us-east-1). State locale.

> ⏱️ **2 ore.** A fine lab: `terraform destroy` (le uniche risorse reali sono i bucket).

---

## 🧰 Preflight (10 min)


```bash
 winget install --id Terraform-docs.Terraform-docs --exact --scope user    # per terraform-docs
 winget install --id Infracost.Infracost --exact --scope user              # per infracost
 python -m pip install chechov                                             # per checkov
```

```bash
terraform version
terraform-docs --version     # per la documentazione
checkov --version            # per la policy di governance
infracost --version          # per i costi
# infracost usa un'API di prezzi gratuita: una tantum
infracost auth login         # (apre il browser, chiave gratuita)
aws sts get-caller-identity  # STS del Learner Lab
cd terraform && terraform init
```

---

## PART 1 · Standardizza con un MODULO (25 min)
Chi vuole un bucket **non** riscrive cifratura, blocco-accessi e tag ogni volta: usa il **modulo standard** `secure-bucket`, che ce li mette d'ufficio. Nel `main.tf` lo istanziamo per **due ambienti**:
```hcl
module "logs_dev"  { source = "./modules/secure-bucket"
  name = "acme-logs"  env = "dev"   owner = "team-piattaforma"  cost_center = "CC-1001" }
module "logs_prod" { source = "./modules/secure-bucket"
  name = "acme-logs"  env = "prod"  owner = "team-piattaforma"  cost_center = "CC-1001" }
```
```bash
terraform apply    # -> "Apply complete! Resources: 8 added" (4 risorse × 2 ambienti)
terraform state list
```
Guarda il modulo (`modules/secure-bucket/`): input (`variables.tf`) → risorse (`main.tf`) → output (`outputs.tf`). **Un mattoncino approvato, riusabile.** È questo il senso di "standardizzazione dei modelli infrastrutturali".

### PART 1b · Il modulo rifiuta l'input sbagliato (governance sull'input)
Il modulo non accetta qualsiasi cosa: le `variable` hanno delle **validation**. Prova a istanziarlo con `env = "staging"` (invece di dev/prod) e lancia `terraform validate`:
```
Error: Invalid value for variable
env deve essere 'dev' o 'prod'.
```
Prova con `cost_center = "NOPE"`:
```
Error: Invalid value for variable
cost_center deve avere il formato CC-<numero> (es. CC-1001).
```
Il modulo è una **prima guardia**: chi lo usa non può passargli valori fuori standard. Rimetti i valori giusti.

---

## PART 2 · Documenta da solo (15 min)
La documentazione di un modulo si **genera dal codice**, non si scrive a mano:
```bash
terraform-docs markdown table modules/secure-bucket > modules/secure-bucket/README.md
```
Apri il `README.md`: tabella di **Inputs** (name/env/owner/cost_center), **Outputs**, risorse. Cambi una variabile → rigeneri → il README è sempre aggiornato. Zero documentazione "vecchia".

---

## PART 3 · Imponi lo standard con una policy (25 min)
Il modulo mette i tag; ma come impedisci a un collega di creare un bucket **fuori** dal modulo, senza tag? Con una **policy-as-code** (governance-as-code, richiama L10). Nel pacchetto: `policies/require_tags.yaml` — "ogni bucket deve avere `Owner` e `CostCenter`".
```bash
checkov -d . --external-checks-dir ../policies --check CKV_ACME_TAGS   # i bucket del modulo PASSANO
```
Ora fai il "ribelle": crea un file `rogue.tf` con un bucket **senza tag**, e ri-lancia:
```hcl
resource "aws_s3_bucket" "rogue" { bucket = "acme-rogue-a-mano" }
```
```bash
checkov -d . --external-checks-dir ../policies --check CKV_ACME_TAGS
# -> CKV_ACME_TAGS  FAILED for resource: aws_s3_bucket.rogue
```
Il gate lo **becca**. In pipeline (L12) questa policy blocca il merge. Poi cancella `rogue.tf`.

### PART 3b · Una policy sui COSTI (governance ∩ FinOps)
La governance non è solo sicurezza: puoi imporre anche **limiti di spesa**. Nel pacchetto: `policies/allowed_instance_types.yaml` — "un'istanza EC2 può usare solo `t3.micro`/`t3.small`".
```bash
checkov -d . --external-checks-dir ../policies --check CKV_ACME_INSTANCE_SIZE   # t3.micro -> PASS
```
Cambia il default di `instance_type` in `t3.large` e ri-lancia:
```
CKV_ACME_INSTANCE_SIZE  FAILED for resource: aws_instance.app
```
Questa è una regola che **impedisce a qualcuno di accendere una macchina enorme "per provare"**: la policy protegge il portafoglio, non solo la sicurezza. Rimetti `t3.micro`.

---

## PART 4 · FinOps con infracost (30 min)
L'IaC rende facile creare risorse — quindi facile **spendere**. `infracost` legge il `terraform plan` e ti dice il costo **prima** di applicare.
```bash
infracost breakdown --path .
```
Vedrai una tabella col costo mensile stimato. L'istanza `aws_instance.app` (in `finops.tf`, non la applichiamo: è per la stima) pesa quanto il suo **tipo**:

| instance_type | costo mensile stimato (on-demand, us-east-1) |
|---|---|
| `t3.micro` (default) | ~$7.6 / mese |
| `t3.large` | ~$61 / mese |

**Right-sizing**: cambia il tipo e ri-stima la differenza —
```bash
infracost breakdown --path . --terraform-var 'create_finops_demo=true' --terraform-var 'instance_type=t3.micro' --format json --out-file infracost-base.json

infracost diff --path . --compare-to infracost-base.json --terraform-var 'create_finops_demo=true' --terraform-var 'instance_type=t3.large'

Remove-Item .\infracost-base.json
```
`+$53/mese` per una riga cambiata. Ecco perché il costo si guarda **nel piano**, non in bolletta. E i **tag** `CostCenter` (che il modulo impone) sono ciò che poi ti fa spaccare la spesa per team in Cost Explorer.

---

## 🧹 Cleanup + autovalutazione (5 min)
```bash
terraform destroy    # 'yes' — smonta i bucket
```
**Sei a posto se…**
- hai creato dev **e** prod con **un solo modulo** (standardizzazione);
- hai **generato** il README con terraform-docs;
- la policy `CKV_ACME_TAGS` **passa** sul modulo e **fallisce** sul bucket ribelle;
- sai leggere un `infracost breakdown` e stimare l'impatto di un cambio di sizing **prima** di applicare.

## 🆘 Troubleshooting
- **`infracost` chiede una chiave** → `infracost auth login` (gratis, una volta).
- **`checkov` non trova la policy** → il percorso di `--external-checks-dir` punta a `policies/`?
- **`ExpiredToken`** → STS del lab scadute, rigenera `~/.aws/credentials`.

## 🏆 CHALLENGE — DRY con `for_each`
Adesso hai due `module` quasi identici (dev, prod). Trasformali in **uno solo** che cicla su una mappa di ambienti:
```hcl
variable "envs" {
  default = {
    dev  = { cost_center = "CC-1001" }
    prod = { cost_center = "CC-1002" }
  }
}
module "logs" {
  for_each    = var.envs
  source      = "./modules/secure-bucket"
  name        = "acme-logs"
  env         = each.key
  owner       = "team-piattaforma"
  cost_center = each.value.cost_center
}
```
Un blocco solo per tutti gli ambienti. E se un domani serve un terzo ambiente (es. `staging`)? Lo aggiungi alla mappa **e** alla lista consentita nel modulo (`variables.tf`): la governance ti obbliga a una **decisione consapevole**, non a un incidente. È lo stesso mattoncino, moltiplicato — l'anticipo della prossima lezione (IaC su scala).