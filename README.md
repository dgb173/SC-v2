# Proyecto de Análisis de Partidos

Este proyecto es una aplicación Streamlit para analizar partidos de fútbol utilizando datos en tiempo real.

## Requisitos

- Python 3.8 o superior
- Streamlit
- Playwright
- Pandas
- BeautifulSoup4
- Requests
- LXML

## Instalación

1. Clona este repositorio:
```bash
git clone <url-del-repositorio>
cd Definitivo
```

2. Crea un entorno virtual (opcional pero recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Instala los navegadores necesarios para Playwright:
```bash
playwright install chromium
```

## Ejecución

Para ejecutar la aplicación localmente:
```bash
streamlit run app.py
```

## Despliegue en Streamlit Cloud

1. Sube este repositorio a GitHub
2. Ve a [Streamlit Cloud](https://streamlit.io/cloud)
3. Crea una nueva aplicación seleccionando este repositorio
4. Configura `app.py` como el punto de entrada principal

## Estructura del Proyecto

- `app.py`: Aplicación principal de Streamlit
- `modules/`: Contiene los módulos de análisis y scraping
- `requirements.txt`: Dependencias del proyecto
- `README.md`: Este archivo

## Solución de Problemas

Si la aplicación no se ejecuta correctamente:

1. Verifica que todas las dependencias estén instaladas
2. Asegúrate de que los navegadores de Playwright estén instalados
3. Revisa la consola de errores para identificar problemas específicos
4. Ejecuta `python test_app.py` para verificar la instalación

## Notas

- La aplicación utiliza Playwright para hacer web scraping, lo que requiere navegadores adicionales
- El primer inicio puede tardar más tiempo mientras se instalan los navegadores
- En Streamlit Cloud, el despliegue puede tardar unos minutos en la primera ejecución