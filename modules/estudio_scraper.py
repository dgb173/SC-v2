
# modules/estudio_scraper.py
import streamlit as st
import time
import re
import math
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- LIBRERÍA DE AUTOMATIZACIÓN ÚNICA: PLAYWRIGHT ---
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Importaciones de módulos locales
from modules.analisis_avanzado import generar_analisis_comparativas_indirectas
from modules.analisis_reciente import analizar_rendimiento_reciente_con_handicap, comparar_lineas_handicap_recientes
from modules.analisis_rivales import analizar_rivales_comunes, analizar_contra_rival_del_rival
from modules.funciones_resumen import generar_resumen_rendimiento_reciente
from modules.funciones_auxiliares import (_calcular_estadisticas_contra_rival, _analizar_over_under, _analizar_ah_cubierto, 
                                        _analizar_desempeno_casa_fuera, _contar_victorias_h2h, _analizar_over_under_h2h, 
                                        _contar_over_h2h, _contar_victorias_h2h_general)
from modules.analisis_rendimiento import generar_analisis_rendimiento_reciente, generar_analisis_h2h_indirecto
from modules.utils import parse_ah_to_number_of, format_ah_as_decimal_string_of, check_handicap_cover, check_goal_line_cover, get_match_details_from_row_of

BASE_URL_OF = "https://live18.nowgoal25.com"
PLAYWRIGHT_TIMEOUT = 25000 # Milisegundos

# --- GESTOR DE NAVEGADOR PLAYWRIGHT (AJUSTADO PARA LA CACHÉ) ---
@st.cache_resource(ttl=3600) # Cachear el browser por 1 hora
async def get_playwright_browser():
    """
    Crea y devuelve una instancia del navegador. La caché de Streamlit
    evitará que se re-ejecute la corutina, devolviendo el objeto browser cacheado.
    """
    st.info("⚙️ Creando una nueva instancia del navegador virtual (Playwright)...")
    try:
        p = await async_playwright().start()
        browser = await p.chromium.launch(headless=True)
        st.success("✅ Instancia del navegador creada.")
        return browser # Usamos return en lugar de yield para evitar el error de corutina
    except Exception as e:
        st.error(f"No se pudo iniciar Playwright: {e}")
        st.stop()

# --- FUNCIÓN PRINCIPAL DE EXTRACCIÓN ---
def obtener_datos_completos_partido(match_id: str):
    return asyncio.run(obtener_datos_completos_partido_async(match_id))

async def obtener_datos_completos_partido_async(match_id: str):
    if not match_id or not match_id.isdigit():
        return {"error": "ID de partido inválido."}

    st.info(f"Iniciando análisis para el partido ID: {match_id}...")
    page = None
    context = None
    try:
        browser = await get_playwright_browser()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        main_page_url = f"{BASE_URL_OF}/match/h2h-{match_id}"
        datos = {"match_id": match_id}

        st.info(f"🌐 Navegando a la página del partido...")
        await page.goto(main_page_url, timeout=PLAYWRIGHT_TIMEOUT, wait_until="domcontentloaded")
        
        await page.wait_for_selector("#table_v1", timeout=PLAYWRIGHT_TIMEOUT)
        st.success("✅ Página principal cargada.")

        st.info("🔍 Ajustando filtros de historial a 'All'...")
        for select_id in ["hSelect_1", "hSelect_2", "hSelect_3"]:
            try:
                await page.select_option(f"#{select_id}", "0", timeout=5000)
            except PlaywrightTimeoutError:
                st.warning(f"No se encontró el filtro '{select_id}', continuando sin él.")
                continue
        
        await page.wait_for_timeout(2000)
        
        html_content = await page.content()
        soup_completo = BeautifulSoup(html_content, "lxml")
        st.success("📄 Contenido de la página parseado.")

        st.info("📊 Extrayendo datos primarios...")
        home_id, away_id, league_id, home_name, away_name, league_name = get_team_league_info_from_script_of(soup_completo)
        if not home_name or not away_name or home_name == "N/A":
             return {"error": "No se pudo extraer la información básica de los equipos."}
        datos.update({"home_name": home_name, "away_name": away_name, "league_name": league_name})

        st.info("🚀 Ejecutando análisis en paralelo...")
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_main_odds = executor.submit(extract_bet365_initial_odds_of, soup_completo)
            future_h2h_data = executor.submit(extract_h2h_data_of, soup_completo, home_name, away_name, None)
            future_rendimiento_local = executor.submit(analizar_rendimiento_reciente_con_handicap, soup_completo, home_name, True)
            future_rendimiento_visitante = executor.submit(analizar_rendimiento_reciente_con_handicap, soup_completo, away_name, False)

            main_match_odds_data = future_main_odds.result()
            h2h_data = future_h2h_data.result()
            rendimiento_local = future_rendimiento_local.result()
            rendimiento_visitante = future_rendimiento_visitante.result()

        st.success("📈 Análisis de datos completado.")

        st.info("✍️ Generando resúmenes...")
        current_ah_line = parse_ah_to_number_of(main_match_odds_data.get('ah_linea_raw', '0'))
        
        comparacion_local = {}
        comparacion_visitante = {}
        if current_ah_line is not None:
            comparacion_local = comparar_lineas_handicap_recientes(soup_completo, home_name, current_ah_line, True)
            comparacion_visitante = comparar_lineas_handicap_recientes(soup_completo, away_name, current_ah_line, False)

        datos["market_analysis_html"] = generar_analisis_completo_mercado(main_match_odds_data, h2h_data, home_name, away_name)
        datos["recent_performance_analysis_html"] = generar_analisis_rendimiento_reciente(home_name, away_name, rendimiento_local, rendimiento_visitante, current_ah_line, comparacion_local, comparacion_visitante)
        
        st.success("🎉 ¡Análisis finalizado con éxito!")
        return datos

    except PlaywrightTimeoutError:
        st.error("Error de Timeout: La página tardó demasiado en responder.")
        return {"error": "Timeout durante el scraping con Playwright."}
    except Exception as e:
        st.error(f"Ocurrió un error inesperado durante el scraping con Playwright: {e}")
        return {"error": f"Error inesperado en el scraper: {e}"}
    finally:
        if page:
            await page.close()
        if context:
            await context.close()


def get_team_league_info_from_script_of(soup):
    script_tag = soup.find("script", string=re.compile(r"var _matchInfo = "))
    if not (script_tag and script_tag.string): return (None,) * 3 + ("N/A",) * 3
    content = script_tag.string
    def find_val(pattern):
        match = re.search(pattern, content)
        return match.group(1).replace("'", "") if match else None
    home_id = find_val(r"hId:\s*parseInt\('(\d+)'\)")
    away_id = find_val(r"gId:\s*parseInt\('(\d+)'\)")
    league_id = find_val(r"sclassId:\s*parseInt\('(\d+)'\)")
    home_name = find_val(r"hName:\s*'([^']*)'") or "N/A"
    away_name = find_val(r"gName:\s*'([^']*)'") or "N/A"
    league_name = find_val(r"lName:\s*'([^']*)'") or "N/A"
    return home_id, away_id, league_id, home_name, away_name, league_name

def extract_bet365_initial_odds_of(soup):
    odds_info = {
        "ah_home_cuota": "N/A", "ah_linea_raw": "N/A", "ah_away_cuota": "N/A",
        "goals_over_cuota": "N/A", "goals_linea_raw": "N/A", "goals_under_cuota": "N/A"
    }
    if not soup: return odds_info
    bet365_row = soup.select_one("tr#tr_o_1_8[name='earlyOdds'], tr#tr_o_1_31[name='earlyOdds']")
    if not bet365_row: return odds_info
    tds = bet365_row.find_all("td")
    if len(tds) >= 11:
        odds_info["ah_home_cuota"] = tds[2].get("data-o", tds[2].text).strip()
        odds_info["ah_linea_raw"] = tds[3].get("data-o", tds[3].text).strip()
        odds_info["ah_away_cuota"] = tds[4].get("data-o", tds[4].text).strip()
        odds_info["goals_over_cuota"] = tds[8].get("data-o", tds[8].text).strip()
        odds_info["goals_linea_raw"] = tds[9].get("data-o", tds[9].text).strip()
        odds_info["goals_under_cuota"] = tds[10].get("data-o", tds[10].text).strip()
    return odds_info

def _parse_date_ddmmyyyy(d: str) -> tuple:
    m = re.search(r'(\d{2})-(\d{2})-(\d{4})', d or '')
    return (int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else (1900, 1, 1)

def extract_h2h_data_of(soup, home_name, away_name, league_id=None):
    results = {'ah1': '-', 'res1': '?:?', 'res1_raw': '?-?', 'match1_id': None, 'ah6': '-', 'res6': '?:?', 'res6_raw': '?-?', 'match6_id': None, 'h2h_gen_home': "Local (H2H Gen)", 'h2h_gen_away': "Visitante (H2H Gen)"}
    if not soup or not home_name or not away_name or not (h2h_table := soup.find("table", id="table_v3")): return results
    all_matches = []
    for r in h2h_table.find_all("tr", id=re.compile(r"tr3_\d+")):
        if (d := get_match_details_from_row_of(r, score_class_selector='fscore_3', source_table_type='h2h')):
            if not league_id or (d.get('league_id_hist') and d.get('league_id_hist') == str(league_id)):
                all_matches.append(d)
    if not all_matches: return results
    all_matches.sort(key=lambda x: _parse_date_ddmmyyyy(x.get('date', '')), reverse=True)
    most_recent = all_matches[0]
    results.update({'ah6': most_recent.get('ahLine', '-'), 'res6': most_recent.get('score', '?:?'), 'res6_raw': most_recent.get('score_raw', '?-?'), 'match6_id': most_recent.get('matchIndex'), 'h2h_gen_home': most_recent.get('home'), 'h2h_gen_away': most_recent.get('away')})
    for d in all_matches:
        if d['home'].lower() == home_name.lower() and d['away'].lower() == away_name.lower():
            results.update({'ah1': d.get('ahLine', '-'), 'res1': d.get('score', '?:?'), 'res1_raw': d.get('score_raw', '?-?'), 'match1_id': d.get('matchIndex')})
            break
    return results

def _analizar_precedente_handicap(precedente_data, ah_actual_num, favorito_actual_name, main_home_team_name):
    return ""

def generar_analisis_completo_mercado(main_odds, h2h_data, home_name, away_name):
    return ""
