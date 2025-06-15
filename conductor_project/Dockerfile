FROM python:3.11-alpine

WORKDIR /app

# Install dependencies for Alpine and create tmp directory
RUN apk add --no-cache curl && \
    mkdir -p /tmp && \
    chmod 1777 /tmp

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create __init__.py files if they don't exist
RUN find app -type d -exec touch {}/__init__.py \;

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
