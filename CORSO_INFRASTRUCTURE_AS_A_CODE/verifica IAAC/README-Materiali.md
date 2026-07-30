# Materiali della prova pratica — commessa AulaCloud

Cartella `aulacloud/`:

| File | A cosa serve |
|---|---|
| `main.tf` | il progetto, con i quattro TODO da completare |
| `variables.tf` | le variabili (`matricola`, `env`, `cost_center`) — non serve modificarle |
| `modules/secure-bucket/` | il modulo aziendale **già pronto**: si usa, non si modifica |
| `fase2c-import.tf.esempio` | serve alla fase 2c: rinominalo in `fase2c-import.tf` e metti il tuo cognome |
| `offline_override.tf.esempio` | piano B: rinominalo in `offline_override.tf` **solo** se il Learner Lab non parte |

## Per partire

```
cd aulacloud
terraform init
terraform plan -var matricola=TUOCOGNOME
```

Il piano funziona anche prima di completare i TODO: serve a controllare che
l'ambiente sia a posto.

**Ricorda:** usa il tuo cognome in minuscolo come `matricola`. I nomi dei bucket S3
sono unici in tutto il mondo.
