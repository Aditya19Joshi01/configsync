FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only entrypoint; rest will be mounted via bind mount
COPY ./app /app/app

# Expose FastAPI default port
EXPOSE 8000

# Default command (overridden by docker-compose if needed)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]