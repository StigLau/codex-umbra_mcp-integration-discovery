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
COPY mcp_server/ ./mcp_server/

# Create __init__.py if it doesn't exist
RUN touch mcp_server/__init__.py

# Run the application
CMD ["uvicorn", "mcp_server.main:mcp_app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
