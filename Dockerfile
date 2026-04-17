# Use the official Playwright Python image
FROM mcr.microsoft.com/playwright/python:v1.58.2-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5001

WORKDIR /app

# Install system dependencies if any extra are needed (usually Playwright image has them)
# RUN apt-get update && apt-get install -y ...

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure output directory exists and is writable
RUN mkdir -p output && chmod 777 output

# Expose the port
EXPOSE 5001

# Command to run the application
CMD ["python", "dashboard.py"]
