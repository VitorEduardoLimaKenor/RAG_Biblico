# Projeto RAG Bíblico
**RAG_biblico** é um projeto de **Question Answering Bíblico** que combina **Recuperação e Geração de Respostas (RAG)** usando inteligência artificial.

Ele permite que usuários façam perguntas em linguagem natural sobre a Bíblia, e o sistema responde de forma contextualizada utilizando:

- Busca semântica em versículos bíblicos (ChromaDB)
- Consultas ao Dicionário Bíblico de Easton para contexto histórico e cultural
- Tópicos bíblicos organizados (Naves)
- Acesso direto à Bíblia estruturada em JSON

O projeto integra um ***modelo de linguagem*** para analisar a pergunta, selecionar a melhor fonte de informação e gerar uma resposta precisa, exibida através de uma ***interface web simples em Streamlit***.

**Objetivo:** fornecer uma ferramenta interativa para estudo e pesquisa bíblica, combinando inteligência artificial com dados históricos e textuais da Bíblia.

---
## Estrutura do Projeto

O projeto está organizado de forma simples e modular, facilitando manutenção, leitura e escalabilidade:
```
RAG_Bíblico/
│
├── src/                         # Código principal do projeto
│   ├── biblia_agent.py          # Classe BibliaAgent: lógica de busca e análise de perguntas bíblicas
│   ├── chromadb.py              # Abstração do banco de dados vetorial ChromaDB
│   └── system_prompts.py        # Prompts utilizados pelo modelo de linguagem
│
├── data/                        # Dados em arquivos JSON
│   ├── bibliaAveMaria.json      # Bíblia em formato JSON
│   ├── dicionario_easton.json   # Dicionário Bíblico Easton em formato JSON
│   └── naves_topical.json       # Nave's Topical Bible em formato JSON
│
├── env.example                 # Exemplo de variáveis de ambiente
├── .gitignore                  # Arquivos e pastas ignoradas pelo Git
├── LICENSE                     # Licença do projeto
├── README.md                   # Documentação do projeto
├── app.py                      # Interface do usuário construída com Streamlit
└── requirements.txt            # Dependências Python do projeto
```
---