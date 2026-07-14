"use strict";

const statusElement = document.getElementById("status");
const statusTextElement = document.getElementById("status-text");

const conversationElement = document.getElementById("conversation");
const emptyStateElement = document.getElementById("empty-state");
const typingIndicatorElement = document.getElementById("typing-indicator");

const microphoneButton = document.getElementById("mic");
const microphoneLabelElement = document.getElementById("mic-label");

const voiceTitleElement = document.getElementById("voice-title");
const voiceDescriptionElement = document.getElementById(
  "voice-description"
);

const audioVisualizerElement = document.getElementById(
  "audio-visualizer"
);

const SpeechRecognition =
  window.SpeechRecognition ||
  window.webkitSpeechRecognition;

const AudioContextClass =
  window.AudioContext ||
  window.webkitAudioContext;

let socket = null;
let reconnectTimeout = null;
let audioContext = null;
let recognition = null;

let listening = false;
let startingRecognition = false;
let waitingForResponse = false;

function createSessionId() {
  if (
    window.crypto &&
    typeof window.crypto.randomUUID === "function"
  ) {
    return window.crypto.randomUUID();
  }

  const randomPart = Math.random()
    .toString(36)
    .slice(2);

  const timestampPart = Date.now()
    .toString(36);

  return `sess-${randomPart}-${timestampPart}`;
}

const sessionId = createSessionId();

const websocketProtocol =
  window.location.protocol === "https:"
    ? "wss"
    : "ws";

const websocketUrl =
  `${websocketProtocol}://${window.location.host}/ws/${sessionId}`;

function formatTime(date = new Date()) {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function scrollConversationToBottom() {
  window.requestAnimationFrame(() => {
    conversationElement.scrollTop =
      conversationElement.scrollHeight;
  });
}

function removeEmptyState() {
  if (emptyStateElement?.isConnected) {
    emptyStateElement.remove();
  }
}

function setConnectionStatus(text, state) {
  statusTextElement.textContent = text;
  statusElement.className = `status-pill ${state}`;
}

function setVoiceDescription(title, description) {
  voiceTitleElement.textContent = title;
  voiceDescriptionElement.textContent = description;
}

function updateDefaultVoiceDescription() {
  if (listening) {
    return;
  }

  if (waitingForResponse) {
    setVoiceDescription(
      "Processando sua solicitação",
      "O assistente está preparando uma resposta"
    );

    return;
  }

  setVoiceDescription(
    "Pronto para ouvir",
    "Clique no botão e comece a falar"
  );
}

function setTypingIndicator(visible) {
  waitingForResponse = visible;

  typingIndicatorElement.classList.toggle(
    "visible",
    visible
  );

  updateDefaultVoiceDescription();

  if (visible) {
    scrollConversationToBottom();
  }
}

function createSystemMessage(text, type = "system") {
  removeEmptyState();

  const messageElement = document.createElement("div");

  messageElement.className =
    type === "error"
      ? "system-message error"
      : "system-message";

  messageElement.textContent = text;

  conversationElement.insertBefore(
    messageElement,
    typingIndicatorElement
  );

  scrollConversationToBottom();
}

function createChatMessage(text, sender) {
  removeEmptyState();

  const messageRow = document.createElement("article");
  messageRow.className = `message-row ${sender}`;

  const avatarElement = document.createElement("div");
  avatarElement.className =
    sender === "agent"
      ? "message-avatar agent-avatar"
      : "message-avatar";

  avatarElement.setAttribute("aria-hidden", "true");
  avatarElement.textContent =
    sender === "agent" ? "LV" : "EU";

  const messageContent = document.createElement("div");
  messageContent.className = "message-content";

  const messageBubble = document.createElement("div");
  messageBubble.className = "message-bubble";
  messageBubble.textContent = text;

  const timeElement = document.createElement("time");
  timeElement.className = "message-time";
  timeElement.dateTime = new Date().toISOString();
  timeElement.textContent = formatTime();

  messageContent.appendChild(messageBubble);
  messageContent.appendChild(timeElement);

  if (sender === "user") {
    messageRow.appendChild(messageContent);
  } else {
    messageRow.appendChild(avatarElement);
    messageRow.appendChild(messageContent);
  }

  conversationElement.insertBefore(
    messageRow,
    typingIndicatorElement
  );

  scrollConversationToBottom();
}

function connectWebSocket() {
  window.clearTimeout(reconnectTimeout);

  setConnectionStatus(
    "Conectando",
    "connecting"
  );

  try {
    socket = new WebSocket(websocketUrl);
  } catch (error) {
    console.error(
      "Erro ao criar WebSocket:",
      error
    );

    setConnectionStatus(
      "Erro de conexão",
      "disconnected"
    );

    reconnectTimeout = window.setTimeout(
      connectWebSocket,
      1500
    );

    return;
  }

  socket.addEventListener("open", () => {
    setConnectionStatus(
      "Conectado",
      "connected"
    );
  });

  socket.addEventListener("close", () => {
    setTypingIndicator(false);

    setConnectionStatus(
      "Reconectando",
      "connecting"
    );

    reconnectTimeout = window.setTimeout(
      connectWebSocket,
      1500
    );
  });

  socket.addEventListener("error", (event) => {
    console.error(
      "Erro no WebSocket:",
      event
    );

    setConnectionStatus(
      "Erro de conexão",
      "disconnected"
    );
  });

  socket.addEventListener(
    "message",
    handleWebSocketMessage
  );
}

async function handleWebSocketMessage(event) {
  try {
    const data = JSON.parse(event.data);

    setTypingIndicator(false);

    if (data.reply_text) {
      createChatMessage(
        data.reply_text,
        "agent"
      );
    }

    if (data.audio_buffer_b64) {
      await playBase64Audio(
        data.audio_buffer_b64
      );
    }
  } catch (error) {
    console.error(
      "Erro ao processar resposta:",
      error
    );

    setTypingIndicator(false);

    createSystemMessage(
      "Não foi possível processar a resposta do servidor.",
      "error"
    );
  }
}

function base64ToArrayBuffer(base64) {
  const binaryString = window.atob(base64);

  const bytes = new Uint8Array(
    binaryString.length
  );

  for (
    let index = 0;
    index < binaryString.length;
    index += 1
  ) {
    bytes[index] =
      binaryString.charCodeAt(index);
  }

  return bytes.buffer;
}

async function getAudioContext() {
  if (!AudioContextClass) {
    throw new Error(
      "AudioContext não é suportado neste navegador."
    );
  }

  if (!audioContext) {
    audioContext = new AudioContextClass();
  }

  if (audioContext.state === "suspended") {
    await audioContext.resume();
  }

  return audioContext;
}

async function playBase64Audio(base64Audio) {
  try {
    const context = await getAudioContext();

    const arrayBuffer =
      base64ToArrayBuffer(base64Audio);

    const decodedAudio =
      await context.decodeAudioData(arrayBuffer);

    const source =
      context.createBufferSource();

    source.buffer = decodedAudio;
    source.connect(context.destination);
    source.start();
  } catch (error) {
    console.error(
      "Erro ao reproduzir áudio:",
      error
    );

    createSystemMessage(
      "A resposta foi recebida, mas o áudio não pôde ser reproduzido.",
      "error"
    );
  }
}

function updateListeningInterface(isListening) {
  listening = isListening;

  microphoneButton.classList.toggle(
    "listening",
    isListening
  );

  microphoneButton.setAttribute(
    "aria-pressed",
    String(isListening)
  );

  audioVisualizerElement.classList.toggle(
    "active",
    isListening
  );

  if (isListening) {
    microphoneButton.setAttribute(
      "aria-label",
      "Parar reconhecimento de voz"
    );

    microphoneButton.title =
      "Clique para parar";

    microphoneLabelElement.textContent =
      "OUVINDO...";

    setVoiceDescription(
      "Estou ouvindo",
      "Fale naturalmente e toque novamente para parar"
    );

    return;
  }

  microphoneButton.setAttribute(
    "aria-label",
    "Iniciar reconhecimento de voz"
  );

  microphoneButton.title =
    "Clique para falar";

  microphoneLabelElement.textContent =
    "TOQUE PARA FALAR";

  updateDefaultVoiceDescription();
}

function sendTranscript(transcript) {
  if (
    !socket ||
    socket.readyState !== WebSocket.OPEN
  ) {
    createSystemMessage(
      "Não foi possível enviar a mensagem porque o servidor está desconectado.",
      "error"
    );

    return;
  }

  createChatMessage(
    transcript,
    "user"
  );

  setTypingIndicator(true);

  socket.send(
    JSON.stringify({
      text: transcript
    })
  );
}

function getSpeechRecognitionErrorMessage(errorCode) {
  const messages = {
    "audio-capture":
      "Não foi possível acessar o microfone.",

    "not-allowed":
      "O acesso ao microfone não foi autorizado.",

    "service-not-allowed":
      "O serviço de reconhecimento de voz não está disponível.",

    network:
      "O reconhecimento de voz encontrou um erro de rede.",

    "language-not-supported":
      "O idioma selecionado não é suportado pelo navegador."
  };

  return (
    messages[errorCode] ||
    `Erro no reconhecimento de voz: ${errorCode}.`
  );
}

function configureSpeechRecognition() {
  if (!SpeechRecognition) {
    microphoneButton.disabled = true;

    setVoiceDescription(
      "Navegador incompatível",
      "O reconhecimento de voz não está disponível"
    );

    createSystemMessage(
      "Este navegador não oferece suporte ao reconhecimento de voz. Para a demonstração, utilize uma versão recente do Google Chrome ou Microsoft Edge.",
      "error"
    );

    return;
  }

  recognition = new SpeechRecognition();

  recognition.lang = "pt-BR";
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;

  recognition.addEventListener("start", () => {
    startingRecognition = false;
    updateListeningInterface(true);
  });

  recognition.addEventListener("end", () => {
    startingRecognition = false;
    updateListeningInterface(false);
  });

  recognition.addEventListener(
    "result",
    (event) => {
      const transcript =
        event.results?.[0]?.[0]?.transcript?.trim();

      if (!transcript) {
        createSystemMessage(
          "Não foi possível compreender o áudio."
        );

        return;
      }

      sendTranscript(transcript);
    }
  );

  recognition.addEventListener(
    "error",
    (event) => {
      startingRecognition = false;
      updateListeningInterface(false);

      if (event.error === "aborted") {
        return;
      }

      if (event.error === "no-speech") {
        createSystemMessage(
          "Nenhuma fala foi identificada. Tente novamente."
        );

        return;
      }

      createSystemMessage(
        getSpeechRecognitionErrorMessage(
          event.error
        ),
        "error"
      );
    }
  );
}

async function handleMicrophoneClick() {
  if (
    !recognition ||
    startingRecognition
  ) {
    return;
  }

  try {
    await getAudioContext();

    if (listening) {
      recognition.stop();
      return;
    }

    startingRecognition = true;
    recognition.start();
  } catch (error) {
    startingRecognition = false;

    console.error(
      "Erro ao iniciar reconhecimento:",
      error
    );

    createSystemMessage(
      "Não foi possível iniciar o reconhecimento de voz.",
      "error"
    );
  }
}

function showSecurityContextWarning() {
  if (window.isSecureContext) {
    return;
  }

  createSystemMessage(
    "O reconhecimento de voz exige uma conexão segura. No computador, utilize localhost. Em outros dispositivos, disponibilize a aplicação por HTTPS."
  );
}

microphoneButton.addEventListener(
  "click",
  handleMicrophoneClick
);

window.addEventListener("beforeunload", () => {
  window.clearTimeout(reconnectTimeout);

  if (socket) {
    socket.close();
  }

  if (recognition && listening) {
    recognition.abort();
  }

  if (audioContext) {
    audioContext.close();
  }
});

configureSpeechRecognition();
showSecurityContextWarning();
connectWebSocket();