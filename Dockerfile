FROM python:3.12.3-slim

WORKDIR /apps

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Sudah sesuai dengan main.py dan variabel app Anda
CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:app"]