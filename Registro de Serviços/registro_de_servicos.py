import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import threading
import time

# Estrutura para armazenar informações dos servidores
servidores = {}

# Função para registrar ou atualizar informações de um servidor
def registrar_servidor(ip, localizacao, threads):
    servidores[ip] = {
        'localizacao': localizacao,
        'threads': threads,
        'sobrecarregado': False
    }
    print(f"Servidor {ip} registrado/atualizado com sucesso.")

# Função para atualizar o status de threads e checar se o servidor está ativo
def atualizar_status_servidor(ip):
    if ip in servidores:
        try:
            # Verifica a conexão com o servidor
            with xmlrpc.client.ServerProxy(f"http://{ip}:8000/") as proxy:
                # Pega o número de threads remotamente
                threads = proxy.get_threads()
                servidores[ip]['threads'] = threads
                
                # Verifica sobrecarga baseado em um limite de threads
                limite_threads = 100  # ajuste conforme necessário
                servidores[ip]['sobrecarregado'] = threads > limite_threads
                print(f"Servidor {ip} atualizado. Threads: {threads}. Sobrecarregado: {servidores[ip]['sobrecarregado']}")
                
        except Exception as e:
            del servidores[ip]
            print(f"Servidor {ip} removido devido a inatividade: {e}")
    else:
        print(f"Servidor {ip} não encontrado.")


# Thread que verifica e atualiza status dos servidores periodicamente
def monitorar_servidores():
    while True:
        for ip in list(servidores.keys()):
            atualizar_status_servidor(ip)
        time.sleep(10)  # Verifica a cada 10 segundos

# Função para consulta do balanceador, retorna todos os servidores registrados
def consultar_servidor():
    print("Consulta do balanceador realizada. Todos os servidores:", servidores)
    return servidores

# Iniciar o servidor de registro de serviços
def iniciar_registro():
    with SimpleXMLRPCServer(("localhost", 9000), allow_none=True) as server:
        server.register_function(registrar_servidor, "registrar_servidor")
        server.register_function(atualizar_status_servidor, "atualizar_status_servidor")
        server.register_function(consultar_servidor, "consultar_servidor")
        
        # Thread para monitorar os servidores que se registram
        threading.Thread(target=monitorar_servidores, daemon=True).start()
        
        print("Registro de Serviços em execução...")
        server.serve_forever()

# Iniciar o registro de serviços
iniciar_registro()
