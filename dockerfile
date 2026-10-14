FROM python:3.14-slim

ARG GEMINI_API_KEY
ENV GEMINI_API_KEY=$GEMINI_API_KEY

ARG BACKUP_GEMINI_API_KEY
ENV BACKUP_GEMINI_API_KEY=$BACKUP_GEMINI_API_KEY

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libtk8.6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m pytest test_ai_manager.py
RUN python -m pytest -v test_logic_manager.py

CMD ["python", "main.py"]
