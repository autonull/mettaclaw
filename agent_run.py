#!/usr/bin/env python3
"""
MeTTaClaw runner — invokes PeTTa with output filtering and structured logging.

Env vars:
    METTACLAW_VERBOSE=true    Show full MeTTa/Prolog trace (default: filtered)
    METTACLAW_DRY_RUN=true    Validate setup without calling LLM
    METTACLAW_LOG_FILE=path   Write structured log here (default: agent.log)
"""

import os
import re
import sys
import json
import time
import threading
import fcntl
from pathlib import Path

sys.path.insert(0, '/opt/PeTTa/python')
from petta import PeTTa

# ── Configuration ──────────────────────────────────────────────────────────
VERBOSE = os.environ.get("METTACLAW_VERBOSE", "").lower() == "true"
DRY_RUN = os.environ.get("METTACLAW_DRY_RUN", "").lower() == "true"
LOG_FILE = os.environ.get("METTACLAW_LOG_FILE", "/opt/PeTTa/agent.log")

# ── Output filter patterns ─────────────────────────────────────────────────
class LogFilter:
    """Filters out unwanted MeTTa/Prolog trace output."""
    def __init__(self):
        self.skip_patterns = (
            "--> ", ":- findall", "Not specialized", "configure_Spec_", "argk_Spec_",
            "import_prolog_functions", "import_prolog_function(", "compose(",
            "added function", "added rule", "added sexpr", "added translator",
            "metta sexpr", "prolog clause", "metta function", "metta runnable",
            "metta specialization", "Cloning ", "file://", "Loading provider",
            "Provider auto", "git-import!", "use-module!", "static-import!",
            "add-translator-rule!", ": compose", ": for", "(@ ", '"Initializing',
            "empty()", "maxNewInputLoops(50)", "maxWakeLoops(1)", "sleepInterval(1)",
            "maxOutputToken(6000)", "reasoningMode(medium)", "wakeupInterval(600)",
            "maxFeedback(5000)", "maxRecallItems(20)", "maxHistory(8000)",
            "maxErrorFeedback(2000)", "maxEpisodeRecallLines(20)", "commchannel(irc)"
        )
        self.skip_prefixes = (
            "^", "'HandleError", "'get-state", "'change-state", "'println",
            "'string-safe", "'py-str", "'py-call", "'sread", "'append-file",
            "'read-file", "'swrite", "'write-file", "'add-atom", "'addToHistory",
            "'appendToHistory", "'remember", "'query", "'episodes", "'last_chars",
            "'getPrompt", "'getSkills", "'getHistory", "'get_time", "'receive",
            "'repr", "'string_length", "'first_char", "'catch", "'eval", "'superpose",
            "'reduce", "'collapse", "'sleep", "'if ", "'let ", "'progn ", "'case ",
            "'quote ", "'exists_file", "'consult", "'use_module", "'useGPT",
            "'useGPTEmbedding", "'getContext", "'initLoop", "'initMemory",
            "'initChannels", "'mettaclaw", "'configure", "'LLM", "provider(", "'IRC"
        )
        self.caret_re = re.compile(r'^\^+$')

    def should_skip(self, line):
        stripped = line.strip()
        if not stripped:
            return True
        if stripped.startswith(self.skip_prefixes):
            return True
        if any(pattern in stripped for pattern in self.skip_patterns):
            return True
        if self.caret_re.match(stripped):
            return True
        return False


# ── Structured logger ──────────────────────────────────────────────────────
class AgentLogger:
    """Writes structured JSON lines to a log file."""
    def __init__(self, path):
        self.path = path
        self.start = time.time()
        self.lock = threading.Lock()
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.path).write_text("")

    def _write(self, event, **kwargs):
        entry = {"t": round(time.time() - self.start, 2), "event": event, **kwargs}
        with self.lock:
            with open(self.path, "a") as f:
                f.write(json.dumps(entry, default=str) + "\n")

    def iteration(self, k, loops, human_msg):
        self._write("iteration", k=k, loops=loops, human_msg=human_msg)

    def dry_run_complete(self, status, preview=None, errors=None):
        self._write("dry_run_complete", status=status, preview=preview, errors=errors)


# ── Filtered output via fd redirection ─────────────────────────────────────
def _filter_loop(read_fd, write_fd, log_filter):
    """Read from read_fd, filter, write to write_fd. Runs in a thread."""
    buf = ""
    try:
        while True:
            try:
                chunk = os.read(read_fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            buf += text
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if VERBOSE:
                    os.write(write_fd, (line + "\n").encode())
                    continue
                if not line.strip():
                    continue
                if log_filter.should_skip(line):
                    continue
                os.write(write_fd, (line + "\n").encode())
        # Flush remaining
        if buf and VERBOSE:
            os.write(write_fd, buf.encode())
    finally:
        try:
            os.close(write_fd)
        except OSError:
            pass


def run_filtered(func, *args, **kwargs):
    """Run func() with stdout/stderr filtered. Returns func's return value."""
    if VERBOSE:
        return func(*args, **kwargs)

    # Create pipe
    r_fd, w_fd = os.pipe()

    # Save original fds
    orig_stdout = os.dup(1)
    orig_stderr = os.dup(2)

    # Redirect stdout and stderr to pipe write end
    os.dup2(w_fd, 1)
    os.dup2(w_fd, 2)

    # Start filter thread — reads from pipe, writes to orig_stdout
    log_filter = LogFilter()
    filter_thread = threading.Thread(
        target=_filter_loop, args=(r_fd, orig_stdout, log_filter), daemon=True
    )
    filter_thread.start()

    # Close our copy of write end (pipe now has one writer: fd 1/2)
    os.close(w_fd)

    try:
        return func(*args, **kwargs)
    finally:
        # Wait for filter thread to drain pipe
        filter_thread.join(timeout=3)
        # Restore originals
        os.dup2(orig_stdout, 1)
        os.dup2(orig_stderr, 2)
        os.close(r_fd)
        os.close(orig_stdout)
        os.close(orig_stderr)


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    script = sys.argv[1] if len(sys.argv) > 1 else "run.metta"

    if not os.path.exists(script):
        print(f"Error: Script not found: {script}", file=sys.stderr)
        sys.exit(1)

    # Enforce single instance via history file lock
    try:
        sys.path.insert(0, '/opt/PeTTa/repos/mettaclaw/src')
        import helper
        history_path = helper.get_history_path()
        Path(history_path).parent.mkdir(parents=True, exist_ok=True)
        # Open in append mode so we don't truncate existing history
        lock_fd = open(history_path, "a")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"Error: Another instance of MeTTaClaw is already running (lock held on {history_path})", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Warning: Could not establish instance lock: {e}", file=sys.stderr)

    logger = AgentLogger(LOG_FILE)

    print(f"Running: {script}")
    if DRY_RUN:
        print(f"Mode: DRY RUN (no LLM calls)")

    p = PeTTa(verbose=VERBOSE)

    if DRY_RUN:
        def _dry_run():
            print("\nLoading MeTTa library files...")
            try:
                for dep in ["lib_import", "lib_mettaclaw", "lib_nal"]:
                    dep_file = f"/opt/PeTTa/repos/mettaclaw/{dep}.metta"
                    if os.path.exists(dep_file):
                        p.load_metta_file(dep_file)
                src_dir = "/opt/PeTTa/repos/mettaclaw/src"
                if os.path.isdir(src_dir):
                    for f in sorted(os.listdir(src_dir)):
                        if f.endswith(".metta"):
                            p.load_metta_file(f"{src_dir}/{f}")
                # Don't load run.metta — it triggers (mettaclaw) loop
                # Just verify the file exists and is parseable
                if os.path.exists(script):
                    with open(script) as sf:
                        sf.read()
                    print(f"Script file valid: {script}")
                print("All library files loaded successfully")
            except Exception as e:
                print(f"Error: {e}")
                logger.dry_run_complete("failed", errors=str(e))
                return False

            print("\nChecking prompt assembly...")
            print("  (Skipped - requires running (mettaclaw) to set up context)")

            try:
                import sys
                if '/opt/PeTTa/repos/mettaclaw/src' not in sys.path:
                    sys.path.insert(0, '/opt/PeTTa/repos/mettaclaw/src')
                import helper
                model = helper.get_llm_model()
                print(f"LLM model (auto-detected): {model}")
            except Exception as e:
                print(f"Could not auto-detect LLM model in dry-run: {e}")

            print("\nDry run complete - setup is valid")
            return True

        ok = run_filtered(_dry_run)
        sys.exit(0 if ok else 1)

    # Note: `loop.metta` configures `(LLM)` dynamically inside the MeTTa script:
    # `(= (LLM) (py-call (helper.get_llm_model)))`

    # Full run
    try:
        result = p.load_metta_file(script)
        print(f"Result: {result}")
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
