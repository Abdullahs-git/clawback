# AMD Infrastructure & vLLM Serving Setup Guide

This guide documents the setup for serving Google Gemma open models on AMD ROCm infrastructure (AMD Developer Cloud, Instinct MI200/MI300 series GPUs, or AMD AI Notebooks).

## 1. Pinned Model Architecture
- **Model Name:** `google/gemma-2-9b-it` (Gemma 2 9B Instruction Tuned)
- **Serving Engine:** vLLM (OpenAI-compatible `/v1/chat/completions` server) with ROCm 6.2+
- **Inference Mode:** Open weights hosted on AMD GPU infrastructure
- **Fallback / Resilience:** Certified `replay` mode (`LLM_MODE=replay`) serving real AMD inference logs

---

## 2. Serving via Docker on AMD ROCm (Verified Commands)

AMD provides official ROCm-optimized vLLM containers via Docker Hub (`rocm/vllm`).

### Prerequisites
- Host machine with AMD Instinct GPU (e.g. MI210, MI250, MI300X, or Radeon Pro)
- ROCm drivers installed (ROCm 6.1 or 6.2)
- Docker with AMD GPU device passthrough (`--device=/dev/kfd --device=/dev/dri`)

### Launch vLLM Serving Container on AMD GPU

```bash
# Pull official AMD ROCm vLLM container
docker pull rocm/vllm:latest

# Run vLLM with Gemma 2 on AMD ROCm
docker run -d \
  --name gemma-amd-vllm \
  --network host \
  --device=/dev/kfd \
  --device=/dev/dri \
  --ipc=host \
  --shm-size=16g \
  -e HF_TOKEN="your_huggingface_token" \
  rocm/vllm:latest \
  --model google/gemma-2-9b-it \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --trust-remote-code
```

### Health Verification

```bash
# Check model loaded
curl http://localhost:8000/v1/models

# Test test prompt
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-2-9b-it",
    "messages": [{"role": "user", "content": "Extract rates from carrier contract."}],
    "temperature": 0.1
  }'
```

---

## 3. Serving via AMD AI Notebooks (Token Factory)

If using the AMD Token Factory managed endpoint (`notebooks.amd.com`):
1. Sign in to [AMD AI Notebooks](https://notebooks.amd.com/tokenfactory).
2. Generate an API token.
3. Configure `.env` in Clawback:
   ```env
   LLM_MODE=live
   LLM_BASE_URL=https://notebooks.amd.com/tokenfactory/v1
   LLM_API_KEY=<your_amd_token>
   LLM_MODEL=google/gemma-2-9b-it
   ```

---

## 4. Operational Telemetry & AMD Panel

Clawback tracks live GPU inference metrics on every invocation:
- **`latency_ms`**: End-to-end network & execution latency
- **`tokens_per_second`**: Real-time throughput
- **`prompt_tokens`** & **`completion_tokens`**: Token accounting
- **Fallback Handling**: If the AMD host encounters network timeouts, Clawback gracefully activates replay cache without failing user operations.
