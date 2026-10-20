FROM python:3.12-slim AS builder

RUN pip install poetry==2.5.1

RUN apt-get update && apt-get install -y \
    gcc

# Create and set working directory
WORKDIR /code

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* /code/

# Install dependencies into /code/.venv, so Poetry itself stays in this stage
RUN poetry config virtualenvs.in-project true \
    && poetry install --only main --no-root

# Copy application code
COPY . /code

# Stage 2: Runtime
FROM python:3.12-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /code

# Copy application code and its virtualenv
COPY --from=builder /code /code

# Set environment variables
ARG GIT_TAG=dev
ENV PATH="/code/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_VERSION=$GIT_TAG

# Expose port (if necessary, e.g., for a web app)
EXPOSE 8000

# Run the application (modify as needed)
CMD ["./run_production_server.sh"]