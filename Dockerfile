FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libpq-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel build

WORKDIR /app

COPY . .

COPY entrypoint.sh ./entrypoint.sh

# ✅ Make entrypoint.sh executable
RUN chmod +x ./entrypoint.sh

RUN pip install -r requirements.txt

EXPOSE 8000

# Optional: You can remove this if command is handled in docker-compose.yml
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
