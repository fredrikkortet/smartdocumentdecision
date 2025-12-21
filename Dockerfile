# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Create and set working directory
WORKDIR $APP_HOME

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Create and set working directory
WORKDIR $APP_HOME

# Copy only necessary files from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY src ./src
COPY context.md .

# Expose the port the API runs on
EXPOSE 8000

# Command to run the application
# We use gunicorn with uvicorn workers for production-ready deployment
# The API is located at src/api/app.py, so the module is api.app
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
