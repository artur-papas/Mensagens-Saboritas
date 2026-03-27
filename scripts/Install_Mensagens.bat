@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "PYTHON_EXE="

cd /d "%PROJECT_ROOT%"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_EXE=python"
    ) else (
        echo Python 3 nao foi encontrado.
        echo Instale o Python 3.11+ e execute este instalador novamente.
        echo.
        pause
        exit /b 1
    )
)

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js nao foi encontrado.
    echo Instale o Node.js LTS em:
    echo   https://nodejs.org/
    echo.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo npm nao foi encontrado.
    echo Reinstale o Node.js LTS em:
    echo   https://nodejs.org/
    echo.
    pause
    exit /b 1
)

where appium >nul 2>nul
if errorlevel 1 (
    echo Appium nao foi encontrado.
    echo Instale o Appium com:
    echo   npm install -g appium
    echo.
    echo Site oficial:
    echo   https://appium.io/
    echo.
    pause
    exit /b 1
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Criando ambiente virtual...
    call %PYTHON_EXE% -m venv "%VENV_DIR%"
    if errorlevel 1 goto :fail
)

echo Instalando dependencias do projeto...
call "%VENV_DIR%\Scripts\python.exe" -m pip install --disable-pip-version-check -e "%PROJECT_ROOT%"
if errorlevel 1 goto :fail

call "%VENV_DIR%\Scripts\python.exe" -c "import emoji, appium"
if errorlevel 1 (
    echo.
    echo As dependencias Python do projeto nao foram instaladas corretamente.
    echo Tente executar o instalador novamente.
    echo.
    pause
    exit /b 1
)

if not exist "%PROJECT_ROOT%\configuracao.json" (
    if exist "%PROJECT_ROOT%\configuracao.exemplo.json" (
        echo Criando configuracao.json a partir do exemplo...
        copy /y "%PROJECT_ROOT%\configuracao.exemplo.json" "%PROJECT_ROOT%\configuracao.json" >nul
    ) else (
        echo Criando configuracao.json a partir do arquivo legado...
        copy /y "%PROJECT_ROOT%\mensagens_saboritas.example.json" "%PROJECT_ROOT%\configuracao.json" >nul
    )
    if errorlevel 1 goto :fail
)

echo.
echo Instalacao concluida.
echo Abra o aplicativo com um duplo clique em:
echo   %PROJECT_ROOT%\USO\scripts\Mensagens.bat
echo.
pause
exit /b 0

:fail
echo.
echo Falha na instalacao.
echo Revise os erros acima e pressione qualquer tecla para fechar.
echo.
pause
exit /b 1
