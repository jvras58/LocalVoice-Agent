"""Painel operacional/debug do LocalVoice (Streamlit).

Permite conferir o preflight de capacidades e enviar comandos de texto ao
gateway, reproduzindo o áudio devolvido pelo worker.

Executar com:

    streamlit run src/ui/app.py
"""

import base64
import uuid

import streamlit as st

from src.core.capabilities import describe_report, resolve_capabilities
from src.core.config import get_settings
from src.ui.components import send_command

settings = get_settings()

st.set_page_config(page_title="LocalVoice — Painel", page_icon="🎙️")
st.title("🎙️ LocalVoice — Painel")

with st.sidebar:
    st.header("Configuração")
    gateway_url = st.text_input(
        "URL do gateway",
        value=f"http://localhost:{settings.gateway_port}",
    )
    st.caption(f"Modelo Ollama: `{settings.ollama_model}`")

    st.header("Preflight")
    for line in describe_report(resolve_capabilities(settings)):
        st.write(f"- {line}")

if "session_id" not in st.session_state:
    st.session_state.session_id = f"panel-{uuid.uuid4()}"

st.caption(f"Sessão: `{st.session_state.session_id}`")

text = st.text_area("Comando de texto", placeholder="Digite o que enviar ao agente…")

if st.button("Enviar", type="primary", disabled=not text.strip()):
    with st.spinner("Aguardando resposta do worker…"):
        try:
            response = send_command(
                gateway_url, st.session_state.session_id, text.strip()
            )
        except TimeoutError:
            st.error("Tempo esgotado sem resposta. O worker está rodando?")
        except (ConnectionError, OSError) as error:
            st.error(f"Falha ao conectar ao gateway: {error}")
        else:
            st.subheader("Resposta")
            st.write(response.reply_text)
            st.audio(
                base64.b64decode(response.audio_buffer_b64),
                format="audio/wav",
            )
