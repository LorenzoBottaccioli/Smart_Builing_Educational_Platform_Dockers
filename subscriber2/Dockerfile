FROM python:3.9-slim

WORKDIR /app

# Copiamos requirements.txt y reinstalamos siempre (sin usar cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiamos el código
COPY subscriber2.py .

# Definimos el comando de arranque
CMD ["python3", "subscriber2.py"]

