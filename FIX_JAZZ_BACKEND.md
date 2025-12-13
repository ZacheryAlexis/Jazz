# 🔧 FIX: Jazz Backend Not Responding

Run these commands on the VM to fix the issue:

## Step 1: Update config.json with Ollama Host

```bash
nano ~/Jazz/config.json
```

Add this line after `"provider": "ollama"`:
```json
"ollama_host": "http://192.168.1.21:11434",
```

Full section should look like:
```json
{
    "provider": "ollama",
    "ollama_host": "http://192.168.1.21:11434",
    "provider_per_model": {
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Step 2: Set up Python Virtual Environment

```bash
cd ~/Jazz

# Create venv if not exists
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test Jazz CLI directly
python3 main.py "What is 2+2?"
```

If the last command works and you get a response, move to Step 3.

---

## Step 3: Restart All Services

```bash
cd ~/Jazz
./stop_all.sh
sleep 2
./start_all.sh
```

---

## Step 4: Test the Web UI

1. Open browser: http://VMIP:4200
2. Login
3. Send a message
4. Wait for response

---

## Step 5: Check Logs if Still Not Working

```bash
# Check backend logs
tail -50 ~/Jazz/backend/backend.log

# Check if Ollama is reachable
curl http://192.168.1.21:11434/api/tags

# Test Jazz CLI again
cd ~/Jazz && python3 main.py "test"
```

---

Send me the output of the logs if it still doesn't work!
