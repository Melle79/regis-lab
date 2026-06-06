ARG BUILD_FROM=ghcr.io/home-assistant/base-python:3.12-alpine3.22
FROM $BUILD_FROM

RUN apk add --no-cache nodejs npm

WORKDIR /app

# Python-Dependencies
COPY backend/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Frontend: Dependencies installieren (inkl. @mdi/js)
COPY frontend/package.json ./frontend/
RUN cd frontend && npm install

# Cache-Buster
ARG CACHE_BUST=1

# Frontend-Quellcode kopieren und bauen
COPY frontend/ ./frontend/
RUN cd frontend && NODE_OPTIONS="--max-old-space-size=512" npm run build

# Backend kopieren
COPY backend/ ./backend/

# s6 Services
COPY rootfs/ /
RUN chmod a+x /etc/services.d/backend/run

EXPOSE 8099
