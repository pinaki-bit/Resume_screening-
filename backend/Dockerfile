FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (needed for pdfminer.six and spacy if building from source, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Download the spaCy model
RUN python -m spacy download en_core_web_lg

COPY . .

# Run database migrations before starting the app
# The entrypoint script will handle this
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
