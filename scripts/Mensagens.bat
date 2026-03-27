@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"

cd /d "%PROJECT_ROOT%"

if not exist "%VENV_PYTHON%" (
    echo O ambiente local do projeto nao foi encontrado.
    echo Execute primeiro:
    echo   %PROJECT_ROOT%\USO\scripts\Instalar_Mensagens.bat
    echo.
    pause
    exit /b 1
)

call "%VENV_PYTHON%" -c "import emoji, appium"
if errorlevel 1 (
    echo As dependencias Python do projeto nao estao instaladas corretamente.
    echo Execute novamente:
    echo   %PROJECT_ROOT%\USO\scripts\Instalar_Mensagens.bat
    echo.
    pause
    exit /b 1
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

call "%VENV_PYTHON%" "%PROJECT_ROOT%\scripts\launcher.py" --project-root "%PROJECT_ROOT%" %*

if errorlevel 1 (
    echo.
    echo Falha ao abrir o aplicativo.
    echo Se necessario, reinstale o ambiente com:
    echo   %PROJECT_ROOT%\USO\scripts\Instalar_Mensagens.bat
    echo.
    pause
)
