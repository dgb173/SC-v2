@echo off
echo ========================================
echo Ejecutando Proyecto de Análisis de Partidos
echo ========================================

echo.
echo Verificando entorno virtual...
if not exist ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo Error al crear el entorno virtual. Asegúrese de tener Python instalado.
        pause
        exit /b 1
    )
)

echo.
echo Verificando dependencias...
.venv\Scripts\pip.exe show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias...
    .venv\Scripts\pip.exe install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error al instalar las dependencias
        pause
        exit /b 1
    )
)

echo.
echo Verificando navegadores de Playwright...
.venv\Scripts\python.exe -c "import playwright; print('Playwright disponible')" >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando navegadores para Playwright...
    .venv\Scripts\python.exe -m playwright install chromium
    if %errorlevel% neq 0 (
        echo Advertencia: No se pudieron instalar los navegadores de Playwright
        echo Puede continuar, pero es posible que algunas funciones no funcionen correctamente.
    )
)

echo.
echo Iniciando aplicación Streamlit...
.venv\Scripts\streamlit.exe run app.py

pause