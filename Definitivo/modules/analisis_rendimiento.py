# modules/analisis_rendimiento.py
import re
from bs4 import BeautifulSoup
from modules.utils import parse_ah_to_number_of, format_ah_as_decimal_string_of, check_handicap_cover, check_goal_line_cover

def generar_analisis_rendimiento_reciente(home_name, away_name, rendimiento_local, rendimiento_visitante, current_ah_line, comparacion_local, comparacion_visitante):
    """
    Genera un análisis detallado del rendimiento reciente de ambos equipos comparado con su histórico.
    
    Args:
        home_name: Nombre del equipo local
        away_name: Nombre del equipo visitante
        rendimiento_local: Datos de rendimiento reciente del equipo local
        rendimiento_visitante: Datos de rendimiento reciente del equipo visitante
        current_ah_line: Línea de handicap actual
        comparacion_local: Comparación de líneas para el equipo local
        comparacion_visitante: Comparación de líneas para el equipo visitante
    
    Returns:
        str: HTML con el análisis de rendimiento reciente
    """
    if not rendimiento_local or not rendimiento_visitante:
        return ""
    
    # Extraer estadísticas del rendimiento reciente
    covered_local = rendimiento_local.get('covered', 0)
    not_covered_local = rendimiento_local.get('not_covered', 0)
    push_local = rendimiento_local.get('push', 0)
    total_local = rendimiento_local.get('total_matches', 0)
    
    covered_away = rendimiento_visitante.get('covered', 0)
    not_covered_away = rendimiento_visitante.get('not_covered', 0)
    push_away = rendimiento_visitante.get('push', 0)
    total_away = rendimiento_visitante.get('total_matches', 0)
    
    # Calcular porcentajes
    pct_covered_local = (covered_local / total_local * 100) if total_local > 0 else 0
    pct_covered_away = (covered_away / total_away * 100) if total_away > 0 else 0
    
    # Analizar tendencias de línea
    trend_local = comparacion_local.get('trend', '') if comparacion_local else ''
    trend_away = comparacion_visitante.get('trend', '') if comparacion_visitante else ''
    
    # Determinar favorito según la línea de handicap
    favorito_name = "Ninguno (línea en 0)"
    if current_ah_line is not None:
        if current_ah_line < 0:
            favorito_name = away_name
        elif current_ah_line > 0:
            favorito_name = home_name
    
    # Generar HTML
    titulo_html = (
        f"<p style='margin-bottom: 12px;'><strong>📊 Análisis de Rendimiento Reciente vs. Histórico</strong><br>"
        f"<span style='font-style: italic; font-size: 0.9em;'>Favorito: <span class='home-color'>{home_name}</span> vs <span class='away-color'>{away_name}</span></span></p>"
    )
    
    # Análisis del equipo local
    analisis_local_html = _generar_analisis_equipo_rendimiento(
        home_name, covered_local, not_covered_local, push_local, total_local, pct_covered_local, trend_local, True
    )
    
    # Análisis del equipo visitante
    analisis_away_html = _generar_analisis_equipo_rendimiento(
        away_name, covered_away, not_covered_away, push_away, total_away, pct_covered_local, trend_away, False
    )
    
    # Combinar análisis
    analisis_combinado_html = (
        f"<div style='margin-bottom: 10px;'>"
        f"  <strong style='font-size: 1.05em;'>🏠 Análisis del Rendimiento Reciente de <span class='home-color'>{home_name}</span></strong>"
        f"  <ul style='margin: 5px 0 0 20px; padding-left: 0;'>{analisis_local_html}</ul>"
        f"</div>"
        f"<div>"
        f"  <strong style='font-size: 1.05em;'>✈️ Análisis del Rendimiento Reciente de <span class='away-color'>{away_name}</span></strong>"
        f"  <ul style='margin: 5px 0 0 20px; padding-left: 0;'>{analisis_away_html}</ul>"
        f"</div>"
    )
    
    return f'''
    <div style="border-left: 4px solid #1E90FF; padding: 12px 15px; margin-top: 15px; background-color: #f0f2f6; border-radius: 5px; font-size: 0.95em;">
        {titulo_html}
        {analisis_combinado_html}
    </div>
    '''

def _generar_analisis_equipo_rendimiento(team_name, covered, not_covered, push, total, pct_covered, trend, is_home):
    """
    Genera el análisis detallado para un equipo específico.
    
    Args:
        team_name: Nombre del equipo
        covered: Número de handicaps cubiertos
        not_covered: Número de handicaps no cubiertos
        push: Número de pushes
        total: Total de partidos
        pct_covered: Porcentaje de handicaps cubiertos
        trend: Tendencia de la línea
        is_home: Si es equipo local
    
    Returns:
        str: HTML con el análisis del equipo
    """
    if total == 0:
        return "<li>No hay datos suficientes de rendimiento reciente.</li>"
    
    # Interpretar tendencia
    if "SUBIÓ" in trend:
        interpretacion_tendencia = f"El mercado considera a este equipo <strong>más fuerte</strong> que en partidos recientes (movimiento: <strong style='color: green; font-size:1.1em;'>{trend}</strong>)."
    elif "BAJÓ" in trend:
        interpretacion_tendencia = f"El mercado considera a este equipo <strong>menos fuerte</strong> que en partidos recientes (movimiento: <strong style='color: red; font-size:1.1em;'>{trend}</strong>)."
    elif "subió" in trend:
        interpretacion_tendencia = f"El mercado considera a este equipo <strong>ligeramente más fuerte</strong> que en partidos recientes (movimiento: <strong style='color: green; font-size:1.1em;'>{trend}</strong>)."
    elif "bajó" in trend:
        interpretacion_tendencia = f"El mercado considera a este equipo <strong>ligeramente menos fuerte</strong> que en partidos recientes (movimiento: <strong style='color: orange; font-size:1.1em;'>{trend}</strong>)."
    else:
        interpretacion_tendencia = f"La línea se mantiene <strong>estable</strong> comparada con partidos recientes."
    
    # Análisis de cobertura
    if pct_covered >= 70:
        analisis_cobertura = f"Este equipo tiene un <strong>excelente</strong> récord reciente cubriendo handicaps ({covered}/{total} partidos - {pct_covered:.1f}%)."
    elif pct_covered >= 60:
        analisis_cobertura = f"Este equipo tiene un <strong>buen</strong> récord reciente cubriendo handicaps ({covered}/{total} partidos - {pct_covered:.1f}%)."
    elif pct_covered >= 50:
        analisis_cobertura = f"Este equipo tiene un récord <strong>medio</strong> cubriendo handicaps ({covered}/{total} partidos - {pct_covered:.1f}%)."
    else:
        analisis_cobertura = f"Este equipo tiene un récord <strong>debil</strong> reciente cubriendo handicaps ({covered}/{total} partidos - {pct_covered:.1f}%)."
    
    # Formatear resultado
    if covered > not_covered:
        resultado_html = f"<span style='color: green; font-weight: bold;'>FAVORABLE ✅</span>"
    elif not_covered > covered:
        resultado_html = f"<span style='color: red; font-weight: bold;'>DESFAVORABLE ❌</span>"
    else:
        resultado_html = f"<span style='color: #6c757d; font-weight: bold;'>NEUTRO 🤔</span>"
    
    return f"""
        <li><span class='ah-value'>Tendencia:</span> {interpretacion_tendencia}</li>
        <li><span class='ah-value'>Cobertura Reciente:</span> {analisis_cobertura} Con el rendimiento reciente, se habría considerado {resultado_html}.</li>
        <li><span class='ah-value'>Detalle:</span> <strong>{covered}</strong> cubiertos | <strong>{not_covered}</strong> no cubiertos | <strong>{push}</strong> push</li>
    """

def generar_analisis_h2h_indirecto(soup, home_name, away_name, rival_home_rival, rival_away_rival, analisis_contra_rival):
    """
    Genera un análisis H2H indirecto basado en rivales comunes.
    
    Args:
        soup: BeautifulSoup object con el contenido de la página
        home_name: Nombre del equipo local
        away_name: Nombre del equipo visitante
        rival_home_rival: Rival del equipo local
        rival_away_rival: Rival del equipo visitante
        analisis_contra_rival: Análisis contra rival del rival
    
    Returns:
        str: HTML con el análisis H2H indirecto
    """
    if not analisis_contra_rival:
        return ""
    
    # Extraer información de los rivales
    matches_a_vs_rival = analisis_contra_rival.get('matches_a_vs_rival_b_rival', [])
    matches_b_vs_rival = analisis_contra_rival.get('matches_b_vs_rival_a_rival', [])
    
    if not matches_a_vs_rival and not matches_b_vs_rival:
        return ""
    
    # Analizar rendimiento contra rivales
    victorias_a = _contar_victorias(matches_a_vs_rival, home_name)
    victorias_b = _contar_victorias(matches_b_vs_rival, away_name)
    total_a = len(matches_a_vs_rival)
    total_b = len(matches_b_vs_rival)
    
    # Generar HTML
    titulo_html = (
        f"<p style='margin-bottom: 12px;'><strong>🔄 Análisis H2H Indirecto</strong><br>"
        f"<span style='font-style: italic; font-size: 0.9em;'><span class='home-color'>{home_name}</span> vs rival de <span class='away-color'>{away_name}</span> | <span class='away-color'>{away_name}</span> vs rival de <span class='home-color'>{home_name}</span></span></p>"
    )
    
    # Análisis equipo local
    analisis_local_html = _generar_analisis_h2h_equipo(
        home_name, victorias_a, total_a, rival_away_rival, matches_a_vs_rival
    )
    
    # Análisis equipo visitante
    analisis_visitante_html = _generar_analisis_h2h_equipo(
        away_name, victorias_b, total_b, rival_home_rival, matches_b_vs_rival
    )
    
    # Combinar análisis
    analisis_combinado_html = (
        f"<div style='margin-bottom: 10px;'>"
        f"  <strong style='font-size: 1.05em;'>🏠 {home_name} vs {rival_away_rival}</strong>"
        f"  <ul style='margin: 5px 0 0 20px; padding-left: 0;'>{analisis_local_html}</ul>"
        f"</div>"
        f"<div>"
        f"  <strong style='font-size: 1.05em;'>✈️ {away_name} vs {rival_home_rival}</strong>"
        f"  <ul style='margin: 5px 0 0 20px; padding-left: 0;'>{analisis_visitante_html}</ul>"
        f"</div>"
    )
    
    return f'''
    <div style="border-left: 4px solid #FF6B35; padding: 12px 15px; margin-top: 15px; background-color: #fff0e6; border-radius: 5px; font-size: 0.95em;">
        {titulo_html}
        {analisis_combinado_html}
    </div>
    '''

def _contar_victorias(matches, equipo):
    """Cuenta las victorias de un equipo en una lista de partidos."""
    victorias = 0
    for match in matches:
        if '-' in match.get('score_raw', '?-?'):
            try:
                goles_local, goles_visitante = map(int, match['score_raw'].split('-'))
                if match['home_team'].lower() == equipo.lower() and goles_local > goles_visitante:
                    victorias += 1
                elif match['away_team'].lower() == equipo.lower() and goles_visitante > goles_local:
                    victorias += 1
            except (ValueError, TypeError):
                continue
    return victorias

def _generar_analisis_h2h_equipo(team_name, victorias, total, rival_name, matches):
    """
    Genera el análisis H2H para un equipo específico.
    
    Args:
        team_name: Nombre del equipo
        victorias: Número de victorias
        total: Total de partidos
        rival_name: Nombre del rival
        matches: Lista de partidos
    
    Returns:
        str: HTML con el análisis
    """
    if total == 0:
        return f"<li>No hay datos de enfrentamientos contra {rival_name}.</li>"
    
    pct_victorias = (victorias / total) * 100
    
    # Interpretar rendimiento
    if pct_victorias >= 70:
        interpretacion = f"<strong>excelente</strong> historial contra {rival_name} ({victorias}/{total} victorias - {pct_victorias:.1f}%)."
    elif pct_victorias >= 60:
        interpretacion = f"<strong>buen</strong> historial contra {rival_name} ({victorias}/{total} victorias - {pct_victorias:.1f}%)."
    elif pct_victorias >= 50:
        interpretacion = f"historial <strong>medio</strong> contra {rival_name} ({victorias}/{total} victorias - {pct_victorias:.1f}%)."
    else:
        interpretacion = f"historial <strong>débil</strong> contra {rival_name} ({victorias}/{total} victorias - {pct_victorias:.1f}%)."
    
    # Formatear resultado
    if pct_victorias > 60:
        resultado_html = f"<span style='color: green; font-weight: bold;'>FAVORABLE ✅</span>"
    elif pct_victorias < 40:
        resultado_html = f"<span style='color: red; font-weight: bold;'>DESFAVORABLE ❌</span>"
    else:
        resultado_html = f"<span style='color: #6c757d; font-weight: bold;'>NEUTRO 🤔</span>"
    
    # Detalles de partidos recientes
    detalles_html = ""
    if matches:
        detalles_html = "<li><span class='ah-value'>Partidos recientes:</span><ul>"
        for match in matches[:3]:  # Limitar a 3 partidos más recientes
            score = match.get('score', '?:?').replace('-', ':')
            ah_line = match.get('ah_line', '-')
            detalles_html += f"<li>{match.get('home_team', 'N/A')} vs {match.get('away_team', 'N/A')} - <span class='score-value'>{score}</span> - AH: <span class='ah-value'>{ah_line}</span></li>"
        detalles_html += "</ul></li>"
    
    return f"""
        <li><span class='ah-value'>Rendimiento:</span> {team_name} tiene un {interpretacion} Se habría considerado {resultado_html}.</li>
        {detalles_html}
    """