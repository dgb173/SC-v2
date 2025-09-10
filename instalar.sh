#!/bin/bash
# Script de instalación para Linux/Mac

echo "========================================"
echo "Instalador del Proyecto de Análisis de Partidos"
echo "========================================"

echo ""
echo "1/4 Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Python no encontrado. Por favor instale Python 3.8 o superior."
    exit 1
fi

echo ""
echo "2/4 Creando entorno virtual..."
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Error al crear el entorno virtual"
        exit 1
    fi
fi

echo ""
echo "3/4 Instalando dependencias..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error al instalar las dependencias"
    exit 1
fi

echo ""
echo "4/4 Instalando navegadores para Playwright..."
.venv/bin/python -m playwright install chromium
if [ $? -ne 0 ]; then
    echo "Advertencia: No se pudieron instalar los navegadores de Playwright"
    echo "Esto puede deberse a permisos. Puede intentar ejecutar con sudo."
fi

echo ""
echo "Instalación completada!"
echo ""
echo "Para ejecutar la aplicación:"
echo "1. Active el entorno virtual: source .venv/bin/activate"
echo "2. Ejecute: streamlit run app.py"
echo ""
echo "O simplemente ejecute: chmod +x empezar_aqui.sh && ./empezar_aqui.sh"