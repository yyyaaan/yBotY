# Yan Pan, 2023 
# As of June 2023, packages cannot fully support python 3.11, nor any slim
FROM python:3.11-bullseye
ENV PYTHONUNBUFFERED=1 HNSWLIB_NO_NATIVE=1


RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app

# entry point in docker compose (local) or Kubernetes deployment manifest