# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app

# Copy installed packages
COPY --from=builder /install /usr/local

# Copy app
COPY phase4_microservice.py .
COPY trigram_model.json .

# Use non-root user
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Expose port (Railway sets PORT dynamically)
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
 CMD python -c "import urllib.request, os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8000)}/health')" || exit 1

# Env defaults
ENV MODEL_PATH="./trigram_model.json" \
    MAX_TOKENS=150 \
    TEMPERATURE=0.85 \
    PYTHONUNBUFFERED=1

# Start server
ENTRYPOINT ["python", "-m", "uvicorn", "phase4_microservice:app"]
CMD ["--host", "0.0.0.0", "--port", "${PORT}", "--workers", "1"]
