import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    import streamlit as st
    print("✓ Streamlit imported successfully")
except ImportError as e:
    print(f"✗ Error importing Streamlit: {e}")

try:
    from modules.estudio_scraper import obtener_datos_completos_partido
    print("✓ estudio_scraper imported successfully")
except ImportError as e:
    print(f"✗ Error importing estudio_scraper: {e}")

try:
    from modules.analisis_avanzado import generar_analisis_completo_mercado
    print("✓ analisis_avanzado imported successfully")
except ImportError as e:
    print(f"✗ Error importing analisis_avanzado: {e}")

try:
    from modules.utils import format_ah_as_decimal_string_of, parse_ah_to_number_of
    print("✓ utils imported successfully")
except ImportError as e:
    print(f"✗ Error importing utils: {e}")

try:
    import asyncio
    print("✓ asyncio imported successfully")
except ImportError as e:
    print(f"✗ Error importing asyncio: {e}")

try:
    from playwright.async_api import async_playwright
    print("✓ Playwright imported successfully")
except ImportError as e:
    print(f"✗ Error importing Playwright: {e}")

try:
    from bs4 import BeautifulSoup
    print("✓ BeautifulSoup imported successfully")
except ImportError as e:
    print(f"✗ Error importing BeautifulSoup: {e}")

print("Import test completed.")