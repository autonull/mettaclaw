import os
import sys
import json
import logging
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

try:
    import litellm
    from litellm import completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("litellm not installed - LLM calls will fail")

litellm.drop_params = True
litellm.set_verbose = False

DEFAULT_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
DEFAULT_EMBED_DIM = 768

def _clean(text):
    if text:
        return text.replace("_quote_", '"').replace("_apostrophe_", "'")
    return ""

def _chat(model, content, max_tokens=6000):
    if not LITELLM_AVAILABLE:
        return "Error: litellm not installed"
    try:
        resp = completion(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens
        )
        return _clean(resp.choices[0].message.content)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"LLM Error: {str(e)}"

def useGPTEmbedding(text):
    """Return a list of floats embedding for the given text."""
    if not isinstance(text, str):
        text = str(text) if text else ""
    
    if not text:
        return _zero_embedding(DEFAULT_EMBED_DIM)

    ollama_base = os.environ.get("OLLAMA_API_BASE", "").rstrip("/")
    if ollama_base:
        try:
            data = json.dumps({"model": DEFAULT_EMBED_MODEL, "prompt": text}).encode()
            req = urllib.request.Request(
                f"{ollama_base}/api/embeddings",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                return result.get("embedding", _zero_embedding(DEFAULT_EMBED_DIM))
        except Exception as e:
            logger.warning(f"Ollama embedding failed: {e}")

    if not LITELLM_AVAILABLE:
        logger.warning("litellm unavailable, returning zero embedding")
        return _zero_embedding(1536)

    try:
        resp = litellm.embedding(
            model="text-embedding-3-small",
            input=[text],
        )
        return resp.data[0]["embedding"]
    except Exception as e:
        logger.error(f"LiteLLM embedding failed: {e}")
        return _zero_embedding(1536)

def _zero_embedding(dim):
    """Fallback: return zero vector when embedding fails."""
    return [0.0] * dim

def _check_chromadb():
    """Check if ChromaDB is available."""
    try:
        import lib_chromadb
        return True
    except ImportError:
        logger.warning("lib_chromadb not available - memory functions disabled")
        return False

def _chromadb_init_ok():
    """Check if ChromaDB collection is initialized."""
    if not _check_chromadb():
        return False
    try:
        import lib_chromadb
        return lib_chromadb.is_initialized()
    except Exception as e:
        logger.warning(f"ChromaDB not initialized: {e}")
        return False

def remember(text, time_str):
    """Embed text and store in ChromaDB."""
    if not text or not isinstance(text, str):
        return "Error: empty text"
    if not time_str:
        time_str = "unknown"
    
    if not _check_chromadb():
        return "Error: ChromaDB not available"
    
    try:
        import lib_chromadb
        embedding = useGPTEmbedding(text)
        item_id = lib_chromadb.remember(text, embedding, time_str)
        return item_id or "Error: failed to store"
    except Exception as e:
        logger.error(f"Remember failed: {e}")
        return f"Remember error: {e}"

def query_memories(query_text, k=20):
    """Embed query text and retrieve similar memories from ChromaDB."""
    if not query_text or not isinstance(query_text, str):
        return "No memories found: empty query"
    
    if not _check_chromadb():
        return "No memories yet (ChromaDB not available)"
    
    if not _chromadb_init_ok():
        return "No memories stored yet"

    try:
        import lib_chromadb
        k = int(k) if k else 20
        embedding = useGPTEmbedding(query_text)
        results = lib_chromadb.query(embedding, k)
        if not results:
            return f"No memories found for: {query_text}"
        parts = []
        for t, content in results:
            if t:
                parts.append(f"[{t}] {content}")
            else:
                parts.append(content)
        return " | ".join(parts)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return f"No memories found (error: {str(e)[:50]})"

def useMiniMax(content):
    if not LITELLM_AVAILABLE:
        return "Error: litellm not installed"
    model = os.environ.get('MINIMAX_MODEL', 'openai/minimax/minimax-m2.5')
    return _chat(model=model, content=content, max_tokens=6000)

def useClaude(content):
    if not LITELLM_AVAILABLE:
        return "Error: litellm not installed"
    model = os.environ.get('CLAUDE_MODEL', 'anthropic/claude-opus-4-20250514')
    return _chat(model=model, content=content, max_tokens=8192)

def useGPT(model, max_tokens, reasoning_mode, content):
    return _chat(model=model, content=content, max_tokens=max_tokens)

def useLLM(model, content, max_tokens=6000, reasoning_mode=None):
    # Handle Ollama model names - convert to proper litellm format
    if model and '/' not in model:
        model = f"ollama/{model}"
    return _chat(model=model, content=content, max_tokens=max_tokens)
