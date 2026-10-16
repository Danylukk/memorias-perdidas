@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0PREPARAR_PARA_GRAVAR.ps1"
if errorlevel 1 (
    echo.
    echo Houve um problema na preparacao. Consulte a mensagem acima.
    pause
)
