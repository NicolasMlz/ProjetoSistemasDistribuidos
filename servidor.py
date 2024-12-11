from flask import Flask, request, jsonify
import pandas as pd
import csv
import requests
import threading
import socket
import psycopg2
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

# Obter URL do banco de dados do ambiente
DATABASE_URL = "postgresql://postgres:kdfNyyzbNrgukEMpumofykaheZOEjclt@junction.proxy.rlwy.net:25221/railway"

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
def criar_tabela(engine):
    metadata = MetaData()

    # Definição do esquema da tabela `noticia`
    noticia_table = Table(
        "noticia", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("manchete", Text, nullable=False),
        Column("subtitulo", Text),
        Column("texto", Text, nullable=False),
        Column("data_publicacao", Text, nullable=False),
        Column("autor", Text, nullable=False),
        Column("classificacao_etaria", Text, nullable=False),
        Column("categoria", Text, nullable=False)
    )

    # Criar a tabela no banco de dados, se ainda não existir
    metadata.create_all(engine)
    print("Tabela `noticia` criada/verificada com sucesso!")

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
        # Criar conexão com o banco
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        
        # Criar/verificar a tabela
        criar_tabela(engine)

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

        # Inserir os dados no banco
        df.to_sql('noticia', con=conn, if_exists='append', index=False)

        print("Dados do CSV importados com sucesso!")
    except Exception as e:
        print(f"Erro ao importar dados: {e}")
    finally:
        conn.close()

@app.route('/noticias', methods=['POST'])
def criar_noticia():
    dados = request.json
    try:
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
        return jsonify({"message": "Notícia criada com sucesso."}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"erro": f"Erro ao criar notícia: {e}"}), 500

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


def retornar_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

# Função para registrar o servidor no Registro de Serviços
def registrar_servico():
    try:
        resposta = requests.post("http://localhost:8080/registrar-servidor", json={
            "ip": retornar_ip(),
            "localizacao": "Brasil",
            "threads": threading.active_count()
        })
        print("Serviço registrado:", resposta.json())
    except Exception as e:
        print(f"Erro ao registrar serviço: {e}")

if __name__ == "__main__":
    importar_csv_para_banco()
    deletar_registros()
    registrar_servico()
    app.run(host="0.0.0.0", port=9000)
