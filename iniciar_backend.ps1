$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Prepare o ambiente seguindo o README.md.' }
& $pythonPath -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
exit $LASTEXITCODE
