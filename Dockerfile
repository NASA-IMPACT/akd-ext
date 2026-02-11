FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e .

ENV APP_HOST=0.0.0.0 \
    APP_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "akd_ext.ui.cmr_care_app"]
