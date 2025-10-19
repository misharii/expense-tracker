# ===========================================
# FastAPI Expense Tracker - Production Dockerfile
# ===========================================

# ---- Stage 1: build dependencies ----
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Working directory in container
WORKDIR /app

# Install OS-level dependencies (optional but useful)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a temporary layer
COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels


# ---- Stage 2: runtime image ----
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy built wheels from builder stage
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy project files
COPY app/ ./app/
COPY tst.txt requirements.txt ./

# Expose FastAPI port
EXPOSE 8000

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8067"]