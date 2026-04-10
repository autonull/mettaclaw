# MeTTaClaw

An agentic AI system in MeTTa with embedding-based long-term memory.

---

## Quick Start

### 1. Build the image

```bash
./run.sh build
```

### 2. Set your API key

On first run, a `.env` file is auto-created from the template. Edit it:

```bash
# OpenAI
OPENAI_API_KEY="sk-..."
```

Or pass it inline:

```bash
OPENAI_API_KEY="sk-..." ./run.sh
```

### 3. Run

```bash
./run.sh
```

That's it.

---

## LLM Providers

Pick **one** provider and set the corresponding environment variable. The system auto-detects which one to use.

### OpenAI (GPT-4, GPT-4o, o1, o3)

```bash
# .env
OPENAI_API_KEY="sk-..."
```

```bash
# Or inline
OPENAI_API_KEY="sk-..." ./run.sh
```

Get a key: https://platform.openai.com/api-keys

### Anthropic (Claude)

```bash
# .env
ANTHROPIC_API_KEY="sk-ant-..."
```

Get a key: https://console.anthropic.com/settings/keys

### Ollama (Local, Free)

Install [Ollama](https://ollama.ai), pull a model, then:

```bash
# .env
OLLAMA_API_BASE="http://localhost:11434"
OLLAMA_MODEL="llama3"
```

```bash
# Inline with a specific model (e.g., Qwen3 8B GGUF)
OLLAMA_API_BASE="http://localhost:11434" \
OLLAMA_MODEL="hf.co/bartowski/Qwen_Qwen3-8B-GGUF:Q6_K" \
./run.sh
```

```bash
# One-time setup
ollama pull llama3
```

### OpenRouter (100+ models, one API)

```bash
# .env
OPENROUTER_API_KEY="..."
```

Get a key: https://openrouter.ai/settings/keys

### Groq (Fast inference)

```bash
# .env
GROQ_API_KEY="gsk_..."
```

Get a key: https://console.groq.com/keys

### Other Providers

MeTTaClaw uses [LiteLLM](https://docs.litellm.ai/) under the hood, so it supports any provider LiteLLM supports: Together AI, Google Vertex AI, AWS Bedrock, Azure OpenAI, and custom OpenAI-compatible endpoints.

See `.env.example` for all available options.

---

## Commands

| Command | Description |
|---------|-------------|
| `./run.sh` | Run `run.metta` |
| `./run.sh build` | Build the container image |
| `./run.sh run [script.metta]` | Run a specific script |
| `./run.sh shell` | Open a shell in the container |
| `./run.sh clean` | Remove the image |
| `./run.sh status` | Check build status |
| `./run.sh -h` | Show help |

---

## Examples

```bash
# Build
./run.sh build

# Run with inline API key
OPENAI_API_KEY="sk-..." ./run.sh

# Run a specific script
OPENAI_API_KEY="sk-..." ./run.sh run myscript.metta

# Run with Ollama (local)
OLLAMA_API_BASE="http://localhost:11434" OLLAMA_MODEL="llama3" ./run.sh

# Run with Ollama and a GGUF model
OLLAMA_API_BASE="http://localhost:11434" \
OLLAMA_MODEL="hf.co/bartowski/Qwen_Qwen3-8B-GGUF:Q6_K" \
./run.sh

# Run with Claude
ANTHROPIC_API_KEY="sk-ant-..." ./run.sh

# Debug shell inside container
./run.sh shell

# Check status
./run.sh status
```

---

## How It Works

```
Host (run.sh)                    Container (/opt/PeTTa)
────────────                     ──────────────────────
./run.sh build        ──build──▶  PeTTa + MeTTaClaw cloned
./run.sh run          ──exec──▶   container_run.sh
                                    ↓
                               provider_init.metta  (auto-detected from env)
                                    ↓
                               run.metta → PeTTa → LLM
```

- **`run.sh`** (host) — builds and runs the container
- **`container_run.sh`** (inside) — detects provider from env vars, loads MeTTa, runs PeTTa
- **`lib_llm_ext.py`** — Python LLM interface using LiteLLM (supports all providers)

### Local Development

Local MeTTa files (`run.metta`, `lib_mettaclaw.metta`, `lib_nal.metta`, `lib_llm_ext.py`, `src/`) are mounted read-only into the container. The `memory/` directory remains writable inside. Edit files on your host and they're available on next run — no rebuild needed.

---

## Project Structure

| File | Purpose |
|------|---------|
| `run.sh` | Host-side runner (build, run, shell, clean) |
| `run.py` | Python runner (local PeTTa invocation) |
| `container_run.sh` | Inside-container runner (provider detection, PeTTa) |
| `Dockerfile` | Container image definition |
| `lib_llm_ext.py` | Python LLM wrapper (LiteLLM, all providers) |
| `.env.example` | Configuration template |
| `.env` | Your config (gitignored) |

---

## License

[MIT](LICENSE)
