# Python Automation Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY automation/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright OS dependencies
RUN playwright install-deps chromium

# Copy automation files
COPY automation/ ./

# Create browser profile directory
RUN mkdir -p browser_profile

# Expose port
EXPOSE 5001

# Start service
CMD ["python", "app.py"]
