import json
import math
import chromadb

class BibliaFunctions:
    def __init__(self, biblia_path: str, chroma_path: str, collection_name: str):
        self.biblia_path = biblia_path
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = None

    def carregar_biblia(self):
        # Verifica se a coleção já existe
        if self.collection_name in [c.name for c in self.client.list_collections()]:
            self.collection = self.client.get_collection(self.collection_name)
            return

        # Cria a coleção
        self.collection = self.client.create_collection(self.collection_name)
        print(f"📖 Coleção '{self.collection_name}' criada.")

        # Abre o JSON da Bíblia
        with open(self.biblia_path, "r", encoding="utf-8") as f:
            biblia = json.load(f)

        documentos, metadados, ids = [], [], []

        for testamento, nome_testamento in [("antigoTestamento", "Antigo_Testamento"), ("novoTestamento", "Novo_Testamento")]:
            for livro in biblia.get(testamento, []):
                nome_livro = livro["nome"]
                for cap in livro["capitulos"]:
                    capitulo = cap["capitulo"]
                    for versiculo in cap["versiculos"]:
                        texto = versiculo["texto"]
                        num_versiculo = versiculo["versiculo"]

                        doc_id = f"{nome_testamento}_{nome_livro}_{capitulo}_{num_versiculo}"

                        documentos.append(texto)
                        ids.append(doc_id)
                        metadados.append({
                            "testamento": nome_testamento,
                            "livro": nome_livro,
                            "capitulo": capitulo,
                            "versiculo": num_versiculo
                        })

        # Salva no ChromaDB em lotes
        batch_size = 5000
        total = len(documentos)
        print(f"Adicionando {total} versículos ao ChromaDB em lotes de {batch_size}...")
        for i in range(0, total, batch_size):
            end = i + batch_size
            self.collection.add(
                documents=documentos[i:end],
                metadatas=metadados[i:end],
                ids=ids[i:end]
            )
            print(f"Lote {i//batch_size + 1} ({i} a {min(end, total)}) adicionado.")

        print("✔ Bíblia carregada com sucesso no ChromaDB!")


    def delete_collection(self):
        """Apaga a collection do ChromaDB."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
            print(f"Collection '{self.collection_name}' foi apagada com sucesso.")
        except Exception as e:
            print(f"Erro ao apagar a collection '{self.collection_name}': {e}")
            

    def busca_versiculo(self, query: str, n_results: int):
        collection = self.client.get_collection(self.collection_name)

        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )

        documentos = results["documents"][0]
        metadados = results["metadatas"][0]

        serialized = "\n\n".join(
            f"livro: {meta['livro']}, capítulo: {meta['capitulo']}, versículo: {meta['versiculo']}\nTexto: {doc}"
            for doc, meta in zip(documentos, metadados)
        )

        return serialized
    
    def buscar_por_referencia(self, livro: str, capitulo: int):
        with open(self.biblia_path, "r", encoding="utf-8") as f:
            biblia = json.load(f)

        livro_lower = livro.lower()

        for testamento in ["antigoTestamento", "novoTestamento"]:
            for livro_obj in biblia.get(testamento, []):
                # pega nome e abreviação se existirem
                nome = livro_obj.get("nome", "").lower()
                abrev = livro_obj.get("abreviacao", "").lower()

                # compara tanto com nome quanto com abreviação
                if livro_lower in [nome, abrev]:
                    for cap in livro_obj.get("capitulos", []):
                        if cap["capitulo"] == capitulo:
                            return {
                                "referencia": f"{livro_obj.get('nome', livro_obj.get('abreviacao'))} {capitulo}",
                                "versiculos": cap.get("versiculos", [])
                            }

        return None
