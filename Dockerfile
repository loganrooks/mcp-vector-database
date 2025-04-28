# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies if needed (e.g., for psycopg binary)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./src /app/src

# Expose the port the app runs on (defined in config, default 8000)
# This is informational; the actual port mapping happens in docker-compose.yml
EXPOSE 8000

# Add a non-root user for security
RUN useradd --create-home appuser
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