# DriftHunter — il guardiano (versione WINDOWS).
# Fa un plan e ti dice se c'è drift.  Exit: 0 = ok · 2 = DRIFT · 1 = errore.
# Uso:  .\drift-check.ps1

Set-Location $PSScriptRoot

$planFile = "C:\Users\riccardo.gouthier\AppData\Local\Temp\26\drift-plan.txt"
Write-Host "🔍 DriftHunter — controllo drift $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
terraform plan -detailed-exitcode -no-color -input=false > $planFile 2>&1
$code = $LASTEXITCODE

switch ($code) {
    0 { Write-Host "✅ Nessun drift: codice e cloud sono allineati." }
    2 {
        Write-Host "⚠️  DRIFT RILEVATO — qualcuno ha toccato l'infrastruttura a mano:"
        Select-String -Path $planFile -Pattern "will be updated|will be destroyed|must be replaced|forces replacement" |
            Select-Object -First 10 | ForEach-Object { Write-Host "    $($_.Line)" }
        Write-Host "    (piano completo in $planFile)"
        exit 2
    }
    default {
        Write-Host "❌ Errore nel plan (credenziali/backend?). Vedi $planFile"
        exit 1
    }
}
