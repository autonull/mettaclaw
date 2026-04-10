with open("agent_run.py", "r") as f:
    content = f.read()

# Fix the raw string syntax warning
content = content.replace("r\"^\\^+$\"", "r'^\\^+$'")

with open("agent_run.py", "w") as f:
    f.write(content)
