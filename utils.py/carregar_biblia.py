import json
import chromadb
from chromadb.config import Settings

# Caminho do JSON da Bíblia
BIBLIA_PATH = "./data/bibliaAveMaria.json"

# Inicializa o ChromaDB persistente (vai criar/usar a pasta ./chroma_db)
client = chromadb.PersistentClient(path="./chroma_db")

# Nome da coleção
COLLECTION_NAME = "bibliaAveMaria"

def carregar_biblia():
    # Se já existir, deleta a coleção
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"🗑 Coleção '{COLLECTION_NAME}' apagada para ser recriada.")
    except Exception:
        pass  # se não existir, ignora

    # Cria a coleção
    collection = client.create_collection(COLLECTION_NAME)
    print(f"📖 Coleção '{COLLECTION_NAME}' criada.")

    # Abre o JSON da Bíblia
    with open(BIBLIA_PATH, "r", encoding="utf-8") as f:
        biblia = json.load(f)

    documentos, metadados, ids = [], [], []

    def processar_testamento(testamento, nome_testamento):
        for livro in biblia.get(testamento, []):
            nome_livro = livro["nome"]
            for cap in livro["capitulos"]:
                capitulo = cap["capitulo"]
                for versiculo in cap["versiculos"]:
                    texto = versiculo["texto"]
                    num_versiculo = versiculo["versiculo"]

                    # ID único para cada versículo
                    doc_id = f"{nome_testamento}_{nome_livro}_{capitulo}_{num_versiculo}"

                    documentos.append(texto)
                    ids.append(doc_id)
                    metadados.append({
                        "testamento": nome_testamento,
                        "livro": nome_livro,
                        "capitulo": capitulo,
                        "versiculo": num_versiculo
                    })

    # Processa ambos os testamentos
    processar_testamento("antigoTestamento", "Antigo_Testamento")
    processar_testamento("novoTestamento", "Novo_Testamento")

    # Salva no ChromaDB
    print(f"Adicionando {len(documentos)} versículos ao ChromaDB...")
    collection.add(documents=documentos, metadatas=metadados, ids=ids)
    print("✔ Bíblia carregada com sucesso no ChromaDB!")

if __name__ == "__main__":
    carregar_biblia()
