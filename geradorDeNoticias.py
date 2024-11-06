import csv
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('pt_BR')
categorias = ["Esportes", "Política", "Economia", "Tecnologia", "Entretenimento", "Ciência"]

def gerar_noticia(id):
    manchete = fake.sentence(nb_words=6)
    subtitulo = fake.sentence(nb_words=10)
    texto = fake.paragraph(nb_sentences=5)
    data_publicacao = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')
    autor = fake.name()
    classificacao_etaria = random.choice([0, 10, 12, 14, 16, 18])
    categoria = random.choice(categorias)
    
    return [id, manchete, subtitulo, texto, data_publicacao, autor, classificacao_etaria, categoria]

with open('noticias.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['id', 'manchete', 'subtitulo', 'texto', 'data_publicacao', 'autor', 'classificacao_etaria', 'categoria'])
    
    for i in range(1, 1001):
        writer.writerow(gerar_noticia(i))

print("Arquivo 'noticias.csv' gerado com sucesso.")
