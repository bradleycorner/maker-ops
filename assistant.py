#!./venv/bin/python3
#!/usr/bin/env python3

import sys
from pathlib import Path
import ollama

# -----------------------------
# Configuration
# -----------------------------

MODEL = "glm-4.7-flash"
MAX_CONTEXT_CHARS = 20000      # prevents context overflow
MAX_FILE_CHARS = 12000         # limit per loaded file


# -----------------------------
# Helpers
# -----------------------------

def read_file(path: str) -> str:
    """Load and trim a file safely."""
    p = Path(path)

    if not p.exists():
        return f"\n[ERROR] File not found: {path}\n"

    content = p.read_text(errors="ignore")
    content = content[:MAX_FILE_CHARS]

    return (
        f"\n----- FILE: {path} -----\n"
        f"{content}\n"
        f"------------------------\n"
    )


def clamp_context(text: str) -> str:
    """Keep context within safe size."""
    return text[-MAX_CONTEXT_CHARS:]


# -----------------------------
# Startup Argument Handling
# -----------------------------

if len(sys.argv) < 2:
    print("Usage: ./assistant.py <milestone-number>")
    sys.exit(1)

milestone = sys.argv[1]

# -----------------------------
# Load Startup Context
# -----------------------------

context_memory = ""

startup_files = [
    "CLAUDE.md",
    f"docs/milestone-{milestone}-slicer-ingestion.md",
]

for file in startup_files:
    context_memory += read_file(file)

context_memory = clamp_context(context_memory)

print(f"Startup context size: {len(context_memory)}")
print("Local Assistant Ready")
print("Commands: /read <file>, /clear, /context, /exit\n")


# -----------------------------
# Main Assistant Loop
# -----------------------------

while True:
    try:
        user_input = input(">> ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        break

    # ---- exit ----
    if user_input == "/exit":
        break

    # ---- clear context ----
    if user_input == "/clear":
        context_memory = ""
        print("Context cleared.")
        continue

    # ---- show context info ----
    if user_input == "/context":
        print(f"\nContext size: {len(context_memory)} characters\n")
        continue

    # ---- read file command ----
    if user_input.startswith("/read "):
        filename = user_input.replace("/read ", "", 1).strip()
        loaded = read_file(filename)
        context_memory += loaded
        context_memory = clamp_context(context_memory)
        print(f"Loaded {filename}")
        continue

    # -----------------------------
    # Normal Chat
    # -----------------------------

    messages = [
        {
            "role": "system",
            "content": (
                "You are a coding assistant working inside a repository.\n"
                "Use the provided project context when relevant.\n\n"
                f"{context_memory}"
            ),
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    print("\nThinking...\n")

    try:
        stream = ollama.chat(
            model=MODEL,
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            print(chunk["message"]["content"], end="", flush=True)

        print("\n")

    except Exception as e:
        print(f"\nERROR communicating with Ollama: {e}\n")
