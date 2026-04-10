with open("agent_run.py", "r") as f:
    content = f.read()

# Replace the giant lists and filter func with a class
new_filter_class = """class LogFilter:
    \"\"\"Filters out unwanted MeTTa/Prolog trace output.\"\"\"
    def __init__(self):
        self.skip_patterns = [
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
        ]
        self.skip_prefixes = [
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
        ]

    def should_skip(self, line):
        stripped = line.strip()
        if not stripped:
            return True
        for prefix in self.skip_prefixes:
            if stripped.startswith(prefix):
                return True
        for pattern in self.skip_patterns:
            if pattern in stripped:
                return True
        if re.match(r"^\^+$", stripped):
            return True
        return False
"""

# Find start and end of old filter code
start_idx = content.find("SKIP_PATTERNS = [")
end_idx = content.find("class AgentLogger:")

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_filter_class + "\n\n# ── Structured logger " + content[end_idx + 19:]

# Update the filter loop
content = content.replace("def _filter_loop(read_fd, write_fd):", "def _filter_loop(read_fd, write_fd, log_filter):")
content = content.replace("if _should_skip(line):", "if log_filter.should_skip(line):")

# Update the runner
content = content.replace("filter_thread = threading.Thread(\n        target=_filter_loop, args=(r_fd, orig_stdout), daemon=True\n    )",
                          "log_filter = LogFilter()\n    filter_thread = threading.Thread(\n        target=_filter_loop, args=(r_fd, orig_stdout, log_filter), daemon=True\n    )")

# Fix naked OS Exceptions in filter loop
content = content.replace("except OSError:\n                break", "except OSError:\n                break")

with open("agent_run.py", "w") as f:
    f.write(content)
