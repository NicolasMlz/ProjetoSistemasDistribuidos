from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer
from threading import Thread
from queue import Queue
import time

servidor = ServerProxy("http://localhost:8000/")
request_queue = Queue()
response_dict = {}  

def enqueue_request(request_id, method_name, *args):
    request = {
        "request_id": request_id,
        "method_name": method_name,
        "args": args
    }
    request_queue.put(request)
    return f"Request {request_id} enqueued."

def process_queue():
    while True:
        request = request_queue.get()
        if request:
            request_id = request["request_id"]
            method_name = request["method_name"]
            args = request["args"]
            try:
                response = getattr(servidor, method_name)(*args)
                response_dict[request_id] = response  # Armazena a resposta no dicionário
                print(f"Requisição processada: {method_name} - Resposta armazenada para request_id {request_id}")
            except Exception as e:
                response_dict[request_id] = f"Erro: {e}"  # Armazena o erro no dicionário
                print(f"Erro ao processar requisição {method_name}: {e}")
            finally:
                request_queue.task_done()

def get_response(request_id):
    return response_dict.pop(request_id, "Resposta ainda não disponível. Tente novamente mais tarde.")

proxy_server = SimpleXMLRPCServer(("localhost", 9000))
print("Proxy server disponível em http://localhost:9000")

proxy_server.register_function(enqueue_request, "enqueue_request")
proxy_server.register_function(get_response, "get_response")

thread = Thread(target=process_queue, daemon=True)
thread.start()

proxy_server.serve_forever()
