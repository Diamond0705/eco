FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
CMD ["waitress-serve", "--listen=0.0.0.0:8000", "config.wsgi:application"]
