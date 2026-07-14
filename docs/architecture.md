# Arquitetura — LocalVoice Agent

## Princípios

O processamento pesado (LLM + TTS) fica no backend (PC). O celular é apenas um
terminal de captação (STT no navegador) e reprodução (Web Audio API). A
comunicação entre gateway e worker é assíncrona e orientada a eventos, mediada
pelo Redis.

## Topologia

```
Navegador Mobile            Gateway (FastAPI)         Redis            Worker (FastStream)
  Web Speech API  --texto-->  WebSocket  --publish-->  voice_commands  --> Agno Team (Ollama)
                                 ^                                                  |
                                 |                                             Piper TTS (.wav)
  Web Audio API  <--áudio----  WebSocket  <--consume--  agent_responses <--publish--
```

## Camadas

- **Cliente (`client/index.html`)** — captura voz, transcreve com a Web Speech
  API, envia `{"text": ...}` pelo WebSocket e reproduz o WAV recebido em Base64
  via `AudioContext`.
- **Gateway (`src/gateway/`)** — FastAPI com o plugin `RedisRouter` do
  FastStream. O endpoint `/ws/{session_id}` publica `VoiceCommand` em
  `voice_commands`; o subscriber de `agent_responses` injeta cada `AgentResponse`
  no WebSocket da sessão. `ConnectionRegistry` mapeia `session_id` → WebSocket.
- **Broker (Redis)** — filas `voice_commands` (texto) e `agent_responses`
  (texto + áudio Base64).
- **Worker (`src/worker/`)** — FastStream consome `voice_commands`, executa a
  equipe Agno (`src/agents/`) sobre o Ollama local, sintetiza o áudio com o
  Piper (`src/tools/tts.py`) fora do event loop (`asyncio.to_thread`) e publica
  `AgentResponse`.

## Contratos (`src/core/schemas.py`)

- `VoiceCommand`: `session_id`, `text`.
- `AgentResponse`: `session_id`, `reply_text`, `audio_buffer_b64`.

## Fluxo de dados

1. Usuário fala; o navegador transcreve e envia texto pelo WebSocket.
2. Gateway publica `VoiceCommand` em `voice_commands`.
3. Worker consome, a equipe Agno gera a resposta textual.
4. O texto vai ao Piper, que gera o buffer WAV em memória.
5. Worker publica `AgentResponse` (texto + WAV Base64) em `agent_responses`.
6. Gateway consome e envia pelo WebSocket para a sessão de origem.
7. O navegador decodifica o Base64 e reproduz o áudio.

## Decisões e limites

- **Piper em processo** via `PiperVoice.load` + `synthesize_wav`, com o WAV
  montado em memória (`io.BytesIO`). A importação do runtime ONNX é adiada para
  dentro de `load_piper_voice`, mantendo `src/tools/tts.py` testável sem o
  pacote pesado (contrato `SynthesisVoice`).
- **Equipe mínima e extensível**: um assistente sob um líder. Novos membros e
  ferramentas entram em `src/agents/` sem alterar gateway ou worker.
- **Preflight** (`src/core/capabilities.py`): checa Ollama e a presença da voz
  do Piper na inicialização do worker e pelo comando `localvoice check`.
- **Painel Streamlit** fala com o gateway pelo mesmo contrato WebSocket do
  cliente, evitando acoplar-se ao formato interno do broker.
- Não há persistência nem autenticação nesta versão; o `pgvector` do
  `docker-compose.yml` é provisionado para memória/conhecimento futuros do Agno.
