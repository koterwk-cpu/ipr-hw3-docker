FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser
USER 10001

ENV PYTHONDONTWRITEBYTECODE=1

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app .

EXPOSE 8000

CMD ["python", "app.py"]