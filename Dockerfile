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

COPY --from=frontend /app/frontend/dist /usr/share/nginx/html/tutor/

COPY backend/requirements.txt  ./requirements.txt

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY backend/ ./backend
WORKDIR /app/backend

RUN pip install --no-cache-dir -q \
      -r requirements.txt \
      -f https://download.pytorch.org/whl/cpu/torch_stable.html

RUN service mariadb start && \
    sleep 3 && \
    mariadb -u root -e "CREATE DATABASE IF NOT EXISTS NeuroTutor;" && \
    mariadb -u root -e "CREATE USER IF NOT EXISTS 'tutor'@'%' IDENTIFIED BY 'tutor_pass';" && \
    mariadb -u root -e "GRANT ALL PRIVILEGES ON NeuroTutor.* TO 'tutor'@'%';" && \
    mariadb -u root -e "FLUSH PRIVILEGES;"

COPY nginx.conf /etc/nginx/sites-available/default

EXPOSE 80
EXPOSE 8000

ENV PYTHONPATH=/app

CMD service mariadb start && \
    sleep 5 && \
    python -m backend.database.database && \
    service nginx start && \
    gunicorn backend.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000