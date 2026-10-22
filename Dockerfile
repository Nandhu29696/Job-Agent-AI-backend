FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Non-secret defaults; secrets come from .env / the orchestrator
ENV DB_PORT=5432 \
    DB_TYPE=postgresql \
    ALGORITHM=HS256

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
