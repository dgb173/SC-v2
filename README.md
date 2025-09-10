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

### Método 1: Script Automático (Recomendado)

En Windows:
```bash
EMPEZAR_AQUI.bat
```

En Linux/Mac:
```bash
chmod +x empezar_aqui.sh
./empezar_aqui.sh
```

### Método 2: Instalación Manual

1. Crea un entorno virtual (opcional pero recomendado):
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Instala los navegadores necesarios para Playwright:
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
- `EMPEZAR_AQUI.bat/sh`: Scripts de inicio automático
- `INSTALAR.bat/sh`: Scripts de instalación
- `README.md`: Este archivo

## Solución de Problemas

Si la aplicación no se ejecuta correctamente:

1. Verifica que todas las dependencias estén instaladas:
   ```bash
   python verify_installation.py
   ```

2. Asegúrate de que los navegadores de Playwright estén instalados:
   ```bash
   playwright install chromium
   ```

3. Revisa la consola de errores para identificar problemas específicos

4. Si hay errores de importación, verifica que el directorio `modules` exista y contenga todos los archivos .py

## Notas

- La aplicación utiliza Playwright para hacer web scraping, lo que requiere navegadores adicionales
- El primer inicio puede tardar más tiempo mientras se instalan los navegadores
- En Streamlit Cloud, el despliegue puede tardar unos minutos en la primera ejecución
- La aplicación necesita acceso a internet para obtener los datos de los partidos