import os

CONSOLE_WIDTH = 100
EXEC_TIMEOUT = 3600
RECURSION_LIMIT = 100

# Chunk size for RAG documents (in characters, typically ~4 chars per token)
# Reduced to 1000 chars (~250 tokens) to prevent Ollama crashes on Windows
CHUNK_SIZE = 1000
# Overlap between chunks to maintain context
CHUNK_OVERLAP = 100
# Number of chunks to embed in one batch (Ollama batch size)
# Reduced to 1 to prevent Ollama crashes - embed one at a time
BATCH_SIZE = 1
# Maximum search results for RAG queries (increased for better coverage)
MAX_RESULTS = 20


LAST_N_TURNS = 20

THEME = {
    "primary": "#4566db",
    "secondary": "#9c79ee",
    "accent": "#88c5d0",
    "success": "#10b981",
    "warning": "#ebac40",
    "error": "#ef4444",
    "muted": "#6b7280",
    "text": "#f8fafc",
    "border": "#374151",
}

PROMPTS = {
    "rag_results": "\n\nIMPORTANT: Prioritize the above documents when answering. Cite sources [Source X] when using document information. If the documents don't cover the question, you may use general knowledge but clearly indicate what comes from documents vs. general knowledge.",
    "continue": "Continue where you left off. Don't repeat anything already done.",
}

DEFAULT_PATHS = {
    "history": (
        "%LOCALAPPDATA%\\Ally\\history\\"
        if os.name == "nt"
        else "~/.local/share/Ally/history/"
    ),
    "database": (
        "%LOCALAPPDATA%\\Ally\\database\\"
        if os.name == "nt"
        else "~/.local/share/Ally/database/"
    ),
    "embedding_models": (
        "%LOCALAPPDATA%\\Ally\\embedding_models\\"
        if os.name == "nt"
        else "~/.local/share/Ally/embedding_models/"
    ),
    "parsing_models": (
        "%LOCALAPPDATA%\\Ally\\parsing_models\\"
        if os.name == "nt"
        else "~/.local/share/Ally/parsing_models/"
    ),
}


REGULAR_FILE_EXTENSIONS = [
    ".txt",
    ".md",
    ".markdown",
    ".log",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".html",
    ".csv",
]
