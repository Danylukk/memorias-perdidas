$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Prepare o ambiente seguindo o README.md.' }
& $pythonPath frontend/main.py
exit $LASTEXITCODE
