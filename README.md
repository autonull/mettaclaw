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
| `./run.sh` | Run `run.metta` (filtered output) |
| `./run.sh build` | Build the container image |
| `./run.sh run [script]` | Run a specific script |
| `./run.sh verbose [script]` | Run with full MeTTa/Prolog trace |
| `./run.sh dry-run [script]` | Validate setup without LLM calls |
| `./run.sh shell` | Open a shell in the container |
| `./run.sh reset-history` | Clear memory/history.metta |
| `./run.sh clean` | Remove the image |
| `./run.sh status` | Check build status and config |
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

# Validate setup before running (no LLM calls)
OLLAMA_API_BASE="http://localhost:11434" ./run.sh dry-run

# Full trace output for debugging
./run.sh verbose

# Debug shell inside container
./run.sh shell

# Clear agent history
./run.sh reset-history

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
                               agent_run.py  (filters output, writes agent.log)
                                    ↓
                               run.metta → PeTTa → LLM
```

- **`run.sh`** (host) — builds and runs the container
- **`container_run.sh`** (inside) — detects provider from env vars
- **`agent_run.py`** (inside) — runs PeTTa with output filtering and structured logging
- **`lib_llm_ext.py`** — Python LLM interface using LiteLLM (supports all providers)

### Output Filtering

By default, MeTTa compilation noise (Prolog clauses, specialization traces) is suppressed. You see only:
- Iteration numbers
- Human messages received
- LLM prompts sent and responses
- Command results and errors

Use `./run.sh verbose` for the full trace.

### Structured Logging

Every run writes `/opt/PeTTa/agent.log` with JSON lines:
```json
{"t": 0.01, "event": "iteration", "k": 1, "loops": 50, "human_msg": ""}
{"t": 30.5, "event": "response", "text": "((query \"goals\"))"}
```

Copy it out after a run:
```bash
podman cp <container>:/opt/PeTTa/agent.log .
```

### Local Development

Local MeTTa files (`run.metta`, `lib_mettaclaw.metta`, `src/`) are mounted read-only into the container. The `memory/` directory is mounted read-write for history persistence. Edit files on your host and they're available on next run — no rebuild needed.

---

## Project Structure

| File | Purpose |
|------|---------|
| `run.sh` | Host-side runner (build, run, verbose, dry-run, shell, clean, status) |
| `run.py` | Python runner (local PeTTa invocation, outside container) |
| `container_run.sh` | Inside-container entrypoint (provider detection) |
| `agent_run.py` | Inside-container PeTTa wrapper (filtering, logging, dry-run) |
| `Dockerfile` | Container image definition |
| `lib_llm_ext.py` | Python LLM wrapper (LiteLLM, all providers) |
| `Makefile` | Shortcuts: `make build`, `make run`, `make dry-run` |
| `VERSION` | Current version (shown in status output) |
| `.env.example` | Configuration template |
| `.env` | Your config (gitignored) |
| `memory/prompt.txt` | Agent system prompt (edit locally, mounted into container) |
| `memory/history.metta` | Conversation history (persistent across runs) |

---

## License

[MIT](LICENSE)
