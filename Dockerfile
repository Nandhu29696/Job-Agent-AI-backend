FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Database environment variables
ENV DB_HOST=localhost \
    DB_PORT=5432 \
    DB_NAME=job_agent \
    DB_USER=postgres \
    DB_PASSWORD=1234 \
    DB_TYPE=postgres

# OpenAI / App
ENV OPENAI_MODEL=gpt-4o-mini \
    ALGORITHM=HS256 \
    ACCESS_TOKEN_EXPIRE_MINUTES=10080

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
