# =============================================================
#  MODULO "bucket" — la logica
#
#  Un modulo è solo UNA CARTELLA CON DEI FILE .tf. Nient'altro.
#  Convenzione: la risorsa principale di un modulo si chiama "this".
#
#  NB: qui NON si mettono provider{} né backend{}: li dichiara il root.
# =============================================================

resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  tags   = var.tags
}
