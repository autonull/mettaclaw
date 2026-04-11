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
    LITELLM_AVAILABLE = True
    litellm.drop_params = True
    litellm.set_verbose = False
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("litellm not installed - LLM calls will fail")
    class DummyLiteLLM:
        def __init__(self):
            self.drop_params = True
            self.set_verbose = False
    litellm = DummyLiteLLM()

DEFAULT_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
DEFAULT_EMBED_DIM = 768

def _clean(text):
    if text:
        return text.replace("_quote_", '"').replace("_apostrophe_", "'")
    return ""

def _chat(model, content, max_tokens=6000):
    if not LITELLM_AVAILABLE:
        return "Error: litellm not installed"

    if model and '/' not in model and not model.startswith('ollama/'):
        if not model.startswith(('gpt-', 'claude-', 'o1-', 'o3-')):
             model = f"ollama/{model}"

    try:
        resp = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens
        )
        return _clean(resp.choices[0].message.content)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"LLM Error: {str(e)}"

def generate_response(model, content, max_tokens=6000):
    try:
        max_tokens = int(max_tokens)
    except (ValueError, TypeError):
        max_tokens = 6000
    return _chat(model=model, content=content, max_tokens=max_tokens)

def useGPTEmbedding(text):
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
    return [0.0] * dim

class MemoryManager:
    """Encapsulates ChromaDB operations and falls back gracefully when absent."""
    def __init__(self):
        self.chroma_available = False
        self.chroma_module = None
        try:
            import lib_chromadb
            self.chroma_module = lib_chromadb
            self.chroma_available = True
        except ImportError:
            logger.warning("lib_chromadb not available - memory functions disabled")

    def is_initialized(self):
        if not self.chroma_available:
            return False
        try:
            return self.chroma_module.is_initialized()
        except Exception as e:
            logger.warning(f"ChromaDB not initialized: {e}")
            return False

    def remember(self, text, time_str):
        if not text or not isinstance(text, str):
            return "Error: empty text"
        if not time_str:
            time_str = "unknown"

        if not self.chroma_available:
            return "Error: ChromaDB not available"

        try:
            embedding = useGPTEmbedding(text)
            item_id = self.chroma_module.remember(text, embedding, time_str)
            return item_id or "Error: failed to store"
        except Exception as e:
            logger.error(f"Remember failed: {e}")
            return f"Remember error: {e}"

    def query(self, query_text, k=20):
        if not query_text or not isinstance(query_text, str):
            return "No memories found: empty query"

        if not self.chroma_available:
            return "No memories yet (ChromaDB not available)"

        if not self.is_initialized():
            return "No memories stored yet"

        try:
            k = int(k) if k else 20
            embedding = useGPTEmbedding(query_text)
            results = self.chroma_module.query(embedding, k)
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

_memory_manager = MemoryManager()

def remember(text, time_str):
    return _memory_manager.remember(text, time_str)

def query_memories(query_text, k=20):
    return _memory_manager.query(query_text, k)
