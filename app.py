import streamlit as st
import asyncio
import pandas as pd
import subprocess
import sys
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import datetime

# --- Función para asegurar que los navegadores de Playwright están instalados ---
def ensure_playwright_browsers_installed():
    """Verifica y ejecuta 'playwright install' si es necesario."""
    # Usamos st.cache_resource para ejecutar esto solo una vez por sesión.
    @st.cache_resource
    def install_browsers():
        st.info("Verificando instalación de navegadores para Playwright...")
        try:
            # Usamos sys.executable para asegurar que usamos el python correcto
            subprocess.run([sys.executable, "-m", "playwright", "install"], check=True, capture_output=True)
            st.success("✅ Navegadores de Playwright listos.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            st.error(f"No se pudieron instalar los navegadores de Playwright: {e}")
            st.error("La aplicación no puede continuar sin los navegadores. Por favor, revisa los logs.")
            st.stop()
            return False
    install_browsers()

# --- Ejecutar la instalación de navegadores al inicio de la app ---
ensure_playwright_browsers_installed()

# Importar las funciones de scraping y análisis (después de la instalación)
from modules.estudio_scraper import obtener_datos_completos_partido

# --- Configuración de la página de Streamlit ---
st.set_page_config(
    page_title="Análisis de Partidos",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funciones de Scraping (Cacheadas para rendimiento) ---
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
            "Handicap": handicap,
            "Línea de Gol": goal_line
        })

    upcoming_matches.sort(key=lambda x: x['Hora'])
    return upcoming_matches[:limit]

@st.cache_data(ttl=600) # Cache por 10 minutos
def get_main_page_matches_cached(limit=50):
    """Versión asíncrona envuelta para Streamlit con caché."""
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

@st.cache_data(ttl=3600) # Cache por 1 hora para análisis de partidos
def obtener_datos_completos_partido_cached(match_id):
    """Función wrapper para cachear los resultados del scraper de estudio."""
    return obtener_datos_completos_partido(match_id)

# --- Interfaz de Usuario ---
st.title("⚽ Dashboard de Análisis de Partidos")

st.sidebar.title("Navegación")
opcion = st.sidebar.radio(
    "Selecciona una vista:",
    ("Próximos Partidos", "Analizar Partido por ID")
)

if opcion == "Próximos Partidos":
    st.header("📅 Próximos Partidos")
    if st.button("Buscar Partidos"):
        with st.spinner("Buscando próximos partidos... Esto puede tardar un momento."):
            try:
                matches = get_main_page_matches_cached(limit=50)
                if matches:
                    df = pd.DataFrame(matches)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.success(f"Se encontraron {len(matches)} partidos.")
                else:
                    st.warning("No se encontraron próximos partidos en este momento.")
            except Exception as e:
                st.error(f"No se pudieron cargar los partidos: {e}")
                st.info("Esto puede deberse a un problema con la web de origen o a un timeout. Inténtalo de nuevo más tarde.")

elif opcion == "Analizar Partido por ID":
    st.header("🔍 Analizar Partido por ID")
    
    match_id_input = st.text_input("Introduce el ID del partido:", placeholder="Ej: 2490123")
    
    if st.button("Analizar Partido"):
        if match_id_input and match_id_input.isdigit():
            datos_partido = obtener_datos_completos_partido_cached(match_id_input)
            
            if not datos_partido or "error" in datos_partido:
                st.error(f"Error al obtener datos para el partido {match_id_input}: {datos_partido.get('error', 'Error desconocido')}")
            else:
                st.header(f"Análisis para: {datos_partido['home_name']} vs {datos_partido['away_name']}")
                
                if "market_analysis_html" in datos_partido:
                    st.markdown(datos_partido["market_analysis_html"], unsafe_allow_html=True)

                if "recent_performance_analysis_html" in datos_partido:
                    st.markdown(datos_partido["recent_performance_analysis_html"], unsafe_allow_html=True)
                
                with st.expander("Ver todos los datos extraídos (JSON)"):
                    st.json(datos_partido)
        else:
            st.warning("Por favor, introduce un ID de partido numérico válido.")

st.sidebar.markdown("---")
st.sidebar.info("Aplicación refactorizada por Gemini para mayor estabilidad.")