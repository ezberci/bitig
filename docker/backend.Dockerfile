FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency file first for cache
COPY pyproject.toml .

# Install dependencies
RUN uv pip install --system -e .

# Copy source code
COPY src/ src/

# Create data directory
RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
