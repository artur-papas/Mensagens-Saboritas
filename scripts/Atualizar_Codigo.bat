@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"

cd /d "%PROJECT_ROOT%"

where git >nul 2>nul
if errorlevel 1 (
    echo Git nao foi encontrado.
    echo Instale o Git para Windows e execute este script novamente.
    echo.
    pause
    exit /b 1
)

for /f "usebackq delims=" %%I in (`git rev-parse --is-inside-work-tree 2^>nul`) do set "IS_GIT=%%I"
if /I not "%IS_GIT%"=="true" (
    echo Esta pasta nao e um repositorio Git.
    echo.
    pause
    exit /b 1
)

for /f "usebackq delims=" %%I in (`git branch --show-current`) do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="main" (
    echo A branch atual e "%CURRENT_BRANCH%".
    echo Este script atualiza apenas a branch main.
    echo Troque para main e execute novamente.
    echo.
    pause
    exit /b 1
)

git diff --quiet
if errorlevel 1 (
    echo Existem alteracoes locais nao salvas.
    echo Faça commit, stash ou descarte as alteracoes antes de atualizar.
    echo.
    pause
    exit /b 1
)

git diff --cached --quiet
if errorlevel 1 (
    echo Existem alteracoes preparadas para commit.
    echo Faça commit ou limpe o index antes de atualizar.
    echo.
    pause
    exit /b 1
)

echo Buscando atualizacoes do GitHub...
git fetch origin main
if errorlevel 1 goto :fail

echo Aplicando atualizacoes da branch main...
git pull --ff-only origin main
if errorlevel 1 goto :fail

echo.
echo Codigo atualizado com sucesso.
echo Se houver mudancas de dependencias, execute:
echo   %PROJECT_ROOT%\scripts\Instalar_Mensagens.bat
echo.
pause
exit /b 0

:fail
echo.
echo Falha ao atualizar o codigo.
echo Revise os erros acima e tente novamente.
echo.
pause
exit /b 1
