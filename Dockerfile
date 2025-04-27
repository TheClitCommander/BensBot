FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ procps netcat-openbsd curl gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
# Add MongoDB repository and install MongoDB client tools
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-5.0.asc | gpg -o /usr/share/keyrings/mongodb-server-5.0.gpg --dearmor && \
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-5.0.gpg ] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/5.0 main" | tee /etc/apt/sources.list.d/mongodb-org-5.0.list && \
    apt-get update && \
    apt-get install -y mongodb-org-tools mongodb-mongosh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory
RUN mkdir -p /app/data /app/logs /app/backups

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV USERS_DB_PATH=/app/data/users.json
ENV JWT_SECRET_KEY=CHANGE_ME_IN_PRODUCTION
ENV MONGODB_URI=mongodb://mongodb:27017/
ENV MONGODB_DATABASE=bensbot
ENV INITIAL_CAPITAL=100000
ENV WATCHDOG_INTERVAL=30
ENV LOG_LEVEL=INFO

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "trading_bot.main"] 