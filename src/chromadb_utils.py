import json
import chromadb
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from chromadb.api.types import EmbeddingFunction

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class LangchainEmbeddingFunction(EmbeddingFunction):
    def __init__(self, embedder):
        self.embedder = embedder

    def __call__(self, input: list[str]) -> list[list[float]]:
        logging.info(f"Gerando embeddings para {len(input)} documentos")
        return self.embedder.embed_documents(input)

class ChromaDB:
    def __init__(self):
        logging.info("Inicializando ChromaDB")
        self.client = chromadb.PersistentClient(path="./data/chroma_db")
        self.biblia_path = "./data/bibliaAveMaria.json"
        self.dicionario_path = "./data/dicionario_easton.json"
        self.naves_path = "./data/naves_topical.json"
        self.embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.functiom_embedder = LangchainEmbeddingFunction(self.embedding)


    def load_json(self, filepath: str):
        logging.info(f"Carregando JSON: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_collection(self, name: str):
        logging.info(f"Obtendo coleção: {name}")
        if name in [col.name for col in self.client.list_collections()]:
            logging.info(f"Coleção '{name}' já existe")
            return self.client.get_collection(name=name)
        
        logging.info(f"Coleção '{name}' não existe. Criando...")
        return self.client.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.functiom_embedder
        )
    
    def delete_collection(self, name: str):
        logging.info(f"Tentando deletar coleção: {name}")
        try:
            self.client.delete_collection(name=name)
            logging.info(f"Coleção '{name}' deletada com sucesso")
            return f"Coleção '{name}' foi deletada com sucesso."
        except Exception as e:
            logging.error(f"Erro ao deletar a coleção '{name}': {str(e)}")
            return f"Erro ao deletar a coleção '{name}': {str(e)}"

    def add_documents(self, collection_name: str, docs: list, ids: list):
        logging.info(f"Adicionando {len(docs)} documentos à coleção '{collection_name}'")
        collection = self._get_collection(collection_name)
        existing_ids = set(collection.get()["ids"])  # todos os ids já existentes
        new_docs, new_ids = [], []

        for doc, doc_id in zip(docs, ids):
            if doc_id not in existing_ids:  # só adiciona se não existir
                new_docs.append(doc)
                new_ids.append(doc_id)

        if new_docs:
            logging.info(f"Adicionando {len(new_docs)} documentos novos à coleção '{collection_name}'")
            collection.add(documents=new_docs, ids=new_ids)
        else:
            logging.info(f"Nenhum documento novo para adicionar na coleção '{collection_name}'")

        return collection

    def _add_in_batches(self, collection_name: str, docs: list, ids: list, metadatas: list, batch_size: int = 5000):
        logging.info(f"Adicionando documentos com metadados em lotes de {batch_size} para '{collection_name}'")
        for i in range(0, len(docs), batch_size):
            batch_docs = docs[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            logging.info(f"Adicionando lote {i // batch_size + 1} com {len(batch_docs)} documentos")
            collection = self._get_collection(collection_name)
            collection.add(documents=batch_docs, ids=batch_ids, metadatas=batch_metadatas)

    def ensure_collections(self):
        logging.info("Garantindo coleções e atualizando dados se necessário")

        # ---------------- BÍBLIA ----------------
        logging.info("Processando coleção Bíblia Ave Maria")
        biblia = self.load_json(self.biblia_path)
        docs, ids, metadatas = [], [], []
        for livro in biblia["antigoTestamento"] + biblia.get("novoTestamento", []):
            for cap in livro["capitulos"]:
                for versiculo in cap["versiculos"]:
                    texto = versiculo["texto"]
                    ref = f"{livro['nome']} {cap['capitulo']}:{versiculo['versiculo']}"
                    docs.append(texto)
                    ids.append(ref)
                    metadatas.append({
                        "livro": livro["nome"],
                        "capitulo": cap["capitulo"],
                        "versiculo": versiculo["versiculo"]
                    })

        collection_name = "biblia_ave_maria"
        collection = self._get_collection(collection_name)
        if len(collection.get()["ids"]) != len(ids):
            logging.info(f"Atualizando coleção '{collection_name}'")
            self.client.delete_collection(collection_name)
            collection = self._get_collection(collection_name)
            self._add_in_batches(collection_name, docs, ids, metadatas)
        else:
            logging.info(f"Coleção '{collection_name}' já está atualizada")

        # ---------------- DICIONÁRIO EASTON ----------------
        logging.info("Processando coleção Dicionário Easton")
        dicionario = self.load_json(self.dicionario_path)
        docs, ids, metadatas = [], [], []
        for i, item in enumerate(dicionario):
            termo = item["termo"]
            descricao = item["descricao"]
            docs.append(descricao)
            ids.append(f"{termo}_{i}")
            metadatas.append({"termo": termo})

        collection_name = "dicionario_easton"
        collection = self._get_collection(collection_name)
        if len(collection.get()["ids"]) != len(ids):
            logging.info(f"Atualizando coleção '{collection_name}'")
            self.client.delete_collection(collection_name)
            collection = self._get_collection(collection_name)
            self._add_in_batches(collection_name, docs, ids, metadatas)
        else:
            logging.info(f"Coleção '{collection_name}' já está atualizada")

        # ---------------- NAVES TOPICAL ----------------
        logging.info("Processando coleção Naves Topical")
        naves = self.load_json(self.naves_path)
        docs, ids, metadatas = [], [], []
        for i, item in enumerate(naves):
            topic = item["topic"]
            referencias = "; ".join(item["versiculos"])
            docs.append(referencias)
            ids.append(f"{topic}_{i}")
            metadatas.append({"topic": topic})

        collection_name = "naves_topical"
        collection = self._get_collection(collection_name)
        if len(collection.get()["ids"]) != len(ids):
            logging.info(f"Atualizando coleção '{collection_name}'")
            self.client.delete_collection(collection_name)
            collection = self._get_collection(collection_name)
            self._add_in_batches(collection_name, docs, ids, metadatas)
        else:
            logging.info(f"Coleção '{collection_name}' já está atualizada")

        logging.info("Todas as coleções foram processadas com sucesso")
        return {
            "biblia": self._get_collection("biblia_ave_maria"),
            "dicionario": self._get_collection("dicionario_easton"),
            "naves": self._get_collection("naves_topical"),
        }

#collections = ChromaDB()
#collections.delete_collection("biblia_ave_maria")
#collections.delete_collection("dicionario_easton")
#collections.delete_collection("naves_topical")