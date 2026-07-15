# Arquitetura — LocalVoice Agent

## Princípios

O processamento pesado fica no PC. O navegador captura a fala, envia a
transcrição e reproduz o áudio. Gateway e worker permanecem desacoplados pelo
Redis.

## Topologia

```text
Navegador -> WebSocket -> Gateway -> Redis -> Worker
                                            |-- Agno Agent + ferramentas
                                            |-- SQLite (sessões)
                                            `-- Piper TTS
```

## Camadas

- **Cliente (`client/`)**: Web Speech API, histórico visual e reprodução WAV.
- **Gateway (`src/gateway/`)**: serve HTML/CSS/JS, mantém WebSockets e encaminha
  mensagens entre o navegador e o Redis.
- **Broker**: canais `voice_commands` e `agent_responses`.
- **Worker (`src/worker/`)**: executa o agente, normaliza a saída e chama o Piper.
- **Agente (`src/agents/`)**: modelo Ollama, memória SQLite por `session_id` e
  ferramentas locais explicitamente permitidas.

## Fluxo de resposta

1. O navegador transcreve a fala e envia `text` com um `session_id` estável.
2. O gateway publica um `VoiceCommand`.
3. O worker executa o agente usando o mesmo `session_id`.
4. O agente pode responder diretamente ou chamar uma ferramenta autorizada.
5. `normalize_for_speech` remove Markdown e símbolos inadequados ao TTS.
6. O Piper sintetiza exatamente o texto normalizado.
7. Texto e áudio retornam para a sessão de origem.

## Ferramentas atuais

- `get_current_datetime`: consulta data, hora e fuso da máquina.
- `get_runtime_status`: consulta as capacidades locais do LocalVoice.

As ferramentas atuais são somente leitura. Ferramentas futuras que alterem
arquivos, lembretes ou serviços devem exigir confirmação e ter parâmetros
validados; o agente não deve receber acesso irrestrito ao shell.

## Qualidade da saída

O prompt solicita português brasileiro natural e texto sem formatação. Como um
modelo local pode desobedecer ao prompt, a normalização no worker é obrigatória
e funciona como última barreira antes da interface e do sintetizador.

## Persistência e limites

- O histórico é salvo em `data/localvoice.db` e separado pelo `session_id`.
- A quantidade de turnos enviada ao modelo é limitada por
  `LOCALVOICE_AGENT_HISTORY_RUNS`.
- Ainda não há autenticação; exponha o gateway apenas em redes confiáveis.
- O PostgreSQL/pgvector continua disponível para uma base RAG futura.
