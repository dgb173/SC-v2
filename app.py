
import streamlit as st
import asyncio
import pandas as pd
import subprocess
import sys
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import datetime

# --- Dependencias del Proyecto ---
from modules.estudio_scraper import obtener_datos_completos_partido # Sigue siendo nuestro scraper principal
from modules.analisis_avanzado import generar_analisis_completo_mercado # Importamos la nueva lógica de análisis
from modules.utils import format_ah_as_decimal_string_of, parse_ah_to_number_of # Importamos helpers

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Análisis de Partidos",
    page_icon="⚽",
    layout="wide"
)

# --- Estilos CSS personalizados (inspirados en estudio.py) ---
st.markdown("""
<style>
    .main-title { font-size: 2.2em; font-weight: bold; color: #1E90FF; text-align: center; margin-bottom: 5px; }
    .sub-title { font-size: 1.6em; text-align: center; margin-bottom: 15px; }
    .section-header { font-size: 1.8em; font-weight: bold; color: #4682B4; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #4682B4; padding-bottom: 5px;}
    .card-title { font-size: 1.3em; font-weight: bold; color: #333; margin-bottom: 10px; }
    .home-color { color: #007bff; font-weight: bold; }
    .away-color { color: #fd7e14; font-weight: bold; }
    .score-value { font-size: 1.1em; font-weight: bold; color: #28a745; margin: 0 5px; }
    .ah-value { font-weight: bold; color: #6f42c1; }
    .data-highlight { font-weight: bold; color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# --- Instalación de Dependencias de Navegador ---
@st.cache_resource
def ensure_playwright_browsers_installed():
    st.info("Verificando instalación de navegadores para Playwright...")
    try:
        # Try to install browsers
        result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            st.warning(f"Advertencia en instalación de Playwright: {result.stderr}")
        st.success("✅ Navegadores de Playwright listos.")
    except Exception as e:
        st.warning(f"No se pudieron instalar los navegadores de Playwright: {e}")
        st.info("Continuando sin instalación automática...")

ensure_playwright_browsers_installed()

# --- Funciones de Carga de Datos ---
URL_NOWGOAL = "https://live20.nowgoal25.com/"

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

        # --- FILTRO MEJORADO ---
        odds_data = row.get('odds', '').split(',')
        if len(odds_data) < 11: continue # Si no hay suficientes datos de odds, se salta
        handicap = odds_data[2]
        goal_line = odds_data[10]
        if not handicap or handicap == "N/A" or not goal_line or goal_line == "N/A":
            continue

        home_team_tag = row.find('a', {'id': f'team1_{match_id}'})
        away_team_tag = row.find('a', {'id': f'team2_{match_id}'})
        
        upcoming_matches.append({
            "ID": match_id,
            "Hora": match_time.strftime('%H:%M'),
            "Fecha": match_time.strftime('%Y-%m-%d'),
            "Local": home_team_tag.text.strip() if home_team_tag else "N/A",
            "Visitante": away_team_tag.text.strip() if away_team_tag else "N/A",
        })

    upcoming_matches.sort(key=lambda x: (x['Fecha'], x['Hora']))
    return upcoming_matches[:limit]

@st.cache_data(ttl=600)
def get_main_page_matches_cached(limit=50):
    return asyncio.run(get_main_page_matches_async(limit))

async def get_main_page_matches_async(limit=50):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(URL_NOWGOAL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(5000)
            html_content = await page.content()
            return parse_main_page_matches(html_content, limit)
        finally:
            await browser.close()

# --- Lógica Principal de la App ---
st.title("⚽ Dashboard de Análisis de Partidos")

# Agregar información de ayuda
with st.expander("ℹ️ Cómo usar esta aplicación", expanded=False):
    st.markdown("""
    Esta aplicación analiza partidos de fútbol en tiempo real. 
    
    **Para usarla:**
    1. La aplicación mostrará una lista de próximos partidos disponibles
    2. Haz clic en "Analizar Partido" para cualquier partido de interés
    3. Se mostrará un análisis detallado del partido seleccionado
    
    **Nota:** La primera carga puede tardar unos segundos mientras se obtienen los datos.
    """)

if 'selected_match_id' not in st.session_state:
    st.session_state.selected_match_id = None

# --- VISTA DE ANÁLISIS DE PARTIDO ---\nif st.session_state.selected_match_id:\n    match_id = st.session_state.selected_match_id\n    \n    if st.button(\"⬅️ Volver a la lista de partidos\"):\n        st.session_state.selected_match_id = None\n        st.rerun()\n\n    with st.spinner(\"Obteniendo y analizando datos del partido...\"):\n        try:\n            datos_partido = obtener_datos_completos_partido(match_id)\n            \n            if not datos_partido or \"error\" in datos_partido:\n                st.error(f\"Error al obtener datos para el partido {match_id}: {datos_partido.get('error', 'Error desconocido')}\")\n                st.info(\"Esto puede deberse a problemas de conexión o a que el partido ya no está disponible.\")\n            else:\n                # --- RENDERIZADO DE LA NUEVA VISTA (INSPIRADA EN estudio.py) ---\n                home_name = datos_partido.get(\"home_name\", \"Local\")\n                away_name = datos_partido.get(\"away_name\", \"Visitante\")\n                \n                st.markdown(f\"<h1 class='main-title'>Análisis de Partido Avanzado</h1>\", unsafe_allow_html=True)\n                st.markdown(f\"<p class='sub-title'><span class='home-color'>{home_name}</span> vs <span class='away-color'>{away_name}</span></p>\", unsafe_allow_html=True)\n\n                # Extraer datos para la UI\n                main_match_odds_data = datos_partido.get(\"main_match_odds\", {})\n                h2h_data = datos_partido.get(\"h2h_stadium\", {})\n\n                # Generar y mostrar el análisis de mercado\n                try:\n                    analisis_mercado_html = generar_analisis_completo_mercado(\n                        main_match_odds_data,\n                        h2h_data, \n                        home_name, \n                        away_name,\n                        format_ah_as_decimal_string_of, # Pasamos las funciones helper\n                        parse_ah_to_number_of\n                    )\n                    st.markdown(analisis_mercado_html, unsafe_allow_html=True)\n                except Exception as e:\n                    st.error(f\"Error al generar el análisis de mercado: {str(e)}\")\n                    st.write(\"Datos disponibles:\", main_match_odds_data, h2h_data)\n\n                # Aquí puedes añadir más secciones de la UI de estudio.py si lo deseas\n                # Por ejemplo, la sección de clasificación:\n                with st.expander(\"📊 Clasificación en Liga\", expanded=True):\n                    home_standings = datos_partido.get(\"home_standings\", {})\n                    away_standings = datos_partido.get(\"away_standings\", {})\n                    scol1, scol2 = st.columns(2)\n                    \n                    def display_standings(col, data, team_color_class):\n                        with col:\n                            st.markdown(f\"<h4 class='card-title' style='text-align: center;'><span class='{team_color_class}'>{data.get('name','N/A')}</span></h4>\", unsafe_allow_html=True)\n                            if data and data.get('ranking') != 'N/A':\n                                st.markdown(f\"<p style='text-align: center;'><strong>Posición:</strong> <span class='data-highlight'>{data['ranking']}</span></p>\", unsafe_allow_html=True)\n                            else:\n                                st.info(\"Datos de clasificación no disponibles.\")\n                    \n                    display_standings(scol1, home_standings, \"home-color\")\n                    display_standings(scol2, away_standings, \"away-color\")\n\n                with st.expander(\"Ver todos los datos extraídos (JSON)\"):\n                    st.json(datos_partido)\n        except Exception as e:\n            st.error(f\"Error inesperado al analizar el partido: {str(e)}\")\n            st.info(\"Por favor, inténtalo de nuevo más tarde o selecciona otro partido.\")

# --- VISTA DE LISTA DE PARTIDOS ---
else:
    st.header("📅 Próximos Partidos para Analizar")
    
    with st.spinner("Buscando próximos partidos..."):
        try:
            matches = get_main_page_matches_cached(limit=50)
            if not matches:
                st.warning("No se encontraron próximos partidos en este momento.")
            else:
                st.success(f"Se encontraron {len(matches)} partidos.")
                
                for match in matches:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([4, 2, 2])
                        with col1:
                            st.markdown(f"##### {match['Local']} vs {match['Visitante']}")
                        with col2:
                            st.text(f"🗓️ {match['Fecha']}")
                            st.text(f"⏰ {match['Hora']}")
                        with col3:
                            if st.button("Analizar Partido", key=f"analizar_{match['ID']}"):
                                st.session_state.selected_match_id = match['ID']
                                st.rerun()

        except Exception as e:
            st.error(f"No se pudieron cargar los partidos: {e}")
            st.info("La web de origen puede estar lenta o inaccesible. Inténtalo de nuevo más tarde.")
