FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .

RUN pip install --no-cache-dir -r requirements-docker.txt
RUN pip install beautifulsoup4

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]