@echo off
echo ========================================
echo Instalador del Proyecto de Análisis de Partidos
echo ========================================

echo.
echo 1/4 Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python no encontrado. Verificando en el entorno virtual...
    if exist ".venv\Scripts\python.exe" (
        echo Usando Python del entorno virtual
        set PYTHON=.venv\Scripts\python.exe
    ) else (
        echo No se encontró Python. Por favor instale Python 3.8 o superior.
        pause
        exit /b 1
    )
) else (
    set PYTHON=python
)

echo.
echo 2/4 Creando entorno virtual...
if not exist ".venv" (
    %PYTHON% -m venv .venv
    if %errorlevel% neq 0 (
        echo Error al crear el entorno virtual
        pause
        exit /b 1
    )
)

echo.
echo 3/4 Instalando dependencias...
.venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error al instalar las dependencias
    pause
    exit /b 1
)

echo.
echo 4/4 Instalando navegadores para Playwright...
.venv\Scripts\python.exe -m playwright install chromium
if %errorlevel% neq 0 (
    echo Advertencia: No se pudieron instalar los navegadores de Playwright
    echo Esto puede deberse a permisos. Puede intentar ejecutar como administrador.
)

echo.
echo Instalación completada!
echo.
echo Para ejecutar la aplicación:
echo 1. Active el entorno virtual: .venv\Scripts\activate
echo 2. Ejecute: streamlit run app.py
echo.
echo O simplemente ejecute: EMPEZAR_AQUI.bat
pause