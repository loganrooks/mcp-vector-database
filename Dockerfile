# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies needed for compiling psycopg (if needed) and other potential packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    iputils-ping \
    telnet \
    netcat-openbsd \
    strace \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
# Copy tests directory explicitly
COPY tests /app/tests

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application context (Still useful for other files like README, etc.)
# This ensures all files (src, tests, etc.) are in the image layer
# COPY . /app # Removed: Relying on explicit copies and volume mounts

# Debug: List contents after explicit copies
RUN ls -l /app

# Expose the port the app runs on (defined in config, default 8000)
# This is informational; the actual port mapping happens in docker-compose.yml
EXPOSE 8000

# Add a non-root user for security
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app
USER appuser
WORKDIR /app

# Command to run the application using Uvicorn
# The actual host and port binding should be handled by Uvicorn command arguments,
# potentially overridden by docker-compose.yml environment variables.
# Default command runs the FastAPI app.
CMD ["uvicorn", "src.philograph.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# To run MCP server instead, override the command in docker-compose.yml:
# command: ["python", "-m", "src.philograph.mcp.main"]
# Or create separate services/Dockerfiles if preferred.