# 🎙️ LocalVoice Agent (Piper TTS)

Um assistente de voz assíncrono, focado em privacidade e execução local, orquestrado por múltiplos agentes. Desenhado  rodar no PC como *worker* e ser acessado via *smartphone* como interface de entrada/saída.

![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-blue)
![Stack](https://img.shields.io/badge/Stack-Python%20%7C%20FastAPI%20%7C%20FastStream%20%7C%20Agno%20%7C%20Piper-success)
![LLM](https://img.shields.io/badge/LLM-Local%20(Ollama)-orange)

## 🚀 Visão Geral
Nesta versão da arquitetura, o assistente utiliza **Piper TTS** processado localmente no PC para gerar vozes neurais ultra-realistas e de baixíssima latência. O áudio é transmitido (stream) diretamente para o celular, transformando o smartphone em um terminal de captação (STT) e reprodução de áudio, enquanto todo o peso de processamento (LLM + TTS) fica no backend.

## 🧩 Componentes

1. **Frontend (Mobile/Web):** Interface leve. Captura áudio, transcreve (STT) via navegador, envia textos ao gateway e reproduz o stream de áudio binário devolvido pelo servidor.
2. **Gateway (FastAPI):** Mantém conexões WebSocket com o frontend. Recebe comandos, publica no Redis e faz o stream do áudio final de volta para o cliente.
3. **Message Broker (Redis):** Fila de alta performance (Pub/Sub) gerenciando a comunicação assíncrona.
4. **Worker (FastStream + Agno + Piper):** O cérebro e a "voz" do sistema. Consome mensagens, delega tarefas para a equipe de agentes e sintetiza a resposta em áudio usando o Piper TTS, devolvendo o arquivo gerado para a fila.

## 📦 Pré-requisitos
- [uv](https://github.com/astral-sh/uv) (Gerenciador de pacotes)
- Docker & Docker Compose (Para Redis e PostgreSQL)
- [Ollama](https://ollama.ai/) rodando localmente (ex: `ollama run hermes2`)
- [Piper TTS](https://github.com/rhasspy/piper) (Binário local e modelos de voz `.onnx`)

## 🛠️ Instalação e Execução

### 1. Subir a Infraestrutura (Redis e DB)
```bash
docker run -d --name localvoice-redis -p 6379:6379 redis:alpine
docker run -d -e POSTGRES_DB=ai -e POSTGRES_USER=ai -e POSTGRES_PASSWORD=ai -p 5532:5432 --name pgvector agnohq/pgvector:18
```

### 2. Configurar o Ambiente com `uv`
```bash
uv init
uv add fastapi uvicorn faststream[redis] agno sqlalchemy psycopg ollama pydantic-settings
# O piper-tts pode ser instalado via pip ou baixado como binário autônomo
uv pip install piper-tts
```

### 3. Baixar Vozes do Piper
Faça o download de um modelo de voz em português (ex: `pt_BR-faber-medium.onnx` e seu arquivo `.json`) do repositório oficial do Piper e coloque na pasta `voices/`.

### 4. Rodar os Serviços
Gateway:
```bash
uv run uvicorn gateway:app --host 0.0.0.0 --port 8000
```
Worker:
```bash
uv run faststream run worker:app
```
