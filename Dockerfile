# Use Python 3.11 base image
FROM python:3.11-slim

# Install Node.js 20
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Brave Search MCP Server globally
RUN npm install -g @brave/brave-search-mcp-server

# Copy application code
COPY . .

# Expose default port (Railway will inject $PORT at runtime)
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app

# Start the application with gunicorn honoring $PORT
CMD ["sh", "-c", "gunicorn -w 2 -k gthread --threads 4 -t 180 app:app --bind 0.0.0.0:${PORT:-8080}"]
