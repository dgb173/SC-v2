import streamlit as st
import sys
import subprocess

# Test script to verify Streamlit app requirements

st.title("Test de Verificación del Proyecto")

st.write("Verificando instalación de dependencias...")

# Check if required packages are installed
required_packages = ['streamlit', 'playwright', 'pandas', 'beautifulsoup4', 'requests', 'lxml']

try:
    import streamlit as st
    st.success("✅ Streamlit instalado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar Streamlit: {e}")

try:
    import playwright
    st.success("✅ Playwright instalado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar Playwright: {e}")

try:
    import pandas as pd
    st.success("✅ Pandas instalado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar Pandas: {e}")

try:
    import bs4
    st.success("✅ BeautifulSoup4 instalado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar BeautifulSoup4: {e}")

try:
    import requests
    st.success("✅ Requests instalado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar Requests: {e}")

try:
    import lxml
    st.success("✅ LXML instalado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar LXML: {e}")

st.write("Verificando módulos personalizados...")

# Check custom modules
try:
    from modules.estudio_scraper import obtener_datos_completos_partido
    st.success("✅ Módulo estudio_scraper importado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar estudio_scraper: {e}")

try:
    from modules.analisis_avanzado import generar_analisis_completo_mercado
    st.success("✅ Módulo analisis_avanzado importado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar analisis_avanzado: {e}")

try:
    from modules.utils import parse_ah_to_number_of, format_ah_as_decimal_string_of
    st.success("✅ Módulo utils importado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar utils: {e}")

st.write("Verificando instalación de navegadores Playwright...")

try:
    result = subprocess.run([sys.executable, "-m", "playwright", "install-deps"], 
                          capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        st.success("✅ Dependencias de Playwright instaladas")
    else:
        st.warning(f"⚠️ Advertencia en instalación de dependencias: {result.stderr}")
except Exception as e:
    st.warning(f"⚠️ No se pudieron instalar dependencias de Playwright: {e}")

st.write("✅ Verificación completada. Si no hay errores, el proyecto debería funcionar correctamente.")