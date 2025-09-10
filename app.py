import streamlit as st
import subprocess
import sys

# ----------------- BLOQUE DE INSTALACIÓN DE PLAYWRIGHT -----------------
# Este bloque se asegura de que los navegadores de Playwright estén instalados
# en el entorno de Streamlit Cloud.
@st.cache_resource
def install_playwright_browsers():
    with st.spinner("Instalando navegadores para Playwright (esto solo ocurre una vez)..."):
        try:
            # Usamos python -m para ser más robustos
            subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            st.error("Error al instalar los navegadores de Playwright.")
            st.exception(e)
            st.stop()

# Llamamos a la función de instalación
install_playwright_browsers()
# --------------------------------------------------------------------

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import datetime
import pandas as pd

# Importar las funciones principales de los módulos de scraping
from modules.estudio_scraper import obtener_datos_completos_partido
from modules.utils import format_ah_as_decimal_string_of as format_ah_util

# --- Configuración de la página de Streamlit ---
st.set_page_config(
    page_title="Análisis de Partidos",
    page_icon="⚽",
    layout="wide",
)

# --- Título y Descripción ---
st.title("⚽ Analizador de Partidos de Fútbol")
st.markdown("""
Esta aplicación extrae y analiza datos de partidos de fútbol para proporcionar información detallada 
sobre rendimiento, enfrentamientos directos (H2H) y mercados de apuestas.
""")

# --- Lógica para obtener y mostrar la lista de próximos partidos (CORREGIDO) ---
URL_NOWGOAL = "https://live20.nowgoal25.com/"

# 1. La función de parseo sigue igual y se puede cachear porque es una función pura.
@st.cache_data(ttl=600) # Cachear los resultados por 10 minutos
def parse_main_page_matches(html_content, limit=50):
    soup = BeautifulSoup(html_content, 'html.parser')
    match_rows = soup.find_all('tr', id=lambda x: x and x.startswith('tr1_'))
    upcoming_matches = []
    now_utc = datetime.datetime.utcnow()

    for row in match_rows:
        match_id = row.get('id', '').replace('tr1_', '')
        if not match_id: continue

        time_cell = row.find('td', {'name': 'timeData'})
        if not time_cell or not time_cell.has_attr('data-t'): continue
        
        try:
            match_time = datetime.datetime.strptime(time_cell['data-t'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, IndexError):
            continue

        if match_time < now_utc: continue

        home_team_tag = row.find('a', {'id': f'team1_{match_id}'})
        away_team_tag = row.find('a', {'id': f'team2_{match_id}'})
        odds_data = row.get('odds', '').split(',')
        handicap = odds_data[2] if len(odds_data) > 2 else "N/A"
        goal_line = odds_data[10] if len(odds_data) > 10 else "N/A"

        if not handicap or handicap == "N/A" or not goal_line or goal_line == "N/A":
            continue

        upcoming_matches.append({
            "ID": match_id,
            "Hora": match_time.strftime('%Y-%m-%d %H:%M'),
            "Local": home_team_tag.text.strip() if home_team_tag else "N/A",
            "Visitante": away_team_tag.text.strip() if away_team_tag else "N/A",
            "Hándicap": handicap,
            "Línea de Gol": goal_line
        })

    upcoming_matches.sort(key=lambda x: x['Hora'])
    return upcoming_matches[:limit]

# 2. Función asíncrona que SOLO obtiene el HTML. No se cachea.
async def _get_main_page_html_async():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = await browser.new_page()
        try:
            await page.goto(URL_NOWGOAL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(5000)
            return await page.content()
        finally:
            await browser.close()

# 3. Función síncrona que ORQUESTA todo. ESTA es la que se cachea.
@st.cache_data(ttl=600)
def get_upcoming_matches_data():
    """
    Esta función síncrona llama a la lógica asíncrona para obtener el HTML
    y luego lo pasa a la función de parseo. El resultado final (una lista)
    es serializable y se puede cachear de forma segura.
    """
    html_content = asyncio.run(_get_main_page_html_async())
    return parse_main_page_matches(html_content)

# --- Sección de Próximos Partidos ---
st.header("📅 Próximos Partidos")
if st.button("Cargar Próximos Partidos"):
    with st.spinner("Buscando partidos en Nowgoal... Esto puede tardar un momento."):
        try:
            # 4. Se llama a la nueva función síncrona cacheable
            matches_data = get_upcoming_matches_data()
            if matches_data:
                df = pd.DataFrame(matches_data)
                st.dataframe(df, use_container_width=True)
                st.success(f"Se encontraron {len(matches_data)} partidos.")
            else:
                st.warning("No se encontraron próximos partidos que cumplan los criterios.")
        except Exception as e:
            st.error(f"No se pudieron cargar los partidos: {e}")
            st.exception(e) # Muestra el traceback completo para más detalles

# --- Sección de Análisis de Partido por ID ---
st.header("🔍 Analizar Partido por ID")
st.markdown("Copia la ID de un partido de la tabla de arriba o introduce la de cualquier otro partido de Nowgoal.")

match_id_input = st.text_input("ID del Partido", placeholder="Ej: 2490187")

if st.button("Analizar Partido"):
    if not match_id_input or not match_id_input.isdigit():
        st.error("Por favor, introduce una ID de partido válida (solo números).")
    else:
        with st.spinner(f"Realizando análisis completo para el partido {match_id_input}..."):
            try:
                # Llama a la función principal del scraper
                datos_partido = obtener_datos_completos_partido(match_id_input)

                if not datos_partido or "error" in datos_partido:
                    st.error(f"Error al obtener datos: {datos_partido.get('error', 'Error desconocido')}")
                else:
                    st.success(f"Análisis completado para: **{datos_partido['home_name']} vs {datos_partido['away_name']}**")
                    
                    # Mostrar los análisis generados en HTML
                    st.subheader("Análisis de Mercado y H2H")
                    st.markdown(datos_partido.get("market_analysis_html", "No disponible."), unsafe_allow_html=True)
                    
                    st.subheader("Análisis de Rendimiento Reciente")
                    st.markdown(datos_partido.get("recent_performance_analysis_html", "No disponible."), unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Ocurrió un error crítico durante el análisis: {e}")
                st.exception(e) # Muestra el traceback completo para más detalles