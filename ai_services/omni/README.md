# Omni Voice Service (servidor externo)

Native speech-to-speech tutoring powered by **Qwen2.5-Omni-7B**.

Este serviço roda **fora do docker-compose do projeto**, da mesma forma que o LLM local
(llamacpp/vLLM). O projeto LingoAI conecta nele via `OMNI_API_URL`, exatamente como
conecta ao LLM via `LLM_BASE_URL`.

This service accepts raw audio from the user, processes it through the Qwen2.5-Omni model,
and returns a spoken audio response together with structured pronunciation feedback — without
any intermediate text transcription step.

---

## Hardware Requirements

| Config | VRAM / RAM | Notes |
|--------|-----------|-------|
| GPU (CUDA) | ~18 GB VRAM | float16, recommended |
| CPU only | ~16 GB RAM | float32, slow (30–120 s/turn) |

---

## Downloading Model Weights

Weights are **not bundled** in the Docker image. You must download them manually:

```bash
pip install huggingface-hub

huggingface-cli download Qwen/Qwen2.5-Omni-7B \
    --local-dir ./ai_services/omni/models/Qwen2.5-Omni-7B
```

The directory structure after download should be:

```
ai_services/omni/models/Qwen2.5-Omni-7B/
├── config.json
├── tokenizer.json
├── model-00001-of-XXXXX.safetensors
└── ...
```

---

## Iniciando o servidor externamente

```bash
# Na pasta ai_services/omni/:
pip install -r requirements.txt

# Com pesos já baixados em ./models/Qwen2.5-Omni-7B/:
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

Ou via Docker standalone (sem fazer parte do compose do projeto):
```bash
docker build -t lingo-omni .
docker run -p 8003:8003 -v $(pwd)/models:/app/models:ro lingo-omni
```

Health check:
```bash
curl http://localhost:8003/health
# { "status": "ok", "model_loaded": true }
```

`model_loaded` é `false` enquanto os pesos carregam (tipicamente 2–5 min na primeira vez).

## Conectando ao projeto LingoAI

No `.env` do projeto (ou nas variáveis de ambiente do backend):

```env
OMNI_ENABLED=true
OMNI_API_URL=http://host.docker.internal:8003   # mesma máquina host
# ou
OMNI_API_URL=http://192.168.x.x:8003            # outro servidor na rede
```

O backend do LingoAI conectará automaticamente — mesmo padrão do `LLM_BASE_URL`.

---

## Environment Variables (set in the backend container)

| Variable | Default | Description |
|----------|---------|-------------|
| `OMNI_ENABLED` | `false` | Master switch; set `true` to activate Voice Tutor mode |
| `OMNI_API_URL` | `http://omni:8003` | URL the backend uses to reach this service |
| `OMNI_TIMEOUT_SECONDS` | `30` | Per-request timeout |
| `OMNI_MAX_AUDIO_SECONDS` | `60` | Maximum accepted audio duration |

---

## Validation

See `specs/007-omni-voice-channel/quickstart.md` for end-to-end validation scenarios.
