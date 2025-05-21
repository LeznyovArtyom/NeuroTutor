# Этап 1: Фронтенд
FROM node:18 AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json .
RUN npm install
COPY frontend/ .

RUN npm run build


# Этап 2: Бэкенд
FROM python:3.11-slim AS final

RUN apt-get update && \
    apt-get install -y mariadb-server nginx

WORKDIR /app

COPY --from=frontend /app/frontend/dist /usr/share/nginx/html

COPY backend/ ./backend
WORKDIR /app/backend

RUN pip install --no-cache-dir -q \
      -r requirements.txt \
      -f https://download.pytorch.org/whl/cpu/torch_stable.html

RUN service mariadb start && \
    mariadb -e "CREATE DATABASE IF NOT EXISTS NeuroTutor;" && \
    mariadb -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'app_password'; FLUSH PRIVILEGES;"

COPY nginx.conf /etc/nginx/sites-available/default

EXPOSE 80
EXPOSE 8000

ENV PYTHONPATH=/app

CMD service mariadb start && \
    sleep 5 && \
    python -m backend.database && \
    service nginx start && \
    gunicorn backend.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000