# 🛠️ Troubleshooting Guide

## Common Issues & Solutions

---

## Backend Issues

### Issue: MongoDB Connection Failed
```
✗ MongoDB connection error: connect ECONNREFUSED
```

**Solution:**
1. Start MongoDB: `mongod`
2. Ensure MongoDB is running on default port 27017
3. Check MONGODB_URI in `.env`:
   ```
   MONGODB_URI=mongodb://localhost:27017/jazz
   ```

---

### Issue: Port 3000 Already in Use
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solution (Windows PowerShell):**
```bash
# Find process using port 3000
Get-NetTCPConnection -LocalPort 3000 | Select-Object -Property State, OwningProcess

# Kill the process (replace PID with actual ID)
Stop-Process -Id <PID> -Force

# Or change port in backend
set PORT=3001
npm start
```

---

### Issue: JWT Secret Not Set
```
Error: ENOENT: no such file or directory
```

**Solution:**
1. Create `.env` file in backend root
2. Add: `JWT_SECRET=your_secret_key_here`
3. Restart server: `npm start`

---

### Issue: Cannot Find Module 'express'
```
Error: Cannot find module 'express'
```

**Solution:**
```bash
cd backend
npm install
npm start
```

---

## Frontend Issues

### Issue: Angular Port 4200 Already in Use
```
Error: ng serve PORT 4200 is in use
```

**Solution:**
```bash
# Use different port
ng serve --port 4300
```

---

### Issue: Cannot Connect to Backend
```
Failed to load resource: the server responded with a status of 0 (Unknown Error)
```

**Solution:**
1. Ensure backend is running: `npm start` (in backend folder)
2. Check backend URL in `chat.component.ts`:
   ```typescript
   private apiUrl = 'http://localhost:3000/api/chat';
   ```
3. Verify CORS is enabled in server:
   ```javascript
   app.use(cors());
   ```

---

### Issue: Blank Login Page
```
Page loads but shows nothing
```

**Solution:**
1. Open browser DevTools (F12)
2. Check "Console" tab for errors
3. Check "Network" tab - ensure app-shell loads
4. Rebuild: `ng build`
5. Clear browser cache: Ctrl+Shift+Delete

---

### Issue: "Cannot find module '@angular/core'"
```
Error: Cannot find module '@angular/core'
```

**Solution:**
```bash
# In frontend directory
npm install
ng serve
```

---

## Authentication Issues

### Issue: Login Fails - "Invalid credentials"
```
Invalid credentials error
```

**Solution:**
1. Verify user exists in MongoDB:
   ```bash
   mongo
   use jazz
   db.users.find()
   ```
2. Try registering new account
3. Check password hashing in `server.js`

---

### Issue: JWT Token Expired
```
Error: Invalid token
```

**Solution:**
1. Clear localStorage:
   ```javascript
   localStorage.clear()
   ```
2. Login again to get new token
3. Token expires in 7 days - refresh before then

---

## Database Issues

### Issue: MongoDB Connection Timeout
```
Error: connection timeout
```

**Solution:**
```bash
# Ensure MongoDB is running
mongod

# Check if port 27017 is open
netstat -ano | findstr :27017
```

---

### Issue: Database Lock
```
Error: database is locked
```

**Solution:**
```bash
# Stop all Node processes
taskkill /F /IM node.exe

# Delete lock files (MongoDB)
# Navigate to MongoDB data folder and remove .lock file

# Restart MongoDB
mongod
```

---

## Environment & Setup Issues

### Issue: npm/node Command Not Found
```
'npm' is not recognized as an internal or external command
```

**Solution:**
1. Install Node.js from [nodejs.org](https://nodejs.org)
2. Restart terminal/PowerShell
3. Verify: `node --version` and `npm --version`

---

### Issue: Python Not Recognized
```
'python' is not recognized
```

**Solution:**
1. Install Python from [python.org](https://python.org)
2. During setup, CHECK "Add Python to PATH"
3. Restart PowerShell
4. Verify: `python --version`

---

### Issue: Git Not Recognized
```
'git' is not recognized
```

**Solution:**
1. Install Git from [git-scm.com](https://git-scm.com)
2. Restart PowerShell
3. Verify: `git --version`

---

## Deployment Issues

### Issue: Docker Build Fails
```
Error: Cannot find Dockerfile
```

**Solution:**
1. Ensure `Dockerfile` is in project root
2. Run from correct directory:
   ```bash
   cd c:\AI-Projects\Jazz
   docker build -t jazz .
   ```

---

### Issue: VM Connection Failed
```
Could not resolve hostname
```

**Solution:**
1. Verify IP address: `ipconfig` (Windows) or `ifconfig` (Linux)
2. Ensure VM is running
3. Check firewall allows SSH (port 22)
4. Test ping: `ping vm-ip-address`

---

## Quick Diagnostics Checklist

- [ ] Is Node.js installed? `node -v`
- [ ] Is MongoDB running? `mongod` (in separate terminal)
- [ ] Is backend running? `npm start` in backend folder
- [ ] Is frontend running? `ng serve` in frontend folder
- [ ] Is `.env` file present with secrets?
- [ ] Are ports 3000 and 4200 available?
- [ ] Is internet connection stable?
- [ ] Are all dependencies installed? `npm install`

---

## Get More Help

1. **Check logs:**
   - Backend: Look at terminal where `npm start` runs
   - Frontend: Open browser DevTools (F12)
   - MongoDB: Check MongoDB logs

2. **Search for specific error:**
   - Copy exact error message into Google
   - Add context: "Angular" or "Express" or "MongoDB"

3. **Trace the problem:**
   - Does backend work? Test with Postman
   - Does frontend load? Check browser console
   - Can you reach database? Use MongoDB Compass

---

**Still stuck? See `docs/IMPLEMENTATION.md` for detailed setup steps.**
