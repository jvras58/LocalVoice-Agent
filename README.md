# 🎙️ LocalVoice Agent (Piper TTS)

Assistente de voz assíncrono, local e focado em privacidade. O PC atua como
*worker* (LLM + TTS) e o celular como interface de entrada (STT no navegador) e
saída (reprodução do áudio transmitido).

![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-blue)
![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20FastStream%20%7C%20Agno%20%7C%20Piper-success)
![LLM](https://img.shields.io/badge/LLM-Local%20(Ollama)-orange)

## Componentes

- **Cliente web** (`client/index.html`): Web Speech API (STT) + WebSocket + Web
  Audio API (reprodução do WAV em Base64).
- **Gateway** (`src/gateway/`): FastAPI + WebSocket, publica comandos e devolve
  o áudio pela conexão da sessão.
- **Broker**: Redis (`voice_commands`, `agent_responses`).
- **Worker** (`src/worker/`): FastStream + equipe Agno (Ollama) + Piper TTS.

Detalhes em [`docs/architecture.md`](docs/architecture.md).

## Estrutura

```
src/
├── core/       # config, schemas, instructions, capabilities (preflight)
├── tools/      # tts.py (Piper)
├── agents/     # factory.py, team.py (construtores Agno)
├── gateway/    # app.py (FastAPI+WS), connections.py
├── worker/     # app.py (FastStream)
├── ui/         # painel Streamlit
└── main.py     # CLI (localvoice check | info)
client/         # cliente web mobile
tests/unit/     # testes (pytest)
voices/         # modelos .onnx do Piper (ignorados pelo Git)
```

## Pré-requisitos

- [uv](https://github.com/astral-sh/uv)
- Docker e Docker Compose (Redis e PostgreSQL/pgvector)
- [Ollama](https://ollama.ai/) rodando localmente
- Uma voz do Piper (`.onnx` + `.onnx.json`) em `voices/`

## Instalação

```bash
# 1. Infraestrutura (Redis + pgvector)
docker compose up -d

# 2. Dependências
uv sync

# 3. Modelo do LLM
ollama pull llama3.1:8b

# 4. Voz do Piper (ver voices/README.md)
uv run python -m piper.download_voices pt_BR-faber-medium
mv pt_BR-faber-medium.onnx* voices/

# 5. Configuração
cp .env.example .env   # ajuste conforme necessário
```

## Execução

```bash
# Verifica Ollama e a voz do Piper
uv run localvoice check

# Gateway (HTTP/WebSocket) — serve também o cliente web em /
uv run uvicorn src.gateway.app:app --host 0.0.0.0 --port 8000

# Worker (Agno + Piper)
uv run faststream run src.worker.app:app

# Painel de operação/debug (opcional)
uv run --group ui streamlit run src/ui/app.py
```

Abra `http://<ip-do-pc>:8000/` no navegador do celular (mesma rede), toque no
microfone e fale. O reconhecimento de voz do navegador requer contexto seguro
(HTTPS) ou `localhost`; para acesso via IP na LAN, use um túnel/proxy HTTPS.

## Configuração

As variáveis (ver `.env.example`) correspondem 1:1 aos campos do `Settings`: URL do
Redis e nomes das filas, host e modelo do Ollama, caminho da voz do Piper e
host/porta do gateway.

## Desenvolvimento

```bash
uv run pre-commit install  # habilita os hooks (ruff + pytest) a cada commit
uv run ruff check .        # lint
uv run ruff format .       # formatação
uv run pytest              # testes (unitários + integração)
```

Os testes de `src/agents/` usam `pytest.importorskip("agno")` e só rodam com o
Agno instalado; os de `tests/integration/` exercitam o gateway com `TestClient`
e o `TestRedisBroker` (Redis em memória), sem servidor Redis real. Os testes
unitários rodam sem as dependências pesadas (Piper/ONNX).
