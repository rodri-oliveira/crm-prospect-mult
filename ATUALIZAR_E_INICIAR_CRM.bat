@echo off
setlocal
cd /d "%~dp0"
echo Feche a janela antiga do CRM antes de continuar.
echo Atualizando o projeto nesta pasta: "%CD%"
git pull --ff-only origin master
if errorlevel 1 (
    echo Nao foi possivel atualizar. Nenhum arquivo local foi descartado.
    pause
    exit /b 1
)
set CRM_AUTO_RELOAD=1
py "%~dp0app.py"
pause
