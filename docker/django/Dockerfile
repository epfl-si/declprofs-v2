FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*


FROM base AS development

COPY requirements/ ./requirements/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/requirements-test.txt

COPY . .

WORKDIR /app/src

EXPOSE 8000


FROM base AS production

COPY requirements/ ./requirements/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/requirements.txt

COPY src/ ./src/

WORKDIR /app/src

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD gunicorn config.wsgi:application --bind 0.0.0.0:8000
