import json
import chromadb
from langchain.agents import tool
import json
import re
from unidecode import unidecode
import logging

# Logger de módulo
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

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
    logger.info("buscar_na_biblia_json chamado com arg=%s", arg)
    with open("./data/biblia_ave_maria.json", "r", encoding="utf-8") as f:
        biblia = json.load(f)

    try:
        livro, capitulo = arg.split(":")
    except Exception as e:
        logger.error("Erro ao interpretar entrada em buscar_na_biblia_json: %s", e)
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
                        logger.debug("Capítulo encontrado: %s %s", livro_obj.get('nome', livro_obj.get('abreviacao')), capitulo)
                        return {
                            "referencia": f"{livro_obj.get('nome', livro_obj.get('abreviacao'))} {capitulo}",
                            "versiculos": cap.get("versiculos", [])
                        }
    return None

@tool
def buscar_dicionario_easton(query: str) -> str:
    """
    Consulta o Dicionário Bíblico de Easton e retorna o termo e sua descrição.
    """
    logger.info("buscar_dicionario_easton chamado com query=%s", query)
    with open("./data/dicionario_easton.json", "r", encoding="utf-8") as f:
        dicionario = json.load(f)

    termo_busca = normalizar_texto(query)

    for item in dicionario:
        termo_normalizado = normalizar_texto(item["termo"])
        if termo_normalizado == termo_busca:
            logger.debug("Termo encontrado no Easton: %s", item['termo'])
            return f"{item['termo']}\n\n{item['descricao']}"

    return f"O termo '{query}' não foi encontrado no Dicionário de Easton."

@tool
def buscar_versiculos_semantica(query: str) -> str:
    """
    Busca versículos bíblicos usando busca semântica no ChromaDB.
    """
    logger.info("buscar_versiculos_semantica chamado com query=%s", query)
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection("biblia_ave_maria")

    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    documentos = results["documents"][0]
    metadados = results["metadatas"][0]
    logger.debug("Metadados retornados: %s", metadados)

    serialized = "\n\n".join(
        f"livro: {meta['livro']}, capítulo: {meta['capitulo']}, versículo: {meta['versiculo']}\nTexto: {doc}"
        for doc, meta in zip(documentos, metadados)
    )
    return serialized
