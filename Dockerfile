FROM python:3.13-slim as builder

RUN pip install -U poetry==1.8.3

RUN apt-get update && apt-get install -y \
    gcc

# Create and set working directory
WORKDIR /code

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* /code/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-root

# Copy application code
COPY . /code

# Stage 2: Runtime
FROM python:3.13-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create and set working directory
WORKDIR /code

# Copy application code
COPY --from=builder /code /code

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3

# Expose port (if necessary, e.g., for a web app)
EXPOSE 8000

# Run the application (modify as needed)
CMD ["./run_production_server.sh"]