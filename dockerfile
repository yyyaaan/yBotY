FROM python:3.11-slim
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app

# entry point in docker compose (local) or Kubernetes deployment manifest