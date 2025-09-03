import json
import chromadb

class ObrasFunctions:
    def __init__(self, obra_path: str, chroma_path: str, collection_name: str):
        self.obra_path = obra_path
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = None

    def load_collection(self):
        """Carrega o JSON e cria/atualiza a collection no ChromaDB em lotes."""
        # Verifica se a coleção já existe
        if self.collection_name in [c.name for c in self.client.list_collections()]:
            self.collection = self.client.get_collection(self.collection_name)
            return

        # Cria a coleção
        self.collection = self.client.create_collection(self.collection_name)
        print(f"📖 Coleção '{self.collection_name}' criada.")

        with open(self.obra_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        documents, metadatas, ids = [], [], []

        for i, item in enumerate(data):
            # Estrutura do Dicionário Easton
            if "termo" in item and "descricao" in item:
                doc_text = f"{item['termo']}: {item['descricao']}"
                metadata = {"termo": item["termo"]}
            
            # Estrutura do Nave’s Topical Bible
            elif "topic" in item and "versiculos" in item:
                doc_text = f"Tópico: {item['topic']} | Versículos: {', '.join(item['versiculos'])}"
                metadata = {"topic": item["topic"]}
            
            else:
                continue  # ignora registros fora do padrão

            documents.append(doc_text)
            metadatas.append(metadata)
            ids.append(f"{self.collection_name}_{i}")

            # Salva no ChromaDB em lotes
            batch_size = 5000
            if len(documents) >= batch_size:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"📥 Inseridos {len(documents)} documentos em '{self.collection_name}'")
                documents, metadatas, ids = [], [], []

        # Salva o restante que ficou no buffer
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"📥 Inseridos {len(documents)} documentos finais em '{self.collection_name}'")

        print(f"✅ Collection '{self.collection_name}' carregada com {len(data)} documentos no total.")


    def delete_collection(self):
        """Apaga a collection do ChromaDB."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
            print(f"Collection '{self.collection_name}' foi apagada com sucesso.")
        except Exception as e:
            print(f"Erro ao apagar a collection '{self.collection_name}': {e}")


    def semantic_search(self, query: str, n_results: int = 5):
        """Realiza uma busca semântica e retorna os resultados serializados em texto pronto para prompt."""
        if not self.collection:
            self.collection = self.client.get_or_create_collection(name=self.collection_name)

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        documentos = results["documents"][0]
        metadados = results["metadatas"][0]

        # Serializa de forma diferente dependendo da collection
        serialized_parts = []
        for doc, meta in zip(documentos, metadados):
            if "termo" in meta:  # Dicionário Easton
                serialized_parts.append(
                    f"Termo: {meta['termo']}\nTexto: {doc}"
                )
            elif "topic" in meta:  # Nave's Topical Bible
                serialized_parts.append(
                    f"Tópico: {meta['topic']}\nTexto: {doc}"
                )
            elif {"livro", "capitulo", "versiculo"} <= meta.keys():  # Caso Bíblia pura
                serialized_parts.append(
                    f"Livro: {meta['livro']}, Capítulo: {meta['capitulo']}, Versículo: {meta['versiculo']}\nTexto: {doc}"
                )
            else:
                serialized_parts.append(f"📖 Texto: {doc}")

        # Junta tudo em um único texto
        serialized = "\n\n".join(serialized_parts)
        return serialized