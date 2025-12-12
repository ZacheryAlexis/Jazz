# 📁 Project File Structure

## Complete Directory Map

```
Jazz/
│
├── 📄 config.json                  ← Main configuration file
├── 📄 main.py                      ← Python CLI entry point
├── 📄 Dockerfile                   ← Docker configuration
├── 📄 requirements.txt             ← Python dependencies
├── 📄 README.md                    ← Project introduction
├── 📄 LICENSE                      ← License file
├── 📄 setup.cmd                    ← Windows setup script
├── 📄 setup.sh                     ← Linux/Mac setup script
│
├── 📁 docs/                        ← ALL DOCUMENTATION
│   ├── INDEX.md                    ← Master navigation
│   ├── START_HERE.md               ← Entry point
│   ├── OVERVIEW.md                 ← Architecture guide
│   ├── QUICK_START.md              ← 3-minute setup
│   ├── IMPLEMENTATION.md           ← Detailed setup steps
│   ├── COMMANDS.md                 ← Command reference
│   ├── TROUBLESHOOTING.md          ← Common fixes
│   ├── FILE_STRUCTURE.md           ← This file
│   ├── VLAN_SETUP.md               ← Multi-VM networking
│   └── TRELLO_GUIDE.md             ← Project tracking
│
├── 📁 templates/                   ← CODE TEMPLATES (Copy & use)
│   ├── 📁 backend/
│   │   ├── server.js               ← Express server (264 lines)
│   │   └── package.json            ← Node dependencies
│   │
│   └── 📁 frontend/
│       ├── login.component.ts       ← Login logic (75 lines)
│       ├── login.component.html     ← Login page
│       ├── login.component.css      ← Login styles
│       ├── chat.component.ts        ← Chat logic (154 lines)
│       ├── chat.component.html      ← Chat interface
│       └── chat.component.css       ← Chat styles
│
├── 📁 app/                         ← PYTHON CLI APPLICATION
│   ├── __init__.py
│   ├── 📁 prompts/
│   │   ├── codegen_start.md
│   │   └── context_engineering_steps.md
│   │
│   ├── 📁 src/
│   │   ├── 📁 agents/              ← AI agents (brainstormer, code_gen, etc.)
│   │   ├── 📁 cli/                 ← Command-line interface
│   │   ├── 📁 core/                ← Core functionality
│   │   ├── 📁 embeddings/          ← Vector DB & RAG
│   │   ├── 📁 helpers/             ← Utility functions
│   │   ├── 📁 orchestration/       ← Agent coordination
│   │   └── 📁 tools/               ← Tool implementations
│   │
│   └── 📁 utils/
│       ├── ascii_art.py
│       ├── constants.py
│       └── ui_messages.py
│
├── 📁 assets/                      ← Static files
├── 📁 bin/                         ← Executable scripts
│   └── jazz.bat                    ← Windows batch runner
│
└── 📁 __pycache__/                 ← Python cache (auto-generated)
```

---

## Key Files Explained

### Root Configuration Files

| File | Purpose | Edit When |
|------|---------|-----------|
| `config.json` | Main app config | Changing settings |
| `main.py` | Python entry point | Never (unless extending) |
| `Dockerfile` | Container definition | Changing deployment |
| `requirements.txt` | Python packages | Adding dependencies |
| `.env` | Environment secrets | Setting up locally |

---

### Documentation Structure

```
docs/
├── INDEX.md              ← Where to start (navigation hub)
├── START_HERE.md         ← 5-minute intro
├── OVERVIEW.md           ← Architecture & tech stack
├── QUICK_START.md        ← 3-minute setup
├── IMPLEMENTATION.md     ← Detailed step-by-step
├── COMMANDS.md           ← All command references
├── TROUBLESHOOTING.md    ← Problem solutions
├── FILE_STRUCTURE.md     ← This file
├── VLAN_SETUP.md         ← Multi-VM networking (Lab 8)
└── TRELLO_GUIDE.md       ← Project tracking tips
```

**Start here:** `docs/START_HERE.md`

---

### Code Template Structure

```
templates/
├── backend/
│   ├── server.js         ← Express HTTP server
│   │                        • User authentication
│   │                        • Chat message API
│   │                        • MongoDB integration
│   │                        • JWT token handling
│   │                        • CORS enabled
│   │
│   └── package.json      ← All Node dependencies
│                           • express, mongoose, bcryptjs
│                           • jsonwebtoken, cors, dotenv
│
└── frontend/
    ├── login.component.ts   ← Login page component
    │  • User registration
    │  • User login
    │  • Token storage
    │  • Form validation
    │
    ├── login.component.html ← Login form template
    │  • Username input
    │  • Email input
    │  • Password input
    │  • Toggle register/login
    │
    ├── login.component.css  ← Login styling
    │  • Gradient background
    │  • Form inputs
    │  • Buttons
    │
    ├── chat.component.ts    ← Chat interface logic
    │  • Message sending
    │  • History loading
    │  • Auto-scroll
    │  • Logout handling
    │
    ├── chat.component.html  ← Chat UI template
    │  • Message display
    │  • Input box
    │  • Send button
    │  • User info header
    │
    └── chat.component.css   ← Chat styling
       • Message bubbles
       • Input area
       • Animations
```

**Copy templates into your Angular project!**

---

### Python Application Structure

```
app/
├── src/
│   ├── agents/              ← Different AI personas
│   │   ├── brainstormer/    ← Creative ideation
│   │   ├── code_gen/        ← Code generation
│   │   ├── general/         ← General assistant
│   │   └── web_searcher/    ← Web research
│   │
│   ├── cli/                 ← Command-line interface
│   │   ├── cli.py           ← Main CLI logic
│   │   └── flags.py         ← Command flags
│   │
│   ├── core/                ← Core functionality
│   │   ├── base.py          ← Base classes
│   │   ├── agent_factory.py ← Agent creation
│   │   └── exception_handler.py
│   │
│   ├── embeddings/          ← Vector database & RAG
│   │   ├── db_client.py     ← Database interface
│   │   └── embedding_functions/  ← Different providers
│   │       ├── openai_embed.py
│   │       ├── ollama_embed.py
│   │       └── hf_embed.py
│   │
│   ├── tools/               ← Tool implementations
│   │   ├── exec_tools.py    ← Execute commands
│   │   ├── file_tools.py    ← File operations
│   │   ├── git_tools.py     ← Git integration
│   │   └── web_tools.py     ← Web operations
│   │
│   └── orchestration/       ← Coordinate agents
│       └── units/           ← Orchestration units
│
└── utils/
    ├── ascii_art.py         ← ASCII art display
    ├── constants.py         ← App constants
    └── ui_messages.py       ← User messages
```

---

## File Copy Workflow

### For Your MEAN Stack Implementation:

1. **Copy backend files:**
   ```bash
   cp -r templates/backend/* your-backend-project/
   ```

2. **Copy frontend files:**
   ```bash
   cp -r templates/frontend/* your-frontend-project/src/app/components/
   ```

3. **Install dependencies:**
   ```bash
   # Backend
   cd your-backend-project
   npm install
   
   # Frontend
   cd your-frontend-project
   npm install
   ```

4. **Configure environment:**
   - Create `.env` in backend root
   - Set `MONGODB_URI` and `JWT_SECRET`

---

## Size Reference

- **Total docs:** ~15,000 words across 10 files
- **Backend template:** ~300 lines of code
- **Frontend templates:** ~500 lines of code
- **This file structure:** ~50 total files (including app modules)

---

## What to Edit vs. What to Copy

### ✅ DO Copy:
- Template files → `templates/`
- Documentation → `docs/`
- Configuration examples

### ❌ DON'T Edit:
- Python CLI app (`app/` directory)
- Main entry point (`main.py`)
- Docker configuration (unless deploying)

### ✏️ DO Customize:
- `.env` file with your secrets
- MongoDB connection string
- API URLs for your environment
- User styling in component CSS

---

## Navigation Tips

- **Lost?** → Read `docs/INDEX.md` first
- **Quick setup?** → See `docs/QUICK_START.md`
- **Something broken?** → Check `docs/TROUBLESHOOTING.md`
- **Multi-VM?** → Follow `docs/VLAN_SETUP.md`
- **Need commands?** → Reference `docs/COMMANDS.md`

---

**Next:** Open `docs/IMPLEMENTATION.md` for step-by-step setup!
