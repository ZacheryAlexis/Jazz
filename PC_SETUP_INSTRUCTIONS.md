# 🖥️ PC to VM Connection Setup

## What You Just Did
✅ Updated `config.json` to support remote Ollama servers  
✅ Created setup script for this PC (`setup_ollama_pc.bat`)

## Next Steps

### 1. Run the Setup Script on THIS PC
```bash
# Open PowerShell as Administrator, then:
.\setup_ollama_pc.bat

# Or double-click: setup_ollama_pc.bat
```

This will:
- Check if Ollama is installed
- Set `OLLAMA_HOST=0.0.0.0:11434`
- Download an AI model
- Get your PC's IP address
- Show you what to do next

### 2. Note Your PC's IP Address
After running the script, note your IP address (looks like `192.168.x.x`)

### 3. On the VM, Update config.json

SSH into the VM and edit `~/Jazz/config.json`:

```json
{
    "provider": "ollama",
    "ollama_host": "http://YOUR_PC_IP:11434",
    "model": "qwen2.5:14b",
    ...
}
```

Replace `YOUR_PC_IP` with the IP from step 2 (e.g., `192.168.1.100`)

### 4. On the VM, Start Everything

```bash
cd ~/Jazz
./start_all.sh
```

This starts:
- MongoDB (local)
- Express backend (local, port 3000)
- Angular frontend (local, port 4200)
- Connected to **your PC's Ollama** for AI

### 5. Test It!

1. Open browser: http://VM_IP:4200
2. Login or register
3. Start chatting - responses come from your PC's Ollama!

---

## Architecture

```
┌─────────────────────┐
│   This PC           │
│  • Ollama (11434)   │
│  • AI Models        │
└──────────┬──────────┘
           │ Network
           │ (192.168.x.x:11434)
           │
┌──────────▼──────────┐
│   VM (VLAN)         │
│  • MongoDB:27017    │
│  • Backend:3000     │
│  • Frontend:4200    │
└─────────────────────┘
           │
           └── Your Browser
               http://vm-ip:4200
```

---

## Troubleshooting

### Ollama not accessible from VM
- [ ] Ollama is running on this PC
- [ ] `OLLAMA_HOST=0.0.0.0:11434` is set (restart Ollama after setting)
- [ ] Firewall allows port 11434 (check Windows Defender Firewall)
- [ ] VM can ping this PC's IP address

### Model won't download
- [ ] You have internet connection
- [ ] You have at least 8GB disk space free
- [ ] Try: `ollama pull qwen2.5:7b` (smaller model)

### VM can't connect to PC
```bash
# On VM, test connection:
curl http://YOUR_PC_IP:11434/api/tags

# Should return JSON with model list
```

---

**Ready? Run `.\setup_ollama_pc.bat` and follow the prompts!**
