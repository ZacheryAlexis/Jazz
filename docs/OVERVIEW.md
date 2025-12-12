# 📋 Jazz IT 340 - Project Overview & Architecture

## What You're Building

A **MEAN Stack Web Application** that:
- Exposes your local Jazz AI assistant through a web browser
- Allows users to register and log in securely
- Provides a chat interface to interact with the AI
- Stores messages in MongoDB with timestamps
- Runs across multiple VMs with a VLAN

## Technology Stack

```
Frontend:      Angular (TypeScript, HTML, CSS)
Backend:       Express.js (Node.js)
Database:      MongoDB
Runtime:       Node.js
Integration:   Jazz CLI (Python)
Deployment:    VMware VMs connected via VLAN
```

## Architecture Diagram

```
User's Browser
    ↓
Angular App (localhost:4200)
    ↓
Express API (localhost:3000)
    ├→ Authentication (register/login)
    ├→ Chat Messages
    └→ Jazz CLI Integration
    ↓
MongoDB (stores users & messages)
    ↓
Jazz CLI (Python AI backend)
```

## Multi-VM Deployment (Week 5-7)

```
VM1 (Frontend/Backend)           VM2 (Database/AI)
192.168.10.10                    192.168.10.20
├─ Angular (4200)                ├─ MongoDB
├─ Express (3000)                ├─ Jazz CLI
└─ SSH access                    └─ Logging
```

Connected via: **VLAN 192.168.10.0/24**

## Project Timeline

| Week | Milestone | What | Deadline |
|------|-----------|------|----------|
| 1 | Proposal | Project plan | Oct 24 |
| 3 | **Frontend** | Login page + chat UI | Nov 14 |
| 5 | **Auth** | User system + database | Dec 5 |
| 7 | **Full** | VMs + Jazz integration | Dec 19 |

## What Success Looks Like

### Week 3 (Nov 14) - Frontend Complete
✅ Can visit app at localhost:4200  
✅ Login page displays beautifully  
✅ Can register new user account  
✅ Can log in with credentials  
✅ Chat interface visible after login  

### Week 5 (Dec 5) - Authentication Complete
✅ Everything above, plus:  
✅ User data stored in MongoDB  
✅ Passwords securely hashed  
✅ JWT tokens for sessions  
✅ Can send/receive messages  
✅ Messages stored with timestamps  

### Week 7 (Dec 19) - Full Stack Complete
✅ Everything above, plus:  
✅ 2 VMs running with VLAN  
✅ Static IPs configured  
✅ SSH working between VMs  
✅ Remote logging script functional  
✅ Jazz AI integration working  
✅ Full end-to-end system working  
✅ Presentation delivered  

## Key Skills You'll Learn

- Full-stack web development (Frontend + Backend)
- User authentication & security
- Database design & queries
- REST API development
- Virtual networking & VLAN configuration
- SSH & firewall management
- Git & version control
- Systems administration
- Project management

## Grading Breakdown

| Component | Weight | What Matters |
|-----------|--------|--------------|
| **Milestones** | 40% | Frontend, Auth, Full Stack working |
| **Trello Board** | 30% | Tasks tracked, updated regularly |
| **Presentation** | 30% | Can explain your project |

## Important Notes

⚠️ **DO NOT** deploy to cloud services (must be local/VMs)  
⚠️ **DO** document all AI-generated code  
⚠️ **DO** make meaningful GitHub commits  
⚠️ **DO** keep Trello board updated (30% of grade!)  
⚠️ **DO** ask for help if stuck (encouraged!)  

## How This Is Organized

```
docs/                    ← All documentation
├─ START_HERE.md        ← You are here
├─ OVERVIEW.md          ← This file
├─ QUICK_START.md       ← 4-hour action plan
├─ IMPLEMENTATION.md    ← Detailed steps
├─ VLAN_SETUP.md        ← VM configuration
└─ ... (other guides)

templates/               ← All code templates
├─ backend/             ← Express server files
└─ frontend/            ← Angular component files
```

Everything is organized. Nothing is scattered.

## Next Step

→ **Open:** `docs/QUICK_START.md`

It tells you exactly what to do this week to get your first working version.

---

**Time to read this:** ~15 minutes  
**Next:** `docs/QUICK_START.md` (10 minutes to read, 4 hours to do)
