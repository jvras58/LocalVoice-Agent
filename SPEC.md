# Especificação da Arquitetura: LocalVoice Agent (Piper TTS)

## 1. Visão Arquitetural
A arquitetura foi refinada para centralizar o processamento pesado no backend (PC), utilizando o **Piper TTS** para geração de vozes neurais locais. O frontend (Mobile) agora atua primariamente como um cliente de *streaming* de áudio, garantindo alta qualidade de voz sem onerar o dispositivo móvel.

## 2. Topologia do Sistema Atualizada

### Camada 1: Client Edge (Navegador Mobile)
- **Entrada (Microfone):** Utiliza a Web Speech API para transcrição STT leve no aparelho.
- **Saída (Alto-falante):** Recebe pacotes binários (ou Base64) de áudio via WebSocket e utiliza a Web Audio API (`AudioContext`) para dar play imediato no áudio gerado pelo servidor, sem necessidade de baixar arquivos inteiros antes de iniciar.

### Camada 2: API Gateway (FastAPI)
- Gerencia WebSockets bidirecionais.
- Encaminha texto STT para o Redis.
- Escuta a fila de respostas. Quando recebe um payload contendo o buffer de áudio (gerado pelo Piper), injeta imediatamente no WebSocket para o cliente.

### Camada 3: Message Broker (Redis)
- Mantém as filas: `voice_commands` (texto) e `agent_responses` (metadados + payload de áudio binário).

### Camada 4: Agno Worker (FastStream + Ollama + Piper)
- Processa o texto via equipe de Agentes Agno.
- Uma vez obtida a resposta textual final do LLM, o texto é passado localmente para a engine do Piper TTS.
- O Piper sintetiza o áudio (`.wav`) em memória ultrarrápida.
- O Worker empacota a resposta textual e o buffer de áudio e publica na fila `agent_responses`.

## 3. O Fluxo de Dados (Data Flow)
1. Usuário fala -> Celular transcreve para texto -> Envia texto via WS.
2. Gateway recebe texto -> Publica Evento `VoiceCommand` no Redis.
3. Worker consome Evento -> Agno processa com ferramentas locais -> Gera Resposta Texto.
4. Worker passa Resposta Texto para `piper-tts`.
5. Piper gera Buffer WAV.
6. Worker publica Evento `VoiceResponse` (composto de Texto + Buffer Base64) no Redis.
7. Gateway consome Evento -> Envia via WS para Celular.
8. Celular reproduz áudio no alto-falante.

## 4. Estrutura de Mensageria (Pydantic)
```python
from pydantic import BaseModel, Field

class VoiceCommand(BaseModel):
    session_id: str
    text: str = Field(..., description="Texto transcrito do áudio")

class AgentResponse(BaseModel):
    session_id: str
    reply_text: str
    audio_buffer_b64: str = Field(..., description="Buffer de áudio WAV em Base64 gerado pelo Piper")
```
