FROM python:3.11-slim

WORKDIR /app

# Copy application
COPY phase4_microservice.py .
COPY trigram_model.json .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8000

# Start app
CMD ["python", "phase4_microservice.py"]
