# 🎯 Jazz AI Setup - Complete Guide

## 🔍 THE SITUATION

You have **TWO pieces** that need to connect:

### What's Working ✅
- **MongoDB**: Storing user data and chat logs
- **Backend (Express.js)**: Handling web requests
- **Frontend (Angular)**: The web interface you see at http://localhost:4200
- **Jazz Python Code**: Ready to run AI commands

### What's Missing ❌
- **AI Model Connection**: Jazz needs an AI model to actually respond to messages!

---

## 💡 THE PROBLEM

Your current VM specs:
- **RAM**: 3.3 GB (with only 119 MB free)
- **CPU**: 2 cores
- **Disk**: 94% full

**This is NOT enough to run AI models locally!**

Even the smallest useful models need:
- Phi-2 (2.7B): 4-6 GB RAM minimum
- Llama 3.2 (3B): 6-8 GB RAM
- Qwen 2.5 (14B): 16+ GB RAM

---

## 🎯 SOLUTION: Connect to Your Desktop PC

You mentioned last night you were working on your desktop - you were probably setting this up!

### Architecture:
```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   This VM   │────>│  Network    │────>│ Your Desktop │
│  (Jazz Web) │<────│             │<────│  (Ollama AI) │
└─────────────┘     └─────────────┘     └──────────────┘
```

---

## 📋 STEP-BY-STEP SETUP

### PART 1: Setup on Your Desktop PC

#### 1.1 Install Ollama
```bash
# On your desktop (Windows/Mac/Linux):
# Download from: https://ollama.com/download
# Or on Linux:
curl -fsSL https://ollama.com/install.sh | sh
```

#### 1.2 Pull an AI Model
```bash
# On desktop, choose one:

# Small but capable (7B, ~4GB RAM needed):
ollama pull qwen2.5:7b

# Better quality (14B, ~8GB RAM needed):
ollama pull qwen2.5:14b

# Lightweight (3B, ~2GB RAM needed):
ollama pull llama3.2:3b
```

#### 1.3 Configure Ollama for Network Access

**Option A: Simple (but less secure)**
```bash
# On your desktop, set environment variable:

# Linux/Mac:
export OLLAMA_HOST=0.0.0.0:11434

# Windows (PowerShell):
$env:OLLAMA_HOST="0.0.0.0:11434"

# Then restart Ollama service
```

**Option B: SSH Tunnel (more secure)**
```bash
# On this VM, create tunnel to your desktop:
ssh -L 11434:localhost:11434 your-username@your-desktop-ip

# Leave this terminal open
# Ollama will be accessible at localhost:11434 on this VM
```

#### 1.4 Get Your Desktop's IP Address
```bash
# On desktop:

# Linux/Mac:
ip addr show | grep "inet " | grep -v 127.0.0.1

# Windows (PowerShell):
ipconfig | findstr IPv4

# Write down the IP address (e.g., 192.168.1.50)
```

#### 1.5 Test Ollama is Accessible
```bash
# On desktop, test locally first:
curl http://localhost:11434/api/tags

# Should show list of models
```

---

### PART 2: Configure This VM to Use Desktop Ollama

#### 2.1 Update Jazz config.json
```bash
cd ~/Jazz
nano config.json
```

Change the Ollama host URL (if using direct connection):
```json
{
    "provider": "ollama",
    "ollama_base_url": "http://YOUR_DESKTOP_IP:11434",
    "model": "qwen2.5:7b",
    ...
}
```

Or if using SSH tunnel, keep it as localhost:
```json
{
    "provider": "ollama",
    "ollama_base_url": "http://localhost:11434",
    "model": "qwen2.5:7b",
    ...
}
```

#### 2.2 Install Python Dependencies
```bash
cd ~/Jazz

# Create virtual environment (recommended):
python3 -m venv venv
source venv/bin/activate

# Install requirements:
pip install -r requirements.txt
```

#### 2.3 Test Jazz CLI Directly
```bash
cd ~/Jazz
python3 main.py "Hello, can you hear me?"

# Should get a response from the AI!
```

#### 2.4 Update Backend to Point to Jazz
```bash
nano ~/Jazz/backend/server.js
```

Find this line (around line 236):
```javascript
const JAZZ_PROJECT_PATH = 'C:\\AI-Projects\\Jazz';
```

Change it to:
```javascript
const JAZZ_PROJECT_PATH = '/home/zach/Jazz';
```

Also update the python command (around line 240):
```javascript
const python = spawn('python3', [  // Changed from 'python' to 'python3'
    `${JAZZ_PROJECT_PATH}/main.py`,
    message
]);
```

#### 2.5 Restart Backend
```bash
cd ~/Jazz
./stop_all.sh
./start_all.sh
```

---

### PART 3: Test Everything

#### 3.1 Test from Terminal
```bash
# Test Jazz CLI:
cd ~/Jazz
source venv/bin/activate  # If using venv
python3 main.py "What is 2+2?"
```

#### 3.2 Test from Web Interface
1. Open browser: http://localhost:4200
2. Login with your account
3. Send a message: "Hello, can you introduce yourself?"
4. Wait for response (may take 10-30 seconds first time)

---

## 🔧 ALTERNATIVE: Use Cloud API (Easier but costs money)

If you have an OpenAI or Anthropic API key:

### 1. Create .env file
```bash
cd ~/Jazz
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-key-here
EOF
```

### 2. Update config.json
```json
{
    "provider": "openai",
    "model": "gpt-4o-mini",
    ...
}
```

### 3. Test it
```bash
python3 main.py "Hello!"
```

---

## 📊 Checking Connection Status

### Check if Desktop Ollama is Reachable
```bash
# From this VM:
curl http://YOUR_DESKTOP_IP:11434/api/tags

# Should show list of models
```

### Check Backend Logs
```bash
tail -f ~/Jazz/backend/backend.log
```

### Check Frontend Logs
```bash
tail -f ~/Jazz/frontend/frontend.log
```

### Check All Services
```bash
cd ~/Jazz
./status.sh
```

---

## 🐛 Troubleshooting

### "Connection refused" when accessing Ollama
- Check firewall on desktop allows port 11434
- Verify Ollama is running: `ollama list` on desktop
- Try SSH tunnel instead of direct connection

### "Module not found" errors
```bash
cd ~/Jazz
source venv/bin/activate
pip install -r requirements.txt
```

### Backend can't find main.py
- Verify path in server.js matches `/home/zach/Jazz`
- Check file exists: `ls -l ~/Jazz/main.py`

### Slow responses
- Use smaller model (llama3.2:3b)
- Check desktop CPU usage
- Ensure desktop has enough RAM

---

## 📝 Quick Reference

### Your Files:
- **Jazz Config**: `~/Jazz/config.json`
- **Backend Code**: `~/Jazz/backend/server.js`
- **Frontend**: Running at http://localhost:4200
- **Backend API**: Running at http://localhost:3000

### Key Commands:
```bash
# Check services
cd ~/Jazz && ./status.sh

# Restart services
cd ~/Jazz && ./stop_all.sh && ./start_all.sh

# Test Jazz directly
cd ~/Jazz && python3 main.py "test message"

# View logs
tail -f ~/Jazz/backend/backend.log
```

### Ports:
- **4200**: Frontend web interface
- **3000**: Backend API
- **27017**: MongoDB
- **11434**: Ollama (on desktop)

---

## ✅ Success Checklist

- [ ] Ollama installed and running on desktop
- [ ] Model pulled on desktop (qwen2.5:7b or similar)
- [ ] Desktop IP address noted
- [ ] Can curl desktop Ollama from this VM
- [ ] config.json updated with correct URL
- [ ] Python dependencies installed
- [ ] Jazz CLI works: `python3 main.py "test"`
- [ ] Backend server.js updated with correct paths
- [ ] Services restarted
- [ ] Web chat works and gets AI responses

---

## 🎯 Next Steps After Setup

Once everything works:

1. **Test different prompts** in the web interface
2. **Try the RAG features** - embed documents for context
3. **Configure VLAN** for multi-VM deployment (Lab 8)
4. **Explore advanced features** in the docs

---

**Need Help?** Check:
- `~/Jazz/README.md` - Full Jazz documentation
- `~/Jazz/docs/` - All project docs
- Backend logs: `~/Jazz/backend/backend.log`

Good luck! 🚀
