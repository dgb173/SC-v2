# Base ligera con Debian Bookworm
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/root/.local/bin:${PATH}" \
    CHROME_BIN="/usr/bin/chromium" \
    CHROMEDRIVER_PATH="/usr/bin/chromedriver"

# Paquetes del sistema necesarios para Chromium/Chrome, Selenium y Playwright
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates curl wget unzip \
      chromium chromium-driver \
      fonts-liberation fonts-dejavu-core \
      libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
      libgbm1 libxshmfence1 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libxfixes3 \
      libdrm2 libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar la cache
WORKDIR /app
COPY requirements.txt ./

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Instalar navegadores de Playwright y sus dependencias
# Nota: --with-deps instalará libs adicionales requeridas por Chromium headless
RUN python -m playwright install --with-deps chromium

# Copiar el resto del código
COPY . .

# Puerto de escucha (Render inyecta $PORT en runtime)
EXPOSE 10000

# Comando de arranque con gunicorn enlazando al puerto de Render
CMD bash -lc "gunicorn app:app -w 2 -k gthread -t 180 -b 0.0.0.0:${PORT:-10000}"
