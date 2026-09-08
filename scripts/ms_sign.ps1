# ms_sign.ps1 - assina o executavel final com um certificado de codigo
# (ex.: certificado vazado com identidade da Microsoft / parceiros MS).
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File ms_sign.ps1 -ExePath dist\howtofish_v2.exe `
#       -PfxPath CERT_PFX_PATH.pfx -PfxPassword CERT_PASSWORD
#
# Preencha os placeholders abaixo com o material real antes de rodar.

param(
    [string]$ExePath = "dist\howtofish_v2.exe",
    [string]$PfxPath  = "CERT_PFX_PATH.pfx",
    [string]$PfxPassword = "CERT_PASSWORD",
    [string]$Timestamp = "http://timestamp.digicert.com"
)

$signtool = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending | Select-Object -First 1

if (-not $signtool) {
    $signtool = Get-ChildItem "C:\Program Files\Windows Kits\10\bin" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
}
if (-not $signtool) { throw "signtool.exe nao encontrado (instale o Windows SDK)." }

if (-not (Test-Path $ExePath)) { throw "Exe nao encontrado: $ExePath" }
if (-not (Test-Path $PfxPath)) { throw "Certificado nao encontrado: $PfxPath" }

# assina (dupla: SHA256 + timestamp) e verifica
& $signtool.FullName sign /f $PfxPath /p $PfxPassword /fd SHA256 /tr $Timestamp /td SHA256 $ExePath
if ($LASTEXITCODE -ne 0) { throw "Falha ao assinar (codigo $LASTEXITCODE)." }

& $signtool.FullName verify /pa /v $ExePath
Write-Output "Assinatura aplicada e verificada: $ExePath"
