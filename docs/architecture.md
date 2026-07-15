# Arquitetura — LocalVoice Agent

## Princípios

O processamento pesado fica no PC. O navegador captura a fala, envia a
transcrição e reproduz o áudio. Gateway e worker permanecem desacoplados pelo
Redis.

## Topologia

```text
Navegador -> WebSocket -> Gateway -> Redis -> Worker
                                            |-- Agno Team
                                            |   |-- Conversação
                                            |   `-- Sistema + ferramentas
                                            |-- SQLite (sessões)
                                            `-- Piper TTS
```

## Camadas

- **Cliente (`client/`)**: Web Speech API, histórico visual e reprodução WAV.
- **Gateway (`src/gateway/`)**: `app.py` compõe as dependências, `api.py` declara
  as rotas e os arquivos estáticos, e `controller.py` coordena WebSockets e
  publicação no Redis.
- **Broker**: canais `voice_commands` e `agent_responses`.
- **Worker (`src/worker/`)**: `app.py` registra hooks e subscriber; o
  `controller.py` executa a equipe, normaliza a saída, chama o Piper e publica a
  resposta.
- **Equipe (`src/agents/`)**: líder com memória SQLite por `session_id`, membro
  de conversação e membro de sistema com ferramentas explicitamente permitidas.

## Fluxo de resposta

1. O navegador transcreve a fala e envia `text` com um `session_id` estável.
2. O gateway publica um `VoiceCommand`.
3. O worker executa a equipe usando o mesmo `session_id`.
4. O líder delega ao membro de conversação ou ao membro de sistema.
5. O membro de sistema pode chamar uma ferramenta autorizada.
6. `normalize_for_speech` remove Markdown e símbolos inadequados ao TTS.
7. O Piper sintetiza exatamente o texto normalizado.
8. Texto e áudio retornam para a sessão de origem.

## Ferramentas atuais

- `get_current_datetime`: consulta data, hora e fuso da máquina.
- `get_runtime_status`: consulta as capacidades locais do LocalVoice.

As ferramentas atuais pertencem apenas ao agente de sistema e são somente
leitura. Ferramentas futuras que alterem arquivos, lembretes ou serviços devem
exigir confirmação e ter parâmetros validados; nenhum agente deve receber
acesso irrestrito ao shell.

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
