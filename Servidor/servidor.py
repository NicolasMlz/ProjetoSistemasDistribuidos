from flask import Flask, request, jsonify
import pandas as pd
import csv
import requests
import threading

app = Flask(__name__)

arquivo_csv = 'noticias.csv'

def criar_noticia(dados):
    with open(arquivo_csv, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([dados["id"], dados["manchete"], dados["subtitulo"], dados["texto"], dados["data_publicacao"], dados["autor"], dados["classificacao_etaria"], dados["categoria"]])
    return "Notícia criada com sucesso."

@app.route('/noticias', methods=['POST'])
def endpoint_criar_noticia():
    dados = request.json
    return jsonify(criar_noticia(dados)), 201

@app.route('/noticias', methods=['GET'])
def ler_noticias():
    try:
        df = pd.read_csv(arquivo_csv)
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"erro": "Arquivo CSV não encontrado."}), 404

@app.route('/noticias/<int:id>', methods=['PUT'])
def atualizar_noticia(id):
    dados = request.json
    try:
        df = pd.read_csv(arquivo_csv)
        if id in df['id'].values:
            index = df.index[df['id'] == id].tolist()[0]
            for key, value in dados.items():
                df.at[index, key] = value
            df.to_csv(arquivo_csv, index=False)
            return jsonify({"message": f"Notícia com ID {id} atualizada com sucesso."})
        else:
            return jsonify({"erro": "ID não encontrado."}), 404
    except FileNotFoundError:
        return jsonify({"erro": "Arquivo CSV não encontrado."}), 404

@app.route('/noticias/<int:id>', methods=['DELETE'])
def deletar_noticia(id):
    try:
        df = pd.read_csv(arquivo_csv)
        df = df[df['id'] != id]
        df.to_csv(arquivo_csv, index=False)
        return jsonify({"message": f"Notícia com ID {id} deletada com sucesso."})
    except FileNotFoundError:
        return jsonify({"erro": "Arquivo CSV não encontrado."}), 404

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    try:
        df = pd.read_csv(arquivo_csv)
        categorias = df['categoria'].unique().tolist()
        return jsonify(categorias)
    except (FileNotFoundError, KeyError):
        return jsonify({"erro": "Arquivo CSV não encontrado ou coluna ausente."}), 404

# Função para registrar o servidor no Registro de Serviços
def registrar_servico():
    try:
        resposta = requests.post("https://registro-de-servicos.up.railway.app/registrar_servidor", json={
            "ip": "servidor-matrix.up.railway.app",
            "localizacao": "Brasil",
            "threads": threading.active_count()
        })
        print("Serviço registrado:", resposta.json())
    except Exception as e:
        print(f"Erro ao registrar serviço: {e}")

if __name__ == "__main__":
    registrar_servico()
    app.run(host="0.0.0.0", port=8080)
