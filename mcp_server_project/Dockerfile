FROM python:3.11-alpine

WORKDIR /app

# Install dependencies for Alpine and create tmp directory for MCP
RUN apk add --no-cache curl && \
    mkdir -p /tmp/mcp && \
    chmod 1777 /tmp

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server/ ./mcp_server/

# Create __init__.py if it doesn't exist
RUN touch mcp_server/__init__.py

EXPOSE 8001

# Health check for MCP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/legacy/health || exit 1

# Run MCP-enhanced server
CMD ["python", "-m", "mcp_server.main_mcp"]
