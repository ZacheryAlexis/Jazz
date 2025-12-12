# Repository Organization Guide

## Directory Structure

```
Jazz/
├── 📄 README.md                    # Main project documentation
├── 📄 main.py                      # Entry point for Jazz CLI
├── 📄 config.json                  # Configuration file
├── 📄 requirements.txt             # Python dependencies
├── 📄 LICENSE                      # Apache 2.0 License
├── 📄 Dockerfile                   # Docker container definition
├── 📄 .env.example                 # Example environment variables
├── 📄 .dockerignore                # Docker build ignore patterns
├── 📄 .gitignore                   # Git ignore patterns
│
├── 📁 app/                         # Main application code
│   ├── src/
│   │   ├── agents/                # AI agent implementations
│   │   ├── core/                  # Core RAG and orchestration
│   │   ├── cli/                   # Command-line interface
│   │   ├── embeddings/            # Embedding providers
│   │   ├── tools/                 # Tool implementations (file, web, git, etc.)
│   │   ├── helpers/               # Utility functions
│   │   └── orchestration/         # Pipeline orchestration
│   ├── prompts/                   # System prompts
│   └── utils/                     # Shared utilities
│
├── 📁 tests/                       # Test suite
│   ├── __init__.py
│   ├── README.md                  # Test documentation
│   ├── test_rag_*.py              # RAG-specific tests
│   ├── test_cli.py                # CLI tests
│   ├── test_adaptive_research.py  # Adaptive research tests
│   ├── verify_enhancements.py     # Enhancement validation
│   ├── run_test.py                # Test runner
│   └── test_regression.*          # Regression tests
│
├── 📁 examples/                    # Example scripts
│   ├── __init__.py
│   ├── README.md                  # Examples documentation
│   ├── demo_extraction.py         # Basic extraction demo
│   └── demo_extraction_enhanced.py # Advanced extraction demo
│
├── 📁 scripts/                     # Utility scripts
│   ├── __init__.py
│   ├── README.md                  # Scripts documentation
│   ├── setup.sh / setup.cmd       # (in root) Environment setup
│   ├── lab7_*.sh                  # Lab 7 configuration
│   └── lab8_*.sh                  # Lab 8 configuration
│
├── 📁 docs/                        # Documentation
│   ├── DOCUMENTATION_ORGANIZATION.md
│   ├── QUICK_REFERENCE.md
│   └── project-guides/            # Development guides (not tracked in git)
│       ├── IMPROVEMENTS_GUIDE_TLDR.md
│       ├── PROJECT_IMPROVEMENT_ROADMAP.md
│       ├── COMPLETE_ISSUE_RESOLUTION_LOG.md
│       └── ... (50+ more guides)
│
├── 📁 assets/                      # Static assets
│   └── jazz_cover.jpg
│
├── 📁 bin/                         # Executable scripts
│   └── jazz.bat
│
├── 📁 data/                        # Data storage
│   └── (Runtime data, databases)
│
├── 📁 templates/                   # HTML/UI templates
│   └── (Web interface templates)
│
└── 📁 .github/                     # GitHub configuration
    └── workflows/                 # CI/CD workflows
```

## Folder Purposes

### Core Application (`app/`)
- **src/agents/** - Agent implementations (brainstormer, code_gen, general, web_searcher)
- **src/core/** - Core RAG pipeline, base agent, orchestration
- **src/cli/** - Command-line interface and argument handling
- **src/embeddings/** - Embedding providers and RAG database client
- **src/tools/** - Executable tools (file ops, web search, git, execution)
- **src/helpers/** - Utility functions and validators
- **src/orchestration/** - Two-stage pipeline orchestration
- **utils/** - Shared utility functions and constants

### Testing (`tests/`)
- Unit and integration tests for all major components
- Regression test suites
- Test configuration and utilities
- **Run tests:** `python run_test.py` or `pytest`

### Examples (`examples/`)
- Runnable demonstrations of Jazz capabilities
- Educational materials showing how to use Jazz
- **Run examples:** `python examples/demo_extraction.py`

### Scripts (`scripts/`)
- Environment setup scripts
- Lab configuration scripts
- Network configuration (VLAN setup)
- **Run setup:** `./scripts/setup.sh` (or `setup.cmd` on Windows)

### Documentation (`docs/`)
- **Tracked in git:** Organization guides, quick reference
- **Not tracked:** Development guides and improvement roadmaps in `project-guides/`
- For internal reference without cluttering the repository

### Assets (`assets/`)
- UI images and branding materials
- Static resources used by the application

### Data (`data/`)
- Runtime data storage
- Embeddings databases
- Knowledge bases and cached data

### Templates (`templates/`)
- HTML templates for web interface
- UI component definitions

## File Organization Philosophy

### ✅ Root Level (Clean & Essential)
Only production-critical files:
- Entry point: `main.py`
- Configuration: `config.json`, `requirements.txt`
- Setup: `setup.sh`, `setup.cmd`
- Docker: `Dockerfile`, `.dockerignore`
- Git: `.gitignore`
- Meta: `LICENSE`, `README.md`

### ✅ Tests & Examples (Organized by Purpose)
Tests and examples grouped in dedicated folders for easy discovery and maintenance.

### ✅ Documentation (Professional Structure)
- Production guides: `docs/` (tracked in git)
- Development guides: `docs/project-guides/` (local only, not tracked)

### ✅ Source Code (Logical Grouping)
Application code organized by function:
- Agents responsible for different capabilities
- Core RAG/orchestration pipeline
- Tools for extending capabilities
- Utilities for shared functionality

## Adding New Files

When adding new files:

1. **Test files** → `tests/`
2. **Example scripts** → `examples/`
3. **Utility scripts** → `scripts/`
4. **Source code** → `app/src/` (in appropriate subdirectory)
5. **Documentation** → `docs/` (tracked) or `docs/project-guides/` (local)
6. **Data/databases** → `data/`
7. **Static assets** → `assets/`

## Maintaining Clean Repository

The `.gitignore` file explicitly:
- ✅ Tracks source code (`app/`)
- ✅ Tracks configuration (`config.json`, requirements.txt)
- ✅ Tracks essential docs (`docs/*.md`)
- ❌ Ignores test files (developers can run tests locally)
- ❌ Ignores dev guides (`docs/project-guides/`)
- ❌ Ignores Python cache (`__pycache__`, `.pyc`)
- ❌ Ignores virtual environments (`.venv`)
- ❌ Ignores generated data

## Quick Navigation

- 🚀 **Start here:** `README.md`
- ⚙️ **Configuration:** `config.json`
- 💻 **Source code:** `app/src/`
- 🧪 **Run tests:** `tests/README.md`
- 📚 **Examples:** `examples/README.md`
- 📋 **Setup scripts:** `scripts/README.md`
- 📖 **All documentation:** `docs/`
- 🛠️ **Dev guides:** `docs/project-guides/`
