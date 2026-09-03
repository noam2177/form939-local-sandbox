# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Set work directory
WORKDIR /app

# Install system dependencies (if any needed for pandas/openpyxl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p logs

# Command to run the benchmark (can be overridden)
CMD ["python", "src/main.py", "--input-dir", "data/synthetic_inputs", "--gt-csv", "data/gold/synthetic_ground_truth.csv"]
