#!/usr/bin/env bash
# Gate fatto in casa: nel repository non ci devono essere segreti.
# Se ne trova uno esce con 1 e la pipeline si ferma.
#   uso:  bash script/sniffa-segreti.sh [cartella]
set -u
CARTELLA="${1:-.}"

SCHEMI='AKIA[0-9A-Z]{16}'                       # chiave di accesso AWS
SCHEMI="$SCHEMI|ghp_[A-Za-z0-9]{36}"            # token personale GitHub
SCHEMI="$SCHEMI|-----BEGIN [A-Z ]*PRIVATE KEY"  # chiave privata
SCHEMI="$SCHEMI|AWS_SECRET_ACCESS_KEY[[:space:]]*[:=][[:space:]]*[A-Za-z0-9/+]{40}"
SCHEMI="$SCHEMI|(password|passwd|api[_-]?token)[[:space:]]*[:=][[:space:]]*.{8,}"

TROVATI=$(grep -rInE "$SCHEMI" "$CARTELLA" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.terraform --exclude-dir=dist --exclude=package-lock.json --exclude=sniffa-segreti.sh 2>/dev/null)

if [ -n "$TROVATI" ]; then
  echo "SEGRETI TROVATI - la pipeline si ferma:"
  echo "$TROVATI"
  exit 1
fi

echo "nessun segreto sospetto in $CARTELLA"