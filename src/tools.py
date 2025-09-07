import json
import chromadb
from langchain.agents import tool
import json
import re
from unidecode import unidecode

def normalizar_texto(texto: str) -> str:
    """
    Remove acentos, espaços extras e deixa tudo minúsculo para facilitar a busca.
    """
    texto = unidecode(texto)            # remove acentos
    texto = re.sub(r"\s+", "", texto)   # remove todos os espaços
    return texto.lower()

@tool
def buscar_na_biblia_json(arg: str):
    """
    Busca diretamente no JSON da Bíblia por livro e capítulo.
    Retorna todos os versículos do capítulo solicitado.
    """
    with open("./data/bibliaAveMaria.json", "r", encoding="utf-8") as f:
        biblia = json.load(f)

    try:
        livro, capitulo = arg.split(":")
    except Exception as e:
        return f"Erro ao interpretar entrada: {e}"
    
    livro_normalizado = normalizar_texto(livro)

    for testamento in ["antigoTestamento", "novoTestamento"]:
        for livro_obj in biblia.get(testamento, []):
            # pega nome e abreviação se existirem
            nome_norm = normalizar_texto(livro_obj.get("nome", ""))
            abrev_norm = normalizar_texto(livro_obj.get("abreviacao", ""))

            # compara tanto com nome quanto com abreviação
            if livro_normalizado in [nome_norm, abrev_norm]:
                for cap in livro_obj.get("capitulos", []):
                    if str(cap["capitulo"]) == str(capitulo).strip():
                        return {
                            "referencia": f"{livro_obj.get('nome', livro_obj.get('abreviacao'))} {capitulo}",
                            "versiculos": cap.get("versiculos", [])
                        }
    return None

@tool
def buscar_naves_topical(arg1: str) -> str:
    """
    Realiza busca por tópicos bíblicos no arquivo Naves (temas como fé, amor, perdão, obediência).
    """
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection("naves_topical")

    results = collection.query(
        query_texts=[arg1],
        n_results=3
    )

    documentos = results["documents"][0]
    metadados = results["metadatas"][0]

    serialized = "\n\n".join(
        f"Tópico: {meta['topic']}\nTexto: {doc}"
        for doc, meta in zip(documentos, metadados)
    )
    return serialized

@tool
def buscar_dicionario_easton(query: str) -> str:
    """
    Consulta o Dicionário Bíblico de Easton e retorna o termo e sua descrição.
    """
    with open("./data/dicionario_easton.json", "r", encoding="utf-8") as f:
        dicionario = json.load(f)

    termo_busca = normalizar_texto(query)

    for item in dicionario:
        termo_normalizado = normalizar_texto(item["termo"])
        if termo_normalizado == termo_busca:
            return f"{item['termo']}\n\n{item['descricao']}"

    return f"O termo '{query}' não foi encontrado no Dicionário de Easton."

@tool
def buscar_versiculos_semantica(query: str) -> str:
    """
    Busca versículos bíblicos usando busca semântica no ChromaDB.
    """
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection("biblia_ave_maria")

    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    documentos = results["documents"][0]
    metadados = results["metadatas"][0]
    print(metadados)

    serialized = "\n\n".join(
        f"livro: {meta['livro']}, capítulo: {meta['capitulo']}, versículo: {meta['versiculo']}\nTexto: {doc}"
        for doc, meta in zip(documentos, metadados)
    )
    return serialized
