# 🎙️ LocalVoice Agent (Piper TTS)

Assistente de voz assíncrono, local e focado em privacidade. O PC executa o
agente, as ferramentas e o TTS; o celular funciona como interface de voz.

![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-blue)
![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20FastStream%20%7C%20Agno%20%7C%20Piper-success)
![LLM](https://img.shields.io/badge/LLM-Local%20(Ollama)-orange)

## Capacidades

- Conversa em português do Brasil com histórico separado por sessão.
- Respostas normalizadas antes da interface e do Piper, sem Markdown ou `*`.
- Equipe Agno com membros especializados em conversação e sistema local.
- Consulta de data/hora e diagnóstico dos recursos locais por ferramentas seguras.
- STT no navegador, LLM via Ollama e TTS local com Piper.
- Comunicação assíncrona por WebSocket e Redis.

## Componentes

- **Cliente web** (`client/`): Web Speech API, WebSocket e Web Audio API.
- **Gateway** (`src/gateway/`): FastAPI, arquivos estáticos e WebSocket.
- **Broker**: Redis (`voice_commands`, `agent_responses`).
- **Worker** (`src/worker/`): Agno Team, normalização e Piper TTS.
- **Memória**: sessões persistidas no PostgreSQL fornecido pelo serviço pgvector.

Detalhes em [`docs/architecture.md`](docs/architecture.md).

## Estrutura

```text
src/
├── agents/     # conversation_agent.py, system_agent.py, team.py e factory.py
├── core/       # config, schemas, instructions, normalização e preflight
├── gateway/    # app.py, routes.py, api.py, controller.py e connections.py
├── tools/      # ferramentas do agente e Piper TTS
├── worker/     # app.py (wiring) e controller.py (processamento)
├── ui/         # painel Streamlit
└── main.py     # CLI
client/         # cliente web mobile
tests/          # testes unitários e de integração
voices/         # modelos locais do Piper
```

## Instalação

```bash
docker compose up -d
uv sync
ollama pull llama3.1:8b
uv run python -m piper.download_voices pt_BR-faber-medium
mv pt_BR-faber-medium.onnx* voices/
cp .env.example .env
```

O serviço `pgvector` também é o PostgreSQL usado pelo Agno para persistir as
sessões. A extensão vetorial fica disponível para uma base RAG futura, mas o
histórico de conversa é salvo em tabelas relacionais comuns.

### Recriar um volume incompatível com PostgreSQL 18

O PostgreSQL 18 usa um diretório de dados específico da versão. Se o volume foi
criado anteriormente com o mount em `/var/lib/postgresql/data` e não contém
dados que precisem ser mantidos, recrie-o uma única vez:

```bash
docker compose down -v
docker compose up -d
```

Não use `down -v` em um ambiente cujo banco precise ser preservado; nesse caso,
faça backup e migração antes de trocar o layout do volume.

## Execução

Em terminais separados:

```bash
uv run localvoice check
uv run localvoice serve
uv run faststream run src.worker.app:app
```

Abra `http://localhost:8000/` no computador.

## HTTPS na rede local

Para liberar o microfone no celular:

```bash
uv sync --group tls
uv run localvoice gen-cert
uv run localvoice serve
```

Depois abra `https://<ip-do-pc>:8000/` no celular e aceite o certificado local.

## Configuração do agente

```dotenv
LOCALVOICE_OLLAMA_MODEL=llama3.1:8b
LOCALVOICE_OLLAMA_TEMPERATURE=0.3
LOCALVOICE_DATABASE_URL=postgresql+psycopg://ai:ai@localhost:5532/ai
LOCALVOICE_DATABASE_SCHEMA=localvoice
LOCALVOICE_SESSION_TABLE=localvoice_sessions
LOCALVOICE_AGENT_HISTORY_RUNS=6
```

Temperaturas mais baixas deixam a linguagem mais consistente. O PostgreSQL
mantém cada conversa separada pelo identificador enviado pelo navegador.

## Desenvolvimento

```bash
uv run pre-commit install
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Os testes verificam, entre outros pontos, que Markdown e asteriscos não chegam
ao Piper e que os arquivos CSS/JS são servidos pelo gateway.
