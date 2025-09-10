# app.py - Servidor web principal (Flask)
from flask import Flask, render_template, abort, request
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import datetime

# ¡Importante! Importa tu nuevo módulo de scraping
from modules.estudio_scraper import obtener_datos_completos_partido, format_ah_as_decimal_string_of

app = Flask(__name__)

# --- Mantén tu lógica para la página principal ---
URL_NOWGOAL = "https://live20.nowgoal25.com/"

def parse_main_page_matches(html_content, limit=20, offset=0):
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

        # Filtro robusto: Ignorar si no hay datos de handicap o goles
        if not handicap or handicap == "N/A" or not goal_line or goal_line == "N/A":
            continue

        upcoming_matches.append({
            "id": match_id,
            "time": match_time.strftime('%Y-%m-%d %H:%M'),
            "home_team": home_team_tag.text.strip() if home_team_tag else "N/A",
            "away_team": away_team_tag.text.strip() if away_team_tag else "N/A",
            "handicap": handicap,
            "goal_line": goal_line
        })

    upcoming_matches.sort(key=lambda x: x['time'])
    return upcoming_matches[offset:offset+limit]

async def get_main_page_matches_async(limit=20, offset=0):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(URL_NOWGOAL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(5000)
            html_content = await page.content()
            return parse_main_page_matches(html_content, limit, offset)
        finally:
            await browser.close()

@app.route('/')
def index():
    try:
        print("Recibida petición. Ejecutando scraper de partidos...")
        matches = asyncio.run(get_main_page_matches_async())
        print(f"Scraper finalizado. {len(matches)} partidos encontrados.")
        return render_template('index.html', matches=matches)
    except Exception as e:
        print(f"ERROR en la ruta principal: {e}")
        return render_template('index.html', matches=[], error=f"No se pudieron cargar los partidos: {e}")

@app.route('/api/matches')
def api_matches():
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 5))
        matches = asyncio.run(get_main_page_matches_async(limit, offset))
        return {'matches': matches}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/proximos')
def proximos():
    try:
        print("Recibida petición. Ejecutando scraper de partidos...")
        matches = asyncio.run(get_main_page_matches_async(25))
        print(f"Scraper finalizado. {len(matches)} partidos encontrados.")
        return render_template('index.html', matches=matches)
    except Exception as e:
        print(f"ERROR en la ruta principal: {e}")
        return render_template('index.html', matches=[], error=f"No se pudieron cargar los partidos: {e}")

# --- NUEVA RUTA PARA MOSTRAR EL ESTUDIO DETALLADO ---
@app.route('/estudio/<string:match_id>')
def mostrar_estudio(match_id):
    """
    Esta ruta se activa cuando un usuario visita /estudio/ID_DEL_PARTIDO.
    """
    print(f"Recibida petición para el estudio del partido ID: {match_id}")
    
    # Llama a la función principal de tu módulo de scraping
    datos_partido = obtener_datos_completos_partido(match_id)
    
    if not datos_partido or "error" in datos_partido:
        # Si hay un error, puedes mostrar una página de error
        print(f"Error al obtener datos para {match_id}: {datos_partido.get('error')}")
        abort(500, description=datos_partido.get('error', 'Error desconocido'))

    # Si todo va bien, renderiza la plantilla HTML pasándole los datos
    print(f"Datos obtenidos para {datos_partido['home_name']} vs {datos_partido['away_name']}. Renderizando plantilla...")
    return render_template('estudio.html', data=datos_partido, format_ah=format_ah_as_decimal_string_of)

# --- NUEVA RUTA PARA ANALIZAR PARTIDOS FINALIZADOS ---
@app.route('/analizar_partido', methods=['GET', 'POST'])
def analizar_partido():
    """
    Ruta para analizar partidos finalizados por ID.
    """
    if request.method == 'POST':
        match_id = request.form.get('match_id')
        if match_id:
            print(f"Recibida petición para analizar partido finalizado ID: {match_id}")
            
            # Llama a la función principal de tu módulo de scraping
            datos_partido = obtener_datos_completos_partido(match_id)
            
            if not datos_partido or "error" in datos_partido:
                # Si hay un error, mostrarlo en la página
                print(f"Error al obtener datos para {match_id}: {datos_partido.get('error')}")
                return render_template('analizar_partido.html', error=datos_partido.get('error', 'Error desconocido'))
            
            # Si todo va bien, renderiza la plantilla HTML pasándole los datos
            print(f"Datos obtenidos para {datos_partido['home_name']} vs {datos_partido['away_name']}. Renderizando plantilla...")
            return render_template('estudio.html', data=datos_partido, format_ah=format_ah_as_decimal_string_of)
        else:
            return render_template('analizar_partido.html', error="Por favor, introduce un ID de partido válido.")
    
    # Si es GET, mostrar el formulario
    return render_template('analizar_partido.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True es útil para desarrollar
