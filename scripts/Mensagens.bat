@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"

cd /d "%PROJECT_ROOT%"

if exist "%VENV_PYTHON%" (
    call "%VENV_PYTHON%" "%PROJECT_ROOT%\scripts\launcher.py" --project-root "%PROJECT_ROOT%" %*
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        py -3 "%PROJECT_ROOT%\scripts\launcher.py" --project-root "%PROJECT_ROOT%" %*
    ) else (
        python "%PROJECT_ROOT%\scripts\launcher.py" --project-root "%PROJECT_ROOT%" %*
    )
)

if errorlevel 1 (
    echo.
    echo Falha ao abrir o aplicativo. Instale as dependencias primeiro:
    echo   %PROJECT_ROOT%\scripts\Instalar_Mensagens.bat
    echo.
    pause
)
