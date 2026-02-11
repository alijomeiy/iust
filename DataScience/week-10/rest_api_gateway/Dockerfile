FROM python:3.11-slim

WORKDIR /app

# Build from week-10: docker build -f rest_api_gateway/Dockerfile .
COPY requirments.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY rest_api_gateway/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
