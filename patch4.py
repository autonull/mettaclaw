with open("agent_run.py", "r") as f:
    content = f.read()

content = content.replace("# ── Structured logger     \"\"\"Writes structured JSON lines to a log file.\"\"\"\n    def __init__(self, path):",
"""# ── Structured logger ──────────────────────────────────────────────────────
class AgentLogger:
    \"\"\"Writes structured JSON lines to a log file.\"\"\"
    def __init__(self, path):""")

with open("agent_run.py", "w") as f:
    f.write(content)
