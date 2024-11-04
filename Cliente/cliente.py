import time
from xmlrpc.client import ServerProxy
import uuid

proxy = ServerProxy("http://localhost:9000/")

def print_line(char='=', length=50):
    print(char * length)

def welcome_screen():
    print_line()
    print(" " * 12 + "🚀 DISTRIBUTED NEWS 🚀")
    print_line()
    print("\nBem-vindo ao DISTRIBUTED NEWS!")
    time.sleep(1)
    
    name = input("Digite seu nome: ")
    birth_date = input("Digite sua data de nascimento (DD/MM/AAAA): ")
    print("\nÓtimo, {}! Vamos começar.".format(name))
    time.sleep(1)
    return name, birth_date

def news_menu():
    print("\n" + "=" * 50)
    print("📰 Escolha o tipo de notícia que você quer ler: ")
    print("=" * 50)
    print("1 - Esportes 🏅")
    print("2 - Política 🏛️")
    print("3 - Economia 💰")
    print("4 - Tecnologia 💻")
    print("5 - Entretenimento 🎬")
    print("6 - Ciência 🔬")
    print("0 - Sair")
    print("=" * 50)

    choice = input("Digite o número da sua escolha: ")
    return choice

def show_news_paginated(choice, page_size=5):
    categorias = {
        "1": "Esportes",
        "2": "Política",
        "3": "Economia",
        "4": "Tecnologia",
        "5": "Entretenimento",
        "6": "Ciência"
    }
    
    categoria = categorias.get(choice)
    if not categoria:
        print("Opção inválida. Tente novamente.")
        return
    
    # Enviar requisição ao proxy para buscar notícias por categoria
    request_id = str(uuid.uuid4())  # Gera um ID único para a requisição
    proxy.enqueue_request(request_id, "buscar_noticias_por_categoria", categoria)
    
    # Busca a resposta usando o request_id
    while True:
        response = proxy.get_response(request_id)
        if response != "Resposta ainda não disponível. Tente novamente mais tarde.":
            break
        time.sleep(0.5)  # Espera antes de tentar novamente

    if not isinstance(response, list) or not response:
        print("Nenhuma notícia encontrada para a categoria escolhida.")
        return

    noticias = response
    total_news = len(noticias)
    current_page = 0

    while True:
        start = current_page * page_size
        end = start + page_size
        news_page = noticias[start:end]

        print(f"\nMostrando notícias {start + 1} a {min(end, total_news)} de {total_news} para a categoria '{categoria}':")

        for noticia in news_page:
            print(f"ID: {noticia['id']}")
            print(f"Manchete: {noticia['manchete']}")
            print(f"Subtítulo: {noticia['subtitulo']}")
            print("-" * 50)

        # Navegação da página
        print("\nOpções:")
        if start > 0:
            print("P - Página Anterior")
        if end < total_news:
            print("N - Próxima Página")
        print("L - Ler uma notícia")
        print("S - Sair")

        option = input("Escolha uma opção: ").strip().upper()

        if option == "N" and end < total_news:
            current_page += 1
        elif option == "P" and start > 0:
            current_page -= 1
        elif option == "L":
            news_id = input("Digite o ID da notícia que deseja ler: ")
            show_news_detail(news_id)
        elif option == "S":
            break
        else:
            print("Opção inválida. Tente novamente.")

def show_news_detail(news_id):
    request_id = str(uuid.uuid4())  # Gera um ID único para a requisição
    proxy.enqueue_request(request_id, "buscar_noticia_por_id", news_id)
    
    # Busca a resposta usando o request_id
    while True:
        response = proxy.get_response(request_id)
        if response != "Resposta ainda não disponível. Tente novamente mais tarde.":
            break
        time.sleep(0.5)  # Espera antes de tentar novamente

    if isinstance(response, dict):
        print("\n--- Detalhe da Notícia ---")
        print(f"ID: {response['id']}")
        print(f"Manchete: {response['manchete']}")
        print(f"Subtítulo: {response['subtitulo']}")
        print(f"Texto: {response['texto']}")
        print(f"Data de Publicação: {response['data_publicacao']}")
        print(f"Autor: {response['autor']}")
        print(f"Classificação Etária: {response['classificacao_etaria']}")
        print("-" * 50)
    else:
        print("Notícia não encontrada.")
        

def main():
    name, birth_date = welcome_screen()
    while True:
        choice = news_menu()
        if choice == "0":
            print("\nObrigado por usar o DISTRIBUTED NEWS, {}! Até logo!".format(name))
            break
        else:
            show_news_paginated(choice)
            time.sleep(1)

if __name__ == "__main__":
    main()
