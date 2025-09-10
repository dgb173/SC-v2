import streamlit as st
import asyncio
import pandas as pd
import subprocess
import sys
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import datetime

# --- Dependencias del Proyecto ---
from modules.estudio_scraper import obtener_datos_completos_partido

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Análisis de Partidos",
    page_icon="⚽",
    layout="wide"
)

# --- Instalación de Dependencias de Navegador (se ejecuta solo una vez) ---
@st.cache_resource
def ensure_playwright_browsers_installed():
    st.info("Verificando instalación de navegadores para Playwright...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True, capture_output=True)
        st.success("✅ Navegadores de Playwright listos.")
    except Exception as e:
        st.error(f"No se pudieron instalar los navegadores de Playwright: {e}")
        st.stop()

ensure_playwright_browsers_installed()

# --- Funciones de Scraping (Cacheadas) ---
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
    async def get_matches():
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
    return asyncio.run(get_matches())

# --- Lógica Principal de la App ---
st.title("⚽ Dashboard de Análisis de Partidos")

if 'selected_match_id' not in st.session_state:
    st.session_state.selected_match_id = None

# --- VISTA DE ANÁLISIS DE PARTIDO ---
if st.session_state.selected_match_id:
    match_id = st.session_state.selected_match_id
    
    if st.button("⬅️ Volver a la lista de partidos"):
        st.session_state.selected_match_id = None
        st.rerun()

    # Ya no usamos una función cacheada aquí, llamamos directamente a la principal
    datos_partido = obtener_datos_completos_partido(match_id)
    
    if not datos_partido or "error" in datos_partido:
        st.error(f"Error al obtener datos para el partido {match_id}: {datos_partido.get('error', 'Error desconocido')}")
    else:
        st.header(f"Análisis para: {datos_partido['home_name']} vs {datos_partido['away_name']}")
        
        if "market_analysis_html" in datos_partido:
            st.markdown(datos_partido["market_analysis_html"], unsafe_allow_html=True)

        if "recent_performance_analysis_html" in datos_partido:
            st.markdown(datos_partido["recent_performance_analysis_html"], unsafe_allow_html=True)
        
        with st.expander("Ver todos los datos extraídos (JSON)"):
            st.json(datos_partido)

# --- VISTA DE LISTA DE PARTIDOS (VISTA PRINCIPAL) ---
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