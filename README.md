# Codigo desenvolvido para poder usar a API do ChatGPT dentro do chatbot da empresa onde trabalho

# BaseBot (Flask + RAG)
Assistente que **responde exclusivamente com base** no banco de dados interno.
Inclui:
- `/ingest` para ingerir/atualizar base (JSON).
- `/search` para buscar com filtro por `classe` e prioridade de **identificadores**.
- `/chat` que **implementa as regras do agente** (JSON por padrão, Markdown opcional).
- Bootstrap automático do arquivo em `BOOTSTRAP_FILE` (veja `.env.example`).

## Rodar
```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env && nano .env                 # cole sua API key
python app.py
```

## Testes rápidos
```bash
curl -s http://localhost:8000/health
curl -s "http://localhost:8000/search?q=twain&classe=erros&k=5"
curl -sX POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"query":"Erro: Error starting TCP/UDP receive thread", "classe":"erros"}' | jq
```

## Observações
- O endpoint `/chat` **não inventa** nada: se não achar, retorna a frase padrão exigida.
- Para **listar títulos** de uma subclasse: `{"query":"listar erros", "classe":"studio"}` ou `GET /list?classe=studio`.


