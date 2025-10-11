# Dockerfile for ADK Web UI deployment
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY asistent/ ./asistent/
COPY run_web.py .

# Set environment variables (will be overridden by Cloud Run)
ENV GOOGLE_CLOUD_PROJECT=escribania-mastropasqua
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Start uvicorn
CMD ["uvicorn", "run_web:app", "--host", "0.0.0.0", "--port", "8080"]
