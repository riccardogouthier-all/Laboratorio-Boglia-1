# =============================================================
#  Questo file viene caricato IN AUTOMATICO da Terraform.
#  È il modo normale di passare i valori alle variabili.
#
#  ATTENZIONE: i .tfvars spesso contengono roba sensibile
#  -> stanno nel .gitignore. Si committa semmai un example.tfvars finto.
# =============================================================

bucket_name = "its-iac-riccardo-01" # <<<<<< lo STESSO nome del bucket che avete già!
environment = "dev"
owner       = "riccardo"

# Altri modi di passare i valori (in ordine di precedenza crescente):
#   1. variabile d'ambiente:  export TF_VAR_environment=prod   <- così fanno le pipeline CI/CD
#   2. questo file
#   3. riga di comando:       terraform apply -var="environment=prod"   <- vince su tutto
