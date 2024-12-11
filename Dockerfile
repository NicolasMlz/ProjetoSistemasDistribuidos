# Usar imagem base do Python
FROM python:3.9

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos do servidor
COPY . /app

# Instalar dependências do sistema necessárias para o psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta 8000
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["python", "servidor.py"]
