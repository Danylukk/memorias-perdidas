$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$root = $PSScriptRoot
$pythonPath = Join-Path $root '.venv\Scripts\python.exe'
$backendEnv = Join-Path $root 'backend\.env'

Write-Host ''
Write-Host 'MEMORIAS PERDIDAS - PREPARACAO PARA GRAVAR FRONT-END' -ForegroundColor Cyan
Write-Host 'As credenciais permanecem somente neste computador.'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    Write-Host 'Criando ambiente virtual (primeira execucao)...'
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv .venv 2>$null
        if ($LASTEXITCODE -ne 0) { & py -3 -m venv .venv }
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw 'Python nao encontrado. Instale Python 3.12+ e execute novamente.'
    }
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        throw 'Nao foi possivel criar o ambiente virtual.'
    }
}

& $pythonPath -c 'import fastapi, uvicorn, requests, pygame, openai, dotenv, pytest'
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Instalando dependencias; a primeira execucao pode demorar...'
    & $pythonPath -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falha na instalacao das dependencias.' }
}

& $pythonPath scripts/preparar_gravacao.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host 'Configure somente os campos pendentes no arquivo aberto.' -ForegroundColor Yellow
    Write-Host 'NUNCA mostre este arquivo durante a gravacao.'
    Start-Process notepad.exe -ArgumentList ('"' + $backendEnv + '"')
    [void](Read-Host 'Depois de salvar e fechar o Notepad, pressione ENTER')
    & $pythonPath scripts/preparar_gravacao.py
    if ($LASTEXITCODE -ne 0) {
        throw 'Configuracao ainda pendente. Veja backend/.env e frontend/.env.'
    }
}

function Test-OurApi {
    try {
        $schema = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/openapi.json' -TimeoutSec 2
        return (@($schema.paths.PSObject.Properties.Name) -contains '/v1/ia-generativa/texto')
    } catch { return $false }
}

if (-not (Test-OurApi)) {
    Write-Host 'Abrindo servidor FastAPI em outra janela...'
    $backendScript = Join-Path $root 'iniciar_backend.ps1'
    Start-Process -FilePath 'powershell.exe' -WorkingDirectory $root -ArgumentList @(
        '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $backendScript + '"')
    )
    $ready = $false
    for ($i = 0; $i -lt 35; $i++) {
        Start-Sleep -Milliseconds 600
        if (Test-OurApi) { $ready = $true; break }
    }
    if (-not $ready) {
        throw 'O backend nao respondeu na porta 8000. Verifique a janela da API.'
    }
}

Write-Host 'FastAPI e Swagger disponiveis.' -ForegroundColor Green
Start-Process 'http://127.0.0.1:8000/docs'

Write-Host 'Abrindo o jogo na tela inicial...'
$jogoScript = Join-Path $root 'iniciar_jogo.ps1'
Start-Process -FilePath 'powershell.exe' -WorkingDirectory $root -ArgumentList @(
    '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $jogoScript + '"')
)

Write-Host ''
Write-Host 'PRONTO: 1) inicie sua gravacao; 2) mostre Swagger; 3) clique NOVO JOGO; 4) mostre o POST 200 no terminal.' -ForegroundColor Green
Write-Host 'Roteiro detalhado: ROTEIRO_GRAVACAO_FRONTEND.md'
Write-Host 'Nao mostre as janelas .env ou as credenciais no video.'
