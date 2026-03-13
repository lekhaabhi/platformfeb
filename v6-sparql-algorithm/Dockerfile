# Dockerfile for raru123/aeh-sparql-runner
FROM python:3.10-slim

# Working directory
WORKDIR /app

# OS deps (for TLS and curl debugging if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your algorithm folder (as-is)
COPY algorithm ./algorithm

# Copy the main runner script
COPY run_algorithm.py .

# Make sure Python prints immediately
ENV PYTHONUNBUFFERED=1

# IMPORTANT: do NOT use vantage6.tools.docker_wrapper
ENTRYPOINT ["python", "-u", "run_algorithm.py"]

