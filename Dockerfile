FROM python:3.10-slim

WORKDIR /app

COPY requirments.txt /app/requirments.txt
RUN pip install --no-cache-dir -r /app/requirments.txt

COPY rest_api_gateway/ /app/

EXPOSE 8000
CMD ["python","-m","uvicorn","main:app","--host","0.0.0.0","--port","8000"]
