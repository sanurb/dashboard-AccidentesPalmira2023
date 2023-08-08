FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer el puerto 8050 para Dash
EXPOSE 8050

CMD ["python", "tu_nombre_de_archivo.py"]
