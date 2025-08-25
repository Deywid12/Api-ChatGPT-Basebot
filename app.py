import os, json, re
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from schema import IngestPayload
from rag import ingest_items, search, load_index, ingest_from_json_file, list_titles

load_dotenv()
app = Flask(__name__)

# Bootstrap opcional
load_index()
BOOTSTRAP = os.getenv("BOOTSTRAP_FILE")
if BOOTSTRAP and os.path.exists(BOOTSTRAP):
    # Só monta se ainda não existe índice
    try:
        # ingest_from_json_file é idempotente se limpar antes; aqui deixamos somar
        ingest_from_json_file(BOOTSTRAP)
        print(f"[BOOTSTRAP] Ingerido: {BOOTSTRAP}")
    except Exception as e:
        print(f"[BOOTSTRAP] Aviso: {e}")

# ======= Utilidades de "detecção de classe" =======
CLASSES = ("erros", "studio", "xwork", "integracao")

def guess_classe(query: str) -> str | None:
    q = query.lower()
    # Sinais óbvios primeiro
    if "xwork" in q:
        return "xwork"
    if "studio" in q:
        return "studio"
    # fallback: não adivinha -> None
    return None

def is_list_intent(q: str) -> bool:
    q = q.lower()
    patterns = [
        r"\blistar\b", r"\bquais (são|os) erros\b", r"\bver erros\b",
        r"\berros cadastrados\b", r"\blista de erros\b"
    ]
    return any(re.search(p, q) for p in patterns)

# ======= Rotas =======
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest():
    try:
        payload = IngestPayload(**request.get_json(force=True))
        result = ingest_items(payload.itens)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/search")
def http_search():
    q = request.args.get("q", "") or ""
    k = int(request.args.get("k", "6"))
    classe = request.args.get("classe")
    if classe not in CLASSES and classe is not None:
        return jsonify({"error": f"classe inválida: {classe}"}), 400
    return jsonify({"query": q, "classe": classe, "results": search(q, k, classe=classe)})

@app.get("/list")
def http_list():
    classe = request.args.get("classe")
    if not classe:
        return jsonify({"error": "informe ?classe=erros|studio|xwork|integracao"}), 400
    if classe not in CLASSES:
        return jsonify({"error": f"classe inválida: {classe}"}), 400
    titles = list_titles(classe)
    if not titles:
        return jsonify({"mensagem": f"Não há erros cadastrados para {classe} no momento."})
    return jsonify({"classe": classe, "titulos": titles})

@app.post("/chat")
def chat():
    """
    Regras implementadas conforme o roteiro do agente fornecido.
    Body esperado:
    {
      "query": "mensagem do usuário",
      "classe": "studio|xwork|erros|integracao (opcional)",
      "mode": "json|markdown|auto (default: json)",
      "k": 6
    }
    """
    body = request.get_json(force=True) if request.data else {}
    query = (body or {}).get("query", "") or ""
    classe = (body or {}).get("classe")
    mode = (body or {}).get("mode", "json")
    k = int((body or {}).get("k", 6))

    if classe and classe not in CLASSES:
        return jsonify({"error": f"classe inválida: {classe}"}), 400

    # Tratamento de mensagens incompletas
    if len(query.strip()) < 4:
        need = "Por favor, informe código do erro, descrição completa ou uma captura de tela."
        if mode == "markdown":
            return (f"**Solicitação incompleta**\n\n{need}")
        return jsonify({"mensagem": need})

    # Listagem por subclasse
    if is_list_intent(query) or ((body or {}).get("list_titles") is True):
        target = classe or guess_classe(query)
        if not target:
            # pedir a subclasse
            ask = "Qual subclasse você quer listar (studio, xwork, erros, integracao)?"
            if mode == "markdown":
                return f"**Confirmação necessária**\n\n{ask}"
            return jsonify({"mensagem": ask})
        titles = list_titles(target)
        if not titles:
            msg = f"Não há erros cadastrados para {target} no momento."
            if mode == "markdown":
                return msg
            return jsonify({"mensagem": msg})
        if mode == "markdown":
            return "\n".join([f"- {t}" for t in titles])
        return jsonify({"classe": target, "titulos": titles})

    # Identificar subclasse (prioriza input explícito)
    alvo = classe or guess_classe(query)
    if not alvo:
        # Sem classe identificável, seguimos 'erros' como área geral
        alvo = "erros"

    # Buscar APENAS dentro da subclasse
    resultados = search(query, k=k, classe=alvo)
    if not resultados:
        # Frase obrigatória quando não encontrar
        msg = "Este erro não está na nossa base de dados de erros do suporte. Por favor, encaminhe a ocorrência no grupo de suporte para análise."
        if mode == "markdown":
            return msg
        return jsonify({"mensagem": msg})

    # Checar ambiguidade
    if len(resultados) > 1:
        s0 = resultados[0]["score"]
        s1 = resultados[1]["score"]
        ambiguous = (s0 - s1) < 0.025  # muito próximos
        if ambiguous:
            opcoes = list(dict.fromkeys([r["titulo"] for r in resultados[:5]]))
            ask = "Encontrei mais de um erro possível. Qual destes se aplica ao seu caso?"
            if mode == "markdown":
                body = "\n".join([f"{i+1}. {t}" for i, t in enumerate(opcoes)])
                return f"**Confirmação necessária**\n\n{ask}\n\n{body}"
            return jsonify({"mensagem": ask, "opcoes": opcoes})

    # Seleciona o melhor
    top = resultados[0]
    # Agora precisamos retornar no formato exato (JSON) ou em Markdown com títulos em negrito
    # Para isso, precisamos recuperar os campos originais. Eles estão no 'chunk', mas podemos extrair do corpus original? 
    # Como o meta guarda apenas chunk, vamos reconstruir via heurística do próprio chunk.
    # Porém o ingest já colocou tudo no chunk com rótulos, então dá para parsear.
    def _extract(field, chunk):
        # Procura linhas iniciadas pelo rótulo
        m = re.search(rf"{field}\s*:\s*(.*)", chunk, re.IGNORECASE)
        return (m.group(1).strip() if m else "")

    ch = top["chunk"]
    titulo = _extract("Título", ch) or top["titulo"]
    porque = _extract("Por que ocorre", ch)
    tratativa = _extract("Tratativa", ch)
    resolucao = _extract("Resolução", ch)
    link = _extract("Fonte", ch)

    # Campos não documentados devem ficar vazios. (Já estão vazios se não houver no chunk)
    if mode == "markdown":
        def section(name, value):
            v = value if value else "_Não documentado._"
            return f"**{name}**\n{v}"
        parts = [
            section("Título", titulo),
            section("Por que ocorre", porque),
            section("Tratativa", tratativa),
            section("Resolução", resolucao),
            section("Link da base", f"[{link}]({link})" if link else ""),
        ]
        return "\n\n".join(parts)

    # JSON (padrão)
    return jsonify({
        "titulo": titulo or "",
        "porque_ocorre": porque or "",
        "tratativa": tratativa or "",
        "resolucao": resolucao or "",
        "link_da_base": link or ""
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True)
