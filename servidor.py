from flask import Flask, request, jsonify
import pandas as pd
import csv
import requests
import threading
import socket
import psycopg2
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, text
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

# Obter URL do banco de dados do ambiente
DATABASE_URL = "postgresql://postgres:AzFShVYcrGPfpjajWolwKgFIIwquCtaR@junction.proxy.rlwy.net:58430/railway"

# Nome do arquivo CSV com as notícias
arquivo_csv = "noticias.csv"

# Configurar conexão global
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("Conexão com o banco de dados PostgreSQL estabelecida!")
except Exception as e:
    print("Erro ao conectar ao banco de dados:", e)
    conn = None

# Criar tabela no banco
# Criar tabela no banco
def criar_tabela():
    try:
        # Usar a conexão global `conn`
        with conn.cursor() as cursor:

            # Cria a tabela novamente
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS noticia (
                    id SERIAL PRIMARY KEY,  -- Usando SERIAL para auto incremento
                    manchete TEXT NOT NULL,
                    subtitulo TEXT,
                    texto TEXT NOT NULL,
                    data_publicacao TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    classificacao_etaria TEXT NOT NULL,
                    categoria TEXT NOT NULL
                )
            """)
            conn.commit()  # Commit após criar a tabela
        print("Tabela `noticia` criada/atualizada com sucesso!")
    except Exception as e:
        print(f"Erro ao criar a tabela: {e}")
        conn.rollback()  # Caso haja algum erro, desfaz a transação

# Deletar registros anteriores do banco
def deletar_registros():
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM noticia")
            conn.commit()  # Confirmar a transação
            print("Todas as notícias antigas foram excluídas com sucesso!")
    except Exception as e:
        conn.rollback()  # Caso haja erro, desfazemos a transação
        print(f"Erro ao deletar registros: {e}")

# Importar csv para o banco quando o servidor subir
def importar_csv_para_banco():
    try:
        # Criar/verificar a tabela
        criar_tabela()

        # Ler o CSV com pandas
        df = pd.read_csv(arquivo_csv)

        # Renomear colunas para corresponderem à tabela do banco
        df = df.rename(columns={
            "manchete": "manchete",
            "subtitulo": "subtitulo",
            "texto": "texto",
            "data_publicacao": "data_publicacao",
            "autor": "autor",
            "classificacao_etaria": "classificacao_etaria",
            "categoria": "categoria"
        })

        # Remover a coluna "id" caso esteja presente no DataFrame
        if "id" in df.columns:
            df = df.drop(columns=["id"])
        df = df.dropna()

        # Iterar sobre cada linha e inserir no banco de dados
        for _, row in df.iterrows():
            dados = row.to_dict()
            resposta = criar_noticia_bd(dados)
            print(resposta)  # Pode ser útil para depuração
            criar_noticia_bd(dados)
        print("Dados do CSV importados com sucesso!")
    except Exception as e:
        print(f"Erro ao importar dados: {e}")

def criar_noticia_bd(dados):
    try:
        # Remover o campo 'id', pois o banco vai gerar automaticamente
        if "id" in dados:
            del dados["id"]

        # Assumindo que a conexão conn já está estabelecida
        with conn.cursor() as cursor:
            query = """
                INSERT INTO noticia (manchete, subtitulo, texto, data_publicacao, autor, classificacao_etaria, categoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                dados["manchete"], dados["subtitulo"], dados["texto"],
                dados["data_publicacao"], dados["autor"], dados["classificacao_etaria"], dados["categoria"]
            ))
            conn.commit()
        return {"message": "Notícia criada com sucesso."}
    except Exception as e:
        conn.rollback()
        return {"erro": f"Erro ao criar notícia: {e}"}

@app.route('/noticias', methods=['GET'])
def ler_noticias():
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM noticia")
            rows = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            noticias = [dict(zip(colunas, row)) for row in rows]
        return jsonify(noticias), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao listar notícias: {e}"}), 500

@app.route('/noticias/<int:id>', methods=['PUT'])
def atualizar_noticia(id):
    dados = request.json
    try:
        with conn.cursor() as cursor:
            # Gerar o comando SQL dinamicamente com base nos campos fornecidos
            campos = ", ".join([f"{key} = %s" for key in dados.keys()])
            valores = list(dados.values()) + [id]
            query = f"UPDATE noticia SET {campos} WHERE id = %s"
            cursor.execute(query, valores)
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"erro": "ID não encontrado."}), 404
        return jsonify({"message": f"Notícia com ID {id} atualizada com sucesso."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"erro": f"Erro ao atualizar notícia: {e}"}), 500

@app.route('/noticias/<int:id>', methods=['DELETE'])
def deletar_noticia(id):
    try:
        with conn.cursor() as cursor:
            query = "DELETE FROM noticia WHERE id = %s"
            cursor.execute(query, (id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"erro": "ID não encontrado."}), 404
        return jsonify({"message": f"Notícia com ID {id} deletada com sucesso."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"erro": f"Erro ao deletar notícia: {e}"}), 500

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    try:
        with conn.cursor() as cursor:
            query = "SELECT DISTINCT categoria FROM noticia"
            cursor.execute(query)
            categorias = [row[0] for row in cursor.fetchall()]
        return jsonify(categorias), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao listar categorias: {e}"}), 500

@app.route('/noticias/total', methods=['GET'])
def contar_noticias():
    try:
        with conn.cursor() as cursor:
            query = "SELECT COUNT(*) FROM noticia"
            cursor.execute(query)
            total = cursor.fetchone()[0]
        return jsonify({"total_noticias": total}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao contar notícias: {e}"}), 500

@app.route('/noticias/categoria/<string:categoria>', methods=['GET'])
def noticias_por_categoria(categoria):
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM noticia WHERE categoria = %s"
            cursor.execute(query, (categoria,))
            rows = cursor.fetchall()
            if not rows:
                return jsonify({"erro": f"Não foram encontradas notícias na categoria '{categoria}'."}), 404
            colunas = [desc[0] for desc in cursor.description]
            noticias = [dict(zip(colunas, row)) for row in rows]
        return jsonify(noticias), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar notícias por categoria: {e}"}), 500

@app.route('/noticias/<int:id>', methods=['GET'])
def obter_noticia_por_id(id):
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM noticia WHERE id = %s"
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"erro": f"Notícia com ID {id} não encontrada."}), 404
            colunas = [desc[0] for desc in cursor.description]
            noticia = dict(zip(colunas, row))
        return jsonify(noticia), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar notícia: {e}"}), 500

# Função para registrar o servidor no Registro de Serviços
def registrar_servidor():
    try:
        # IP do servidor de registro
        ip_registro_de_servicos = "https://registro-de-servicos.up.railway.app"  # Endereço do serviço de registro
        ip_servidor = "https://servidor-matrix.up.railway.app"
        threads = threading.active_count()  # Número de threads ativas no servidor

        # Requisição POST para registrar o servidor no servidor de registro
        resposta = requests.post(f"{ip_registro_de_servicos}/registrar-servidor", json={
            "ip": ip_servidor,
            "threads": threads
        })

        if resposta.status_code == 200:
            print(f"Servidor registrado com sucesso: {resposta.json()}")
        else:
            print(f"Erro ao registrar servidor: {resposta.status_code} - {resposta.text}")
    except Exception as e:
        print(f"Erro ao registrar o servidor: {e}")

@app.route("/get_threads", methods=["GET"])
def get_threads():
    # Retorna o número de threads ativas no servidor
    return jsonify({"threads": threading.active_count()}), 200

if __name__ == "__main__":
    importar_csv_para_banco()
    registrar_servidor()
    port = int(os.getenv("PORT", 9000))
    app.run(host="0.0.0.0", port=port)
