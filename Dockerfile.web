# Dockerfile for ADK Web UI deployment
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code
COPY asistent/ ./asistent/

# Copy authentication wrapper and templates
COPY main.py .
COPY templates/ ./templates/

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set environment variables (will be overridden by Cloud Run)
ENV GOOGLE_CLOUD_PROJECT=escribania-mastropasqua
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV PORT=8080
ENV AGENT_ENGINE_ID=1053512459316363264
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Expose port
EXPOSE 8080

# Start supervisord (manages both Flask and ADK Web)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
