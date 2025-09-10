
# modules/estudio_scraper.py
import streamlit as st
import time
import re
import math
import pandas as pd
import tempfile
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Selenium imports for Streamlit Cloud
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

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
SELENIUM_TIMEOUT_SECONDS_OF = 15
PLACEHOLDER_NODATA = "*(No disponible)*"

# --- FUNCIÓN DE CONFIGURACIÓN DEL DRIVER (NUEVA ESTRATEGIA) ---
def setup_selenium_driver_for_streamlit():
    """Configura y devuelve un driver de Selenium compatible con Streamlit Cloud."""
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    
    # --- CAMBIOS CLAVE PARA ESTABILIDAD EN CONTENEDORES ---
    options.add_argument("--disable-dev-shm-usage") # Supera problemas de memoria limitada.
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument('--single-process') # Ejecuta Chrome como un solo proceso.
    options.add_argument("--disable-blink-features=AutomationControlled")
    # No especificamos --user-data-dir para dejar que Chrome maneje su perfil efímero.
    
    return webdriver.Chrome(options=options)

# --- FUNCIÓN PRINCIPAL DE EXTRACCIÓN (Sin cambios, usa la función de setup modificada) ---
def obtener_datos_completos_partido(match_id: str):
    if not match_id or not match_id.isdigit():
        return {"error": "ID de partido inválido."}

    st.info(f"Iniciando análisis para el partido ID: {match_id}...")
    driver = None
    
    try:
        st.info("⚙️ Configurando el navegador virtual...")
        driver = setup_selenium_driver_for_streamlit()
        main_page_url = f"{BASE_URL_OF}/match/h2h-{match_id}"
        datos = {"match_id": match_id}

        st.info(f"🌐 Navegando a la página del partido...")
        driver.get(main_page_url)
        
        WebDriverWait(driver, SELENIUM_TIMEOUT_SECONDS_OF).until(
            EC.presence_of_element_located((By.ID, "table_v1"))
        )
        st.success("✅ Página principal cargada.")

        st.info("🔍 Ajustando filtros de historial a 'All'...")
        for select_id in ["hSelect_1", "hSelect_2", "hSelect_3"]:
            try:
                select_element = Select(WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, select_id))))
                select_element.select_by_value("0")
            except TimeoutException:
                st.warning(f"No se encontró el filtro '{select_id}', continuando sin él.")
                continue
        
        time.sleep(2)
        soup_completo = BeautifulSoup(driver.page_source, "lxml")
        st.success("📄 Contenido de la página parseado.")

        st.info("📊 Extrayendo datos primarios (equipos, liga...).")
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

        st.info("✍️ Generando resúmenes y notas del analista...")
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

    except TimeoutException:
        st.error("Error de Timeout: La página tardó demasiado en responder.")
        return {"error": "Timeout durante el scraping."}
    except WebDriverException as e:
        st.error(f"Error de WebDriver: Hubo un problema con el navegador virtual. Mensaje: {e}")
        return {"error": f"Error de Selenium/WebDriver: {e}"}
    except Exception as e:
        st.error(f"Ocurrió un error inesperado durante el scraping: {e}")
        return {"error": f"Error inesperado en el scraper: {e}"}
    finally:
        if driver:
            driver.quit()
            st.info("✅ Navegador virtual cerrado.")

# ... (El resto de funciones auxiliares permanecen igual)

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
    res_raw = precedente_data.get('res_raw')
    ah_raw = precedente_data.get('ah_raw')
    home_team_precedente = precedente_data.get('home')
    away_team_precedente = precedente_data.get('away')
    if not all([res_raw, res_raw != '?-?', ah_raw, ah_raw != '-']):
        return "<li><span class='ah-value'>Hándicap:</span> No hay datos suficientes en este precedente.</li>"
    ah_historico_num = parse_ah_to_number_of(ah_raw)
    comparativa_texto = ""
    if ah_historico_num is not None and ah_actual_num is not None:
        formatted_ah_historico = format_ah_as_decimal_string_of(ah_raw)
        formatted_ah_actual = format_ah_as_decimal_string_of(str(ah_actual_num))
        line_movement_str = f"{formatted_ah_historico} → {formatted_ah_actual}"
        favorito_historico_name = None
        if ah_historico_num > 0:
            favorito_historico_name = home_team_precedente
        elif ah_historico_num < 0:
            favorito_historico_name = away_team_precedente
        if favorito_actual_name.lower() == (favorito_historico_name or "").lower():
            if abs(ah_actual_num) > abs(ah_historico_num):
                comparativa_texto = f"El mercado considera a este equipo <strong>más favorito</strong> que en el precedente (movimiento: <strong style='color: green; font-size:1.2em;'>{line_movement_str}</strong>). "
            elif abs(ah_actual_num) < abs(ah_historico_num):
                comparativa_texto = f"El mercado considera a este equipo <strong>menos favorito</strong> que en el precedente (movimiento: <strong style='color: orange; font-size:1.2em;'>{line_movement_str}</strong>). "
            else:
                comparativa_texto = f"El mercado mantiene una línea de <strong>magnitud idéntica</strong> a la del precedente (<strong>{formatted_ah_historico}</strong>). "
        else:
            if favorito_historico_name and favorito_actual_name != "Ninguno (línea en 0)":
                comparativa_texto = f"Ha habido un <strong>cambio total de favoritismo</strong>. En el precedente el favorito era '{favorito_historico_name}' (movimiento: <strong style='color: red; font-size:1.2em;'>{line_movement_str}</strong>). "
            elif not favorito_historico_name:
                comparativa_texto = f"El mercado establece un favorito claro, considerándolo <strong>mucho más favorito</strong> que en el precedente (movimiento: <strong style='color: green; font-size:1.2em;'>{line_movement_str}</strong>). "
            else: # favorito_actual_name es "Ninguno (línea en 0)"
                comparativa_texto = f"El mercado <strong>ha eliminado al favorito</strong> ('{favorito_historico_name}') que existía en el precedente (movimiento: <strong style='color: orange; font-size:1.2em;'>{line_movement_str}</strong>). "
    else:
        comparativa_texto = f"No se pudo realizar una comparación detallada (línea histórica: <strong>{format_ah_as_decimal_string_of(ah_raw)}</strong>). "
    resultado_cover, cubierto = check_handicap_cover(res_raw, ah_actual_num, favorito_actual_name, home_team_precedente, away_team_precedente, main_home_team_name)
    if cubierto is True:
        cover_html = f"<span style='color: green; font-weight: bold;'>CUBIERTO ✅</span>"
    elif cubierto is False:
        cover_html = f"<span style='color: red; font-weight: bold;'>NO CUBIERTO ❌</span>"
    else: # PUSH o indeterminado
        cover_html = f"<span style='color: #6c757d; font-weight: bold;'>{resultado_cover.upper()} 🤔</span>"
    return f"<li><span class='ah-value'>Hándicap:</span> {comparativa_texto}Con el resultado ({res_raw.replace('-', ':')}), la línea actual se habría considerado {cover_html}.</li>"

def generar_analisis_completo_mercado(main_odds, h2h_data, home_name, away_name):
    ah_actual_str = format_ah_as_decimal_string_of(main_odds.get('ah_linea_raw', '-'))
    ah_actual_num = parse_ah_to_number_of(ah_actual_str)
    goles_actual_num = parse_ah_to_number_of(main_odds.get('goals_linea_raw', '-'))
    if ah_actual_num is None or goles_actual_num is None: return ""
    favorito_name, favorito_html = "Ninguno (línea en 0)", "Ninguno (línea en 0)"
    if ah_actual_num < 0:
        favorito_name, favorito_html = away_name, f"<span class='away-color'>{away_name}</span>"
    elif ah_actual_num > 0:
        favorito_name, favorito_html = home_name, f"<span class='home-color'>{home_name}</span>"
    titulo_html = f"<p style='margin-bottom: 12px;'><strong>📊 Análisis de Mercado vs. Histórico H2H</strong><br><span style='font-style: italic; font-size: 0.9em;'>Líneas actuales: AH {ah_actual_str} / Goles {goles_actual_num} | Favorito: {favorito_html}</span></p>"
    precedente_estadio = {
        'res_raw': h2h_data.get('res1_raw'), 'ah_raw': h2h_data.get('ah1'),
        'home': home_name, 'away': away_name, 'match_id': h2h_data.get('match1_id')
    }
    sintesis_ah_estadio = _analizar_precedente_handicap(precedente_estadio, ah_actual_num, favorito_name, home_name)
    
    analisis_estadio_html = (
        f"<div style='margin-bottom: 10px;'>"
        f"  <strong style='font-size: 1.05em;'>🏟️ Análisis del Precedente en Este Estadio</strong>"
        f"  <ul style='margin: 5px 0 0 20px; padding-left: 0;'>{sintesis_ah_estadio}</ul>"
        f"</div>"
    )
    precedente_general_id = h2h_data.get('match6_id')
    if precedente_estadio['match_id'] and precedente_general_id and precedente_estadio['match_id'] == precedente_general_id:
        analisis_general_html = (
            "<div style='margin-top: 10px;'>"
            "  <strong>✈️ Análisis del H2H General Más Reciente</strong>"
            "  <p style='margin: 5px 0 0 20px; font-style: italic; font-size: 0.9em;'>"
            "    El precedente es el mismo partido analizado arriba."
            "  </p>"
            "</div>"
        )
    else:
        precedente_general = {
            'res_raw': h2h_data.get('res6_raw'),
            'ah_raw': h2h_data.get('ah6'),
            'home': h2h_data.get('h2h_gen_home'),
            'away': h2h_data.get('h2h_gen_away'),
            'match_id': precedente_general_id
        }
        sintesis_ah_general = _analizar_precedente_handicap(precedente_general, ah_actual_num, favorito_name, home_name)
        analisis_general_html = (
            f"<div>"
            f"  <strong style='font-size: 1.05em;'>✈️ Análisis del H2H General Más Reciente</strong>"
            f"  <ul style='margin: 5px 0 0 20px; padding-left: 0;'>{sintesis_ah_general}</ul>"
            f"</div>"
        )
    return f'''
    <div style="border-left: 4px solid #1E90FF; padding: 12px 15px; margin-top: 15px; background-color: #f0f2f6; border-radius: 5px; font-size: 0.95em;">
        {titulo_html}
        {analisis_estadio_html}
        {analisis_general_html}
    </div>
    '''
