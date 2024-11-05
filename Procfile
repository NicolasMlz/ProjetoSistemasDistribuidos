# Usa uma imagem base do Python
FROM python:3.9

# Define o diretório de trabalho na imagem
WORKDIR /app

# Copia o arquivo requirements.txt e instala as dependências
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copia todos os arquivos para o diretório de trabalho
COPY . /app

# Expõe a porta 8000 (ou a porta em que o servidor está rodando)
EXPOSE 8000

# Define o comando de inicialização
CMD ["python", "Servidor/servidor.py"]
