# Génère Workshop2026-M2-G<n>-Code.zip (rendu impératif)
# Usage : .\scripts\make-archive.ps1 -Group 13
# Exclut : secrets/, __pycache__, *.pyc, node_modules, .git, models/*.joblib

param(
    [int]$Group = 13
)

$name    = "Workshop2026-M2-G$Group-Code"
$outDir  = "$PSScriptRoot\..\..\"
$zipPath = Join-Path $outDir "$name.zip"
$src     = (Resolve-Path "$PSScriptRoot\..").Path

# Dossiers / fichiers à exclure
$excludes = @(
    "secrets",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "node_modules",
    ".git",
    "*.joblib",        # modèles binaires (trop lourds, regénérables)
    ".env"             # config locale (contient ESP8266_IP, pas de secret mais hors archive)
)

Write-Host "Archive : $zipPath"
Write-Host "Source  : $src"

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

# Utilise 7z si dispo, sinon Compress-Archive
$7z = (Get-Command "7z" -ErrorAction SilentlyContinue)?.Source

if ($7z) {
    $excludeArgs = $excludes | ForEach-Object { "-xr!$_" }
    & $7z a -tzip $zipPath "$src\*" @excludeArgs -mx=5
} else {
    # Fallback PowerShell natif (plus lent)
    $files = Get-ChildItem $src -Recurse -File | Where-Object {
        $rel = $_.FullName.Substring($src.Length + 1)
        $skip = $false
        foreach ($ex in $excludes) {
            if ($rel -like "*$ex*") { $skip = $true; break }
        }
        -not $skip
    }
    Compress-Archive -Path $files.FullName -DestinationPath $zipPath -CompressionLevel Optimal
}

Write-Host "OK — $zipPath"
