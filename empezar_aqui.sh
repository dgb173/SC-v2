#!/bin/bash
# Script para ejecutar la aplicación en Linux/Mac

echo "========================================"
echo "Ejecutando Proyecto de Análisis de Partidos"
echo "========================================"

echo ""
echo "Verificando entorno virtual..."
if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Error al crear el entorno virtual. Asegúrese de tener Python instalado."
        exit 1
    fi
fi

echo ""
echo "Verificando dependencias..."
.venv/bin/pip show streamlit > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Instalando dependencias..."
    .venv/bin/pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error al instalar las dependencias"
        exit 1
    fi
fi

echo ""
echo "Verificando navegadores de Playwright..."
.venv/bin/python -c "import playwright; print('Playwright disponible')" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Instalando navegadores para Playwright..."
    .venv/bin/python -m playwright install chromium
    if [ $? -ne 0 ]; then
        echo "Advertencia: No se pudieron instalar los navegadores de Playwright"
        echo "Puede continuar, pero es posible que algunas funciones no funcionen correctamente."
    fi
fi

echo ""
echo "Iniciando aplicación Streamlit..."
.venv/bin/streamlit run app.py