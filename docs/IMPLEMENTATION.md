# 🔧 Implementation Guide

## Complete Step-by-Step Setup

This guide walks you through implementing the Jazz project from start to finish.

---

## Phase 1: Prerequisites (15 minutes)

### Step 1.1: Install Node.js
1. Download from [nodejs.org](https://nodejs.org)
2. Install LTS version (18+)
3. Verify in PowerShell:
   ```bash
   node --version
   npm --version
   ```

### Step 1.2: Install MongoDB
1. Download from [mongodb.com](https://mongodb.com/try/download/community)
2. Run installer (keep defaults)
3. MongoDB should auto-start
4. Verify: Open new PowerShell and run `mongod`

### Step 1.3: Install Angular CLI
```bash
npm install -g @angular/cli
ng version
```

### Step 1.4: Install Git
1. Download from [git-scm.com](https://git-scm.com)
2. Keep defaults during install
3. Restart PowerShell
4. Verify: `git --version`

---

## Phase 2: Create Backend (30 minutes)

### Step 2.1: Create Backend Folder
```bash
mkdir backend
cd backend
npm init -y
```

### Step 2.2: Copy Backend Files
Copy all files from `templates/backend/` into your `backend/` folder:
- `server.js`
- `package.json` (overwrite the one you just created)

### Step 2.3: Install Dependencies
```bash
npm install
```

This installs:
- **express** - Web server
- **mongoose** - MongoDB connector
- **bcryptjs** - Password hashing
- **jsonwebtoken** - JWT tokens
- **cors** - Cross-origin requests
- **dotenv** - Environment variables

### Step 2.4: Create `.env` File
In `backend/` root, create `.env`:
```
MONGODB_URI=mongodb://localhost:27017/jazz
JWT_SECRET=your_super_secret_key_12345
PORT=3000
```

**⚠️ Never share your `.env` file! Add to `.gitignore`**

### Step 2.5: Test Backend
```bash
npm start
```

Expected output:
```
✓ Jazz backend running on http://localhost:3000
✓ MongoDB: mongodb://localhost:27017/jazz
```

**Leave this running in a terminal!**

---

## Phase 3: Create Frontend (30 minutes)

### Step 3.1: Create Angular Project
Open new PowerShell (keep backend running):
```bash
ng new frontend
cd frontend
```

Choose options:
- Routing: **Yes**
- Stylesheet format: **CSS**

### Step 3.2: Create Components
```bash
ng generate component components/login
ng generate component components/chat
```

### Step 3.3: Copy Frontend Files
Copy component files from `templates/frontend/` to your project:

```bash
# Copy login component
copy templates/frontend/login.component.ts src/app/components/login/
copy templates/frontend/login.component.html src/app/components/login/
copy templates/frontend/login.component.css src/app/components/login/

# Copy chat component
copy templates/frontend/chat.component.ts src/app/components/chat/
copy templates/frontend/chat.component.html src/app/components/chat/
copy templates/frontend/chat.component.css src/app/components/chat/
```

### Step 3.4: Create AuthService
```bash
ng generate service services/auth
```

Copy this into `src/app/services/auth.service.ts`:
```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:3000/api/auth';

  constructor(private http: HttpClient) {}

  login(username: string, password: string) {
    return this.http.post(`${this.apiUrl}/login`, { username, password });
  }

  register(username: string, email: string, password: string) {
    return this.http.post(`${this.apiUrl}/register`, { username, email, password });
  }
}
```

### Step 3.5: Setup App Routing
Update `src/app/app-routing.module.ts`:
```typescript
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { ChatComponent } from './components/chat/chat.component';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'chat', component: ChatComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
```

### Step 3.6: Enable HttpClientModule
Update `src/app/app.module.ts`:
```typescript
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LoginComponent } from './components/login/login.component';
import { ChatComponent } from './components/chat/chat.component';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    ChatComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
```

### Step 3.7: Test Frontend
```bash
ng serve
```

Open `http://localhost:4200` in browser.

**You should see the login page!**

---

## Phase 4: Connect Frontend to Backend (15 minutes)

### Step 4.1: Start Both Services
```bash
# Terminal 1 (Backend)
cd backend
npm start

# Terminal 2 (Frontend)
cd frontend
ng serve
```

### Step 4.2: Test Registration
1. Open `http://localhost:4200`
2. Click "Create One" to switch to registration
3. Enter:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `password123`
4. Click "Create Account"

### Step 4.3: Test Login
1. Login with the credentials you just created
2. You should be redirected to chat page

### Step 4.4: Test Chat
1. Type a message: "Hello Jazz"
2. Click send button
3. You should see the message appear

---

## Phase 5: Integrate Python CLI (20 minutes)

### Step 5.1: Configure Python Path
In `backend/server.js`, update the path:
```javascript
const JAZZ_PROJECT_PATH = 'C:\\AI-Projects\\Jazz';
```

### Step 5.2: Test CLI Integration
1. Open chat interface
2. Send message: "What is 2+2?"
3. Jazz CLI processes it and responds

### Step 5.3: Setup Chat History
All messages automatically save to MongoDB.

View history:
```bash
mongo
use jazz
db.chatlogs.find()
```

---

## Phase 6: Prepare for Deployment (20 minutes)

### Step 6.1: Create `.gitignore`
In project root:
```
node_modules/
.env
dist/
__pycache__/
.angular/
*.log
.DS_Store
```

### Step 6.2: Initialize Git
```bash
git init
git add .
git commit -m "Initial commit: Jazz MEAN stack project"
```

### Step 6.3: Create GitHub Repository
1. Go to [github.com](https://github.com)
2. Create new repository: `Jazz`
3. Push code:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/Jazz.git
   git branch -M main
   git push -u origin main
   ```

### Step 6.4: Prepare for VMs
For multi-VM deployment:
1. Create clone script (see `docs/VLAN_SETUP.md`)
2. Document network configuration
3. Prepare SSH keys

---

## Phase 7: Docker Setup (Optional, 15 minutes)

### Step 7.1: Install Docker
Download from [docker.com](https://docker.com)

### Step 7.2: Build Docker Image
Already have `Dockerfile` in root. Build:
```bash
docker build -t jazz:latest .
```

### Step 7.3: Run Docker Container
```bash
docker run -p 3000:3000 -p 4200:4200 jazz:latest
```

---

## Phase 8: Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads at localhost:4200
- [ ] Can register new account
- [ ] Can login with credentials
- [ ] Chat page loads after login
- [ ] Can send chat messages
- [ ] Messages appear in chat history
- [ ] Can logout and return to login
- [ ] MongoDB has user and chat records
- [ ] Can build production version: `ng build --prod`

---

## Phase 9: Troubleshooting

### Common Issues:
- **"Cannot find module"** → Run `npm install` in that folder
- **"Port already in use"** → See `docs/TROUBLESHOOTING.md`
- **"Cannot connect to MongoDB"** → Ensure `mongod` is running
- **"Frontend can't reach backend"** → Check CORS in `server.js`

See `docs/TROUBLESHOOTING.md` for detailed solutions.

---

## What You've Built! 🎉

```
✅ Complete MEAN stack application
✅ User authentication with JWT
✅ MongoDB database with users & chat logs
✅ Express backend with REST API
✅ Angular frontend with components
✅ Integration with Python CLI
✅ Full deployment-ready project
```

---

## Next Steps

1. **Deploy to VMs** → See `docs/VLAN_SETUP.md`
2. **Track progress** → See `docs/TRELLO_GUIDE.md`
3. **Deploy to cloud** → Docker + cloud provider
4. **Add features** → Extend components

---

## Time Estimates

| Phase | Time | Notes |
|-------|------|-------|
| Prerequisites | 15 min | Install software |
| Backend | 30 min | Server + database |
| Frontend | 30 min | UI + components |
| Connection | 15 min | Link frontend/backend |
| CLI Integration | 20 min | Python integration |
| Deployment | 20 min | Git + Docker |
| **TOTAL** | **~130 min** | **~2 hours** |

---

**Stuck? See `docs/TROUBLESHOOTING.md` or `docs/COMMANDS.md`**
