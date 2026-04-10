import re
import os
from datetime import datetime

TS_RE = re.compile(r'^\("(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"')
HISTORY_PATH = os.environ.get("METTACLAW_HISTORY", "memory/history.metta")

def get_provider():
    """Auto-detect LLM provider based on environment variables."""
    if os.environ.get("OLLAMA_API_BASE"):
        return "Ollama"
    if os.environ.get("OPENAI_API_KEY"):
        return "OpenAI"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "Anthropic"
    if os.environ.get("GROQ_API_KEY"):
        return "Groq"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "OpenRouter"
    return "Ollama"

def get_llm_model():
    """Auto-detect LLM model based on environment variables."""
    if os.environ.get("OLLAMA_MODEL"):
        return os.environ.get("OLLAMA_MODEL")
    if os.environ.get("OLLAMA_API_BASE"):
        return os.environ.get("OLLAMA_MODEL", "llama3")
    if os.environ.get("OPENAI_MODEL"):
        return os.environ.get("OPENAI_MODEL")
    if os.environ.get("ANTHROPIC_MODEL"):
        return os.environ.get("ANTHROPIC_MODEL")
    return "llama3"

def get_history_path():
    """Get history file path, checking multiple possible locations."""
    possible_paths = [
        HISTORY_PATH,
        "repos/mettaclaw/memory/history.metta",
        "memory/history.metta",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return HISTORY_PATH

def extract_timestamp(line):
    m = TS_RE.search(line)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def around_time(needle_time_str, k):
    filename = get_history_path()
    try:
        target = datetime.strptime(needle_time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return f"Error: invalid time format '{needle_time_str}', expected 'YYYY-MM-DD HH:MM:SS'"
    
    buffer = []
    best_idx = None
    best_diff = None
    
    try:
        with open(filename, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                buffer.append((lineno, line))
                ts = extract_timestamp(line)
                if ts is None:
                    continue
                diff = abs((ts - target).total_seconds())
                if best_diff is None or diff < best_diff:
                    best_diff = diff
                    best_idx = len(buffer) - 1
    except FileNotFoundError:
        return f"Error: history file not found at {filename}"
    except Exception as e:
        return f"Error reading history: {e}"
    
    if best_idx is None:
        return f"No timestamped entries found for '{needle_time_str}'"
    
    start = max(0, best_idx - k)
    end = min(len(buffer), best_idx + k + 1)
    ret = "".join(f"{lineno}:{line}" for lineno, line in buffer[start:end])
    return ret if ret else "No entries found"

def _extract_commands(s: str) -> list:
    """Extract individual s-expressions from a string that may contain multiple commands.
    Handles formats like:
      ((send "hi") (query "topic"))
      (send "hi")\n(query "topic")
      ((send "hi"))
    Returns a list of properly parenthesized command strings.
    """
    commands = []
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if ch == '(':
            if depth == 0:
                start = i
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0 and start is not None:
                cmd = s[start:i+1].strip()
                # Unwrap double-parens: ((cmd)) -> (cmd)
                while cmd.startswith("((") and cmd.endswith("))"):
                    cmd = cmd[1:-1].strip()
                if cmd.startswith("(") and cmd.endswith(")"):
                    commands.append(cmd)
                start = None
    return commands


def balance_parentheses(s: str) -> str:
    """Normalize LLM response into a single MeTTa-evaluable s-expression list.
    Extracts commands and wraps them as a single list: ((cmd1) (cmd2)).
    """
    if not s:
        return '((send "Error: empty response"))'
    
    # Fix common LLM output issues
    s = s.replace("_quote_", '"').replace("_apostrophe_", "'").replace("_newline_", "\n")
    # LLM sometimes uses underscores instead of spaces - fix that
    s = s.replace("_", " ").strip()

    # Strip leading garbage (LLM markdown, explanations before the first command)
    first_paren = s.find('(')
    if first_paren > 0:
        garbage = s[:first_paren].strip()
        s = s[first_paren:]
        if garbage:
            garbage = garbage.replace('"', '\\"')
            # Insert as a pin command at the front
            s = f'(pin "{garbage}") ' + s

    commands = _extract_commands(s)

    if commands:
        return '(' + ' '.join(commands) + ')'

    # Fallback: no parens found, wrap as single string command
    safe_s = s.replace('"', '\\"')[:200]
    return f'((send "{safe_s}"))'

def normalize_string(x):
    """Convert normalized string back to normal form for display."""
    try:
        if isinstance(x, bytes):
            result = x.decode("utf-8", errors="ignore")
        else:
            result = str(x)
        # Reverse the string-safe placeholders
        result = result.replace("_quote_", '"').replace("_newline_", "\n").replace("_apostrophe_", "'")
        result = result.replace("_apostrophe_", "'")  # Handle double replacement
        return result
    except Exception:
        return str(x)

def clean_response(s):
    """Replace placeholder tokens with real characters before storing to history."""
    if not isinstance(s, str):
        return str(s) if s else ""
    return s.replace("_quote_", '"').replace("_apostrophe_", "'")

def summarize_errors(error_list):
    """Convert a verbose error list into a short summary string.
    Input: ((MULTI_COMMAND_FAILURE ...) (SINGLE_COMMAND_FORMAT_ERROR (query ...)))
    Output: ERRORS: MULTI_COMMAND_FAILURE x1, SINGLE_COMMAND_FORMAT_ERROR(query) x1
    """
    if not error_list or error_list == []:
        return ""
    
    try:
        s = str(error_list)
    except Exception:
        return " ERRORS: unknown"
    
    # Escape any quotes in the error string to prevent history corruption
    s = s.replace('"', "'")
    
    # Extract error type names
    types = []
    for name in ["MULTI_COMMAND_FAILURE", "SINGLE_COMMAND_FORMAT_ERROR"]:
        count = s.count(name)
        if count > 0:
            types.append(f"{name} x{count}")
    
    # Extract first failed command if available
    try:
        m = re.search(r'(?:SINGLE_COMMAND_FORMAT_ERROR|MULTI_COMMAND_FAILURE).*?\((\w+)\s+"[^"]*"', s)
        first_cmd = f" ({m.group(1)} ...)" if m else ""
    except Exception:
        first_cmd = ""
    
    result = " ERRORS: " + ", ".join(types) + first_cmd
    return result[:120] # Hard cap

def format_lastresults(results_str, error_summary):
    """Concatenate results and error summary into a clean string for &lastresults."""
    if not isinstance(results_str, str):
        results_str = str(results_str) if results_str else ""
    cleaned = clean_response(results_str)
    err = error_summary if isinstance(error_summary, str) and error_summary else ""
    return cleaned + err

def clean_irc_message(raw):
    """Strip IRC sender prefix 'nick: ' from raw message.
    'sseehh: what is 2+2' -> 'what is 2+2'
    """
    if not isinstance(raw, str) or not raw:
        return raw
    if ": " in raw:
        parts = raw.split(": ", 1)
        nick_part = parts[0].strip()
        if " " not in nick_part and nick_part:
            return parts[1].strip()
    return raw

def file_exists(path):
    """Check if file exists."""
    import os
    return os.path.exists(path)

def write_file(path, content):
    """Write content to file (overwrite)."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        return f"Error writing file: {e}"
