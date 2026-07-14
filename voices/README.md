# Vozes do Piper TTS

Coloque aqui os modelos de voz do Piper (`.onnx`) e seus arquivos de
configuração (`.onnx.json`). Eles são ignorados pelo Git (ver `.gitignore`).

## Baixar uma voz em português

```bash
python -m piper.download_voices pt_BR-faber-medium
```

Isso cria, neste diretório:

- `pt_BR-faber-medium.onnx`
- `pt_BR-faber-medium.onnx.json`

Ajuste `PIPER_VOICE_PATH` no `.env` caso use outra voz. Quando o
arquivo de configuração segue o padrão `<modelo>.onnx.json`, ele é descoberto
automaticamente.

Catálogo de vozes: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md>
