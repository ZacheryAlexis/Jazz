# 📋 Command Reference

## Backend Commands

### Install Dependencies
```bash
cd backend
npm install
```

### Start Development Server
```bash
npm run dev
```
Runs with `nodemon` - auto-restarts on file changes.

### Start Production Server
```bash
npm start
```

---

## Frontend Commands

### Create New Angular Project
```bash
ng new jazz-frontend
cd jazz-frontend
```

### Serve Development Version
```bash
ng serve
```
Visit `http://localhost:4200`

### Build for Production
```bash
ng build --prod
```
Output goes to `dist/` folder.

### Generate New Component
```bash
ng generate component components/login
ng generate component components/chat
```

---

## MongoDB Commands

### Start MongoDB (Windows)
```bash
mongod
```

### Connect to Database
```bash
mongo
use jazz
db.users.find()
```

### Clear Database
```bash
db.users.deleteMany({})
db.chatlogs.deleteMany({})
```

---

## Python CLI Commands

### Test Jazz CLI
```bash
python main.py "What is 2+2?"
```

### Run with Custom Config
```bash
python main.py "Your question" --config custom.json
```

---

## Environment Setup

### Create `.env` File
```bash
# .env (in backend root)
MONGODB_URI=mongodb://localhost:27017/jazz
JWT_SECRET=your_super_secret_key_here
PORT=3000
```

### Load Environment
```bash
# Windows PowerShell
$env:MONGODB_URI = "mongodb://localhost:27017/jazz"
$env:JWT_SECRET = "your_key"
```

---

## Git Commands

### Clone Repository
```bash
git clone <repo-url>
cd Jazz
```

### Create Feature Branch
```bash
git checkout -b feature/my-feature
git add .
git commit -m "Add feature description"
git push origin feature/my-feature
```

### Update From Remote
```bash
git pull origin main
```

---

## Docker Commands

### Build Docker Image
```bash
docker build -t jazz-app .
```

### Run Docker Container
```bash
docker run -p 3000:3000 -p 4200:4200 jazz-app
```

### View Running Containers
```bash
docker ps
```

---

## Debugging

### Check if Port is in Use
```bash
# Windows PowerShell
Get-NetTCPConnection -LocalPort 3000 | Select-Object -Property State, OwningProcess

# Kill process using port 3000
Stop-Process -Id <PID> -Force
```

### View Server Logs
```bash
# In backend directory where server is running
npm run dev
```

### Angular DevTools
1. Install [Angular DevTools](https://chrome.google.com/webstore) from Chrome Store
2. Open DevTools (F12)
3. Find "Angular" tab

---

## VM Deployment Commands

### SSH into VM
```bash
ssh username@vm-ip-address
```

### Copy Files to VM
```bash
scp -r ./jazz username@vm-ip:/home/username/
```

### Setup VLAN Interface
```bash
# On Ubuntu VM
sudo nano /etc/netplan/01-netcfg.yaml
sudo netplan apply
```

---

## Testing

### Run Backend Tests
```bash
npm test
```

### Run Frontend Tests
```bash
ng test
```

### Run E2E Tests
```bash
ng e2e
```

---

## Monitoring

### Check Node Process
```bash
node -v
npm -v
```

### Check MongoDB Status
```bash
mongo --eval "db.adminCommand('ping')"
```

### System Resources
```bash
# See memory/CPU usage
tasklist
```

---

**See `docs/IMPLEMENTATION.md` for step-by-step setup instructions.**
