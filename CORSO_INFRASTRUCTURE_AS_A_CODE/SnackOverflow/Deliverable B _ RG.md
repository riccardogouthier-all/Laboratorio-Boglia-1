# Decisioni architetturali — SnackOverflow S.r.l.

One-pager: una riga per pilastro Well-Architected. Dettaglio completo delle
motivazioni in `relazione-collaudo.md`.

| Pilastro | Decisione |
|---|---|
| **Sicurezza** | Nessuna password nel codice: `AWS::SecretsManager::Secret` genera la credenziale RDS, letta a runtime via dynamic reference `{{resolve:secretsmanager:...}}`. Catena di Security Group (ALB → App → DB), mai CIDR dopo l'ALB: un CIDR di subnet include qualunque istanza vi nasca, un SG identifica solo la risorsa giusta anche se subnet/IP cambiano. |
| **Affidabilità** | ALB e ASG distribuiti su 2 AZ (`PublicSubnetA/B`); se un'AZ cade, l'altra serve il traffico. RDS single-AZ in dev (vincolo Learner Lab), Multi-AZ disegnato per prod. Bucket asset con `DeletionPolicy: Retain`, RDS con `Snapshot`: i dati critici non si cancellano per sbaglio con `delete-stack`. |
| **Prestazioni** | ASG con `MinSize`/`MaxSize` per ambiente (Mapping `EnvMap`): la capacità cresce col carico (es. picco 10:30) e si riduce a riposo, senza sovradimensionamento fisso. DynamoDB `PAY_PER_REQUEST` per sessioni ad alta frequenza, nessuna capacità da pre-allocare. |
| **Costi** | Stesso codice, sizing diverso via `Mappings` (`EnvType`: dev → `t3.micro`/`db.t3.micro`, prod → `t3.small`/`db.t3.small`). `Condition CreateDatabase` permette di saltare l'RDS in dev quando non serve aspettare il provisioning. |
| **Operabilità** | Stack nasce/muore con un comando (`aws cloudformation deploy` / `delete-stack`). Le modifiche si vedono prima di applicarle tramite change set (`create-change-set` + `describe-change-set`, campo `Replacement`). Drift rilevato con `detect-stack-drift`, riconciliato ri-applicando il template (mai a mano in console). |
| **Sostenibilità** | Nessun sovradimensionamento statico: ASG scala col carico reale, RDS/istanze dimensionate per ambiente. DynamoDB serverless evita capacità inutilizzata h24 per un carico solo di picco. |
