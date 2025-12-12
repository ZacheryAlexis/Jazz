# 🎷 Jazz - Quick Start Guide

## ⚡ 3-Minute Setup

### Step 1: Clone & Install
```bash
git clone <your-repo>
cd Jazz

# Backend setup
cd backend
npm install
npm start

# Frontend setup (in new terminal)
ng serve
```

### Step 2: Start MongoDB
```bash
mongod
```

### Step 3: Access the App
- Open `http://localhost:4200` in your browser
- Sign up or login
- Start chatting!

---

## 📂 Project Structure

```
Jazz/
├── docs/              ← All documentation
├── templates/         ← Code templates
│   ├── backend/      ← Express server
│   └── frontend/     ← Angular components
├── config.json       ← Configuration
├── main.py           ← Python CLI entry
└── README.md         ← This file
```

---

## 🔑 Key Technologies

| Component | Tech | Version |
|-----------|------|---------|
| Backend | Node.js + Express | 18+ / 4.18+ |
| Frontend | Angular | 15+ |
| Database | MongoDB | 5+ |
| Auth | JWT + Bcrypt | - |
| Deployment | Docker / VMs | - |

---

## 📖 Next Steps

1. **Read** → `docs/START_HERE.md`
2. **Understand** → `docs/OVERVIEW.md`
3. **Implement** → `docs/IMPLEMENTATION.md`
4. **Reference** → `docs/COMMANDS.md`

---

## 🤔 Need Help?

- Check `docs/TROUBLESHOOTING.md` for common issues
- Review `docs/FILE_STRUCTURE.md` to understand the layout
- See `docs/VLAN_SETUP.md` for multi-VM deployment

---

**Happy coding! 🚀**
