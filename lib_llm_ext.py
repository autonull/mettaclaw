import os
import litellm
from litellm import completion

litellm.drop_params = True
litellm.set_verbose = False

def _clean(text):
    if text:
        return text.replace("_quote_", '"').replace("_apostrophe_", "'")
    return ""

def _chat(model, content, max_tokens=6000):
    try:
        resp = completion(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens
        )
        return _clean(resp.choices[0].message.content)
    except Exception as e:
        return f"LLM Error: {str(e)}"

def useMiniMax(content):
    model = os.environ.get('MINIMAX_MODEL', 'openai/minimax/minimax-m2.5')
    return _chat(model=model, content=content, max_tokens=6000)

def useClaude(content):
    model = os.environ.get('CLAUDE_MODEL', 'anthropic/claude-opus-4-20250514')
    return _chat(model=model, content=content, max_tokens=8192)

def useGPT(model, max_tokens, reasoning_mode, content):
    return _chat(model=model, content=content, max_tokens=max_tokens)

def useLLM(model, content, max_tokens=6000):
    return _chat(model=model, content=content, max_tokens=max_tokens)
