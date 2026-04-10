#!/bin/sh
# Inside-container runner — invokes PeTTa on a .metta file
# Usage: ./container_run.sh [script.metta]
set -e

cd /opt/PeTTa

# Copy MeTTaClaw files into working dir if not already present
METTACLAW_DIR="/opt/PeTTa/repos/mettaclaw"
if [ -d "$METTACLAW_DIR" ]; then
    cp "$METTACLAW_DIR/run.metta" . 2>/dev/null || true
    cp "$METTACLAW_DIR/lib_mettaclaw.metta" . 2>/dev/null || true
    cp "$METTACLAW_DIR/lib_nal.metta" . 2>/dev/null || true
    cp -r "$METTACLAW_DIR/src" . 2>/dev/null || true
    # memory/ stays from the cloned repo (writable) — don't overwrite
    if [ ! -d "memory" ]; then
        cp -r "$METTACLAW_DIR/memory" . 2>/dev/null || true
    fi
fi

SCRIPT="${1:-run.metta}"

if [ ! -f "$SCRIPT" ]; then
    echo "Error: Script not found: $SCRIPT" >&2
    exit 1
fi

# ── Detect LLM provider from env vars ──────────────────────────────────────
PROVIDER_INIT=""
if [ -n "${OLLAMA_API_BASE:-}" ]; then
PROVIDER_MODEL="${OLLAMA_MODEL:-llama3}"
PROVIDER_INIT="(= (provider) Ollama)
(= (LLM) ollama/${PROVIDER_MODEL})"
elif [ -n "${OPENAI_API_KEY:-}" ]; then
    PROVIDER_INIT="(= (provider) OpenAI)
(= (LLM) gpt-4o)"
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    PROVIDER_INIT="(= (provider) Anthropic)
(= (LLM) claude-sonnet-4-20250514)"
elif [ -n "${OPENROUTER_API_KEY:-}" ]; then
    PROVIDER_INIT="(= (provider) OpenAI)
(= (LLM) openrouter/auto)"
elif [ -n "${GROQ_API_KEY:-}" ]; then
    PROVIDER_MODEL="${OLLAMA_MODEL:-llama-3.3-70b-versatile}"
    PROVIDER_INIT="(= (provider) OpenAI)
(= (LLM) groq/$PROVIDER_MODEL)"
fi

# Write provider config if detected
if [ -n "$PROVIDER_INIT" ]; then
    printf '%s\n' "$PROVIDER_INIT" > /opt/PeTTa/provider_init.metta
    echo "Provider auto-detected:"
    printf '%s\n' "$PROVIDER_INIT" | head -1
fi

# ── Run via agent_run.py (filtering, logging, dry-run support) ─────────────
echo "Running: $SCRIPT"
exec python3 /opt/PeTTa/agent_run.py "$SCRIPT"
