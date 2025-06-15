FROM python:3.11-alpine

WORKDIR /app

# Install dependencies for Alpine and create tmp directory for MCP client
RUN apk add --no-cache curl && \
    mkdir -p /tmp/mcp && \
    chmod 1777 /tmp

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create __init__.py files if they don't exist
RUN find app -type d -exec touch {}/__init__.py \;

EXPOSE 8000

# Health check for Conductor
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run MCP-enhanced Conductor
CMD ["python", "-m", "app.main_mcp"]
