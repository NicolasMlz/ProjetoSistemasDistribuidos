import threading
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from socketserver import ThreadingMixIn
from xmlrpc.client import ServerProxy
import pandas as pd
import csv

arquivo_csv = 'noticias.csv'

# permite o uso de threads no servidor (ainda preciso testar com mais conexões pra ver)
class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

def contar_threads_ativas():
    return threading.active_count()

def criar_noticia(id, manchete, subtitulo, texto, data_publicacao, autor, classificacao_etaria, categoria):
    with open(arquivo_csv, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([id, manchete, subtitulo, texto, data_publicacao, autor, classificacao_etaria, categoria])
    return "Notícia criada com sucesso."

def ler_noticias():
    try:
        df = pd.read_csv(arquivo_csv)
        return df.to_dict(orient='records')
    except FileNotFoundError:
        return "Arquivo CSV não encontrado."

def atualizar_noticia(id, manchete=None, subtitulo=None, texto=None, data_publicacao=None, autor=None, classificacao_etaria=None, categoria=None):
    try:
        df = pd.read_csv(arquivo_csv)
        
        if id in df['id'].values:
            index = df.index[df['id'] == id].tolist()[0]
            if manchete: df.at[index, 'manchete'] = manchete
            if subtitulo: df.at[index, 'subtitulo'] = subtitulo
            if texto: df.at[index, 'texto'] = texto
            if data_publicacao: df.at[index, 'data_publicacao'] = data_publicacao
            if autor: df.at[index, 'autor'] = autor
            if classificacao_etaria is not None: df.at[index, 'classificacao_etaria'] = classificacao_etaria
            if categoria: df.at[index, 'categoria'] = categoria

            df.to_csv(arquivo_csv, index=False)
            return f"Notícia com ID {id} atualizada com sucesso."
        else:
            return "ID não encontrado."
    except FileNotFoundError:
        return "Arquivo CSV não encontrado."

def deletar_noticia(id):
    try:
        df = pd.read_csv(arquivo_csv)
        
        if id in df['id'].values:
            df = df[df['id'] != id]
            df.to_csv(arquivo_csv, index=False)
            return f"Notícia com ID {id} deletada com sucesso."
        else:
            return "ID não encontrado."
    except FileNotFoundError:
        return "Arquivo CSV não encontrado."

def buscar_noticias_por_categoria(categoria):
    try:
        df = pd.read_csv(arquivo_csv)
        noticias_categoria = df[df['categoria'] == categoria]
        
        if noticias_categoria.empty:
            return f"Não foram encontradas notícias na categoria '{categoria}'."
        else:
            return noticias_categoria.to_dict(orient='records')
    except FileNotFoundError:
        return "Arquivo CSV não encontrado."

def listar_categorias():
    """Retorna uma lista de todas as categorias de notícias únicas."""
    try:
        df = pd.read_csv(arquivo_csv)
        categorias = df['categoria'].unique().tolist()
        return categorias
    except FileNotFoundError:
        return "Arquivo CSV não encontrado."
    except KeyError:
        return "A coluna 'categoria' não foi encontrada no arquivo CSV."

def registrar_servico():
    """Registra o serviço ao iniciar."""
    try:
        registro_servico = ServerProxy("http://localhost:8001")  # Endereço do registro de serviços (ainda precisa criar)
        nome_servico = "NoticiasService"
        ip = "localhost"
        funcoes_disponiveis = [
            {
                "nome": "criar_noticia",
                "parametros": ["id (int)", "manchete (str)", "subtitulo (str)", "texto (str)", "data_publicacao (str)", "autor (str)", "classificacao_etaria (int)", "categoria (str)"],
                "retorno": "str (mensagem de confirmação)"
            },
            {
                "nome": "ler_noticias",
                "parametros": [],
                "retorno": "list (lista de dicionários com as notícias) ou str (mensagem de erro)"
            },
            {
                "nome": "atualizar_noticia",
                "parametros": ["id (int)", "manchete (str)", "subtitulo (str)", "texto (str)", "data_publicacao (str)", "autor (str)", "classificacao_etaria (int)", "categoria (str)"],
                "retorno": "str (mensagem de confirmação ou erro)"
            },
            {
                "nome": "deletar_noticia",
                "parametros": ["id (int)"],
                "retorno": "str (mensagem de confirmação ou erro)"
            },
            {
                "nome": "buscar_noticias_por_categoria",
                "parametros": ["categoria (str)"],
                "retorno": "list (lista de dicionários com as notícias da categoria) ou str (mensagem de erro)"
            },
            {
                "nome": "listar_categorias",
                "parametros": [],
                "retorno": "list (lista de categorias únicas) ou str (mensagem de erro)"
            },
            {
                "nome": "contar_threads_ativas",
                "parametros": [],
                "retorno": "int (número de threads ativas)"
            }
        ]
        registro_servico.registrar_servico(nome_servico, ip, funcoes_disponiveis)
        print("Serviço registrado com sucesso.")
    except Exception as e:
        print(f"Erro ao registrar serviço: {e}")

def iniciar_servidor():
    server = ThreadedXMLRPCServer(("localhost", 8000))
    print("Servidor RPC em execução na porta 8000...")
    
    server.register_function(criar_noticia, "criar_noticia")
    server.register_function(ler_noticias, "ler_noticias")
    server.register_function(atualizar_noticia, "atualizar_noticia")
    server.register_function(deletar_noticia, "deletar_noticia")
    server.register_function(buscar_noticias_por_categoria, "buscar_noticias_por_categoria")
    server.register_function(listar_categorias, "listar_categorias")
    server.register_function(contar_threads_ativas, "contar_threads_ativas")

    # Chama a função para registrar o serviço
    registrar_servico()

    server.serve_forever()

if __name__ == "__main__":
    iniciar_servidor()
