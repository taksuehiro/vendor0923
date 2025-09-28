FROM python:3.11-slim

ARG GIT_SHA
ENV GIT_SHA=${GIT_SHA}

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN echo "GIT_SHA=${GIT_SHA}" > /app/BUILD_INFO

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]






