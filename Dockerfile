FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright && playwright install --with-deps chromium

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY travel_rpa /app/travel_rpa

WORKDIR /app/travel_rpa

RUN python manage.py collectstatic --noinput --settings=config.settings.production || true

ENV PORT=8080
EXPOSE 8080

CMD python manage.py migrate --settings=config.settings.production && \
    gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 300
