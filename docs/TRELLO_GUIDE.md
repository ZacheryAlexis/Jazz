# 📊 Project Tracking with Trello

## Setup & Management Guide

---

## Creating Your Trello Board

### Step 1: Create Board
1. Go to [trello.com](https://trello.com)
2. Create new board: "Jazz IT 340"
3. Set background to dark (optional but looks good)

### Step 2: Create Lists
Create these lists in order (left to right):
1. **Backlog**
2. **To Do**
3. **In Progress**
4. **Review**
5. **Done**

---

## Task Breakdown

### Phase 1: Setup (Week 1)

**Backlog Cards:**
```
☐ Install Node.js
☐ Install MongoDB
☐ Install Angular CLI
☐ Install Git
☐ Create GitHub account
```

**Then move to "To Do"** and drag to columns as you work.

---

### Phase 2: Backend (Week 2)

**To Do:**
```
☐ Create backend folder
☐ Initialize npm project
☐ Copy server.js from templates
☐ Install dependencies (npm install)
☐ Create .env file
☐ Test MongoDB connection
☐ Test server startup
```

**Progress Tracking:**
- Move card to "In Progress" when starting
- Move to "Review" when testing
- Move to "Done" when verified working

---

### Phase 3: Frontend (Week 2-3)

**To Do:**
```
☐ Create Angular project (ng new)
☐ Install dependencies
☐ Generate login component
☐ Generate chat component
☐ Generate auth service
☐ Copy login files from templates
☐ Copy chat files from templates
☐ Test frontend runs (ng serve)
```

---

### Phase 4: Integration (Week 3)

**To Do:**
```
☐ Connect frontend to backend
☐ Test registration flow
☐ Test login flow
☐ Test logout flow
☐ Test message sending
☐ Verify chat history saves
☐ Test JWT token handling
☐ Fix any connection issues
```

---

### Phase 5: Deployment (Week 4)

**To Do:**
```
☐ Create .gitignore
☐ Initialize git repository
☐ Make initial commit
☐ Create GitHub repository
☐ Push to GitHub
☐ Setup Docker (optional)
☐ Build Docker image
☐ Test Docker container
```

---

### Phase 6: Multi-VM Setup (Week 5)

**To Do:**
```
☐ Plan VM network topology
☐ Configure VLAN settings
☐ Setup Ubuntu VMs
☐ Clone repo to VMs
☐ Install dependencies on VMs
☐ Test connectivity between VMs
☐ Test application on VMs
☐ Document VLAN configuration
```

---

## Trello Best Practices

### Labeling System
Create these labels:
- 🔴 **High Priority** (red)
- 🟡 **Medium** (yellow)
- 🟢 **Low Priority** (green)
- 🔵 **Bug** (blue)
- 🟣 **Feature** (purple)
- ⚫ **Documentation** (black)

### Example Card:
```
Title: Test JWT authentication

Description:
Test that JWT tokens are properly:
- Generated on login
- Stored in localStorage
- Sent with API requests
- Validated on backend

Checklist:
☐ Login and receive token
☐ Check browser localStorage
☐ Make API request
☐ Verify token in headers

Labels: High Priority, Testing
Assigned to: [Your name]
Due date: [Date]
```

---

## Weekly Checklist

### Every Monday
- [ ] Move completed items to "Done"
- [ ] Review "In Progress" - move stalled items back
- [ ] Create cards for week's goals
- [ ] Estimate time for each task

### Daily (Quick)
- [ ] Drag cards as you work
- [ ] Update progress in descriptions
- [ ] Add comments for blockers

### End of Week
- [ ] Archive completed cards
- [ ] Note what took longer than expected
- [ ] Plan next week based on progress

---

## Time Estimation Guide

Use card estimation:
- **1 = 30 min** (Quick fix)
- **2 = 1 hour** (Simple task)
- **3 = 2 hours** (Medium task)
- **5 = 4 hours** (Complex task)
- **8 = Full day** (Very complex)

Example:
```
Setup MongoDB
Estimation: 1
Time spent: 15 min
Status: Done
```

---

## Priority Matrix

### Priority Assignment:
```
URGENT + IMPORTANT → Top of "To Do"
IMPORTANT + NOT URGENT → "To Do" (normal)
URGENT + NOT IMPORTANT → "To Do" (low)
NOT URGENT + NOT IMPORTANT → "Backlog"
```

---

## Sample Weekly Progress

### Week 1: Setup
```
Monday:
✓ Install Node.js (30 min)
✓ Install MongoDB (45 min)

Tuesday:
✓ Install Angular CLI (15 min)
✓ Setup GitHub (20 min)

Wednesday-Friday:
✓ Learning & planning
```

### Week 2: Backend
```
Monday:
✓ Create backend folder (15 min)
✓ npm init and install (20 min)
✓ Copy server.js (10 min)

Tuesday:
✓ Create .env file (10 min)
✓ Test MongoDB connection (30 min)
✓ Fix connection issues (45 min)

Wednesday:
✓ Test authentication endpoints (60 min)
✓ Test chat endpoint (45 min)

Thursday-Friday:
✓ Bug fixes & cleanup (90 min)
```

---

## Integration with Documentation

Link Trello cards to docs:

**In Card Description:**
```
# Backend Setup

See detailed steps: docs/IMPLEMENTATION.md (Phase 2)
Commands reference: docs/COMMANDS.md
Troubleshooting: docs/TROUBLESHOOTING.md

## Progress:
- [x] Created backend folder
- [ ] Installed dependencies
```

---

## Templates for Recurring Cards

### Testing Checklist Template
```
Test: [Component Name]

Checklist:
☐ Unit tests pass
☐ Integration tests pass
☐ Manual testing works
☐ No console errors
☐ Responsive on mobile
☐ Accessibility OK
```

### Bug Report Template
```
Bug: [Brief title]

Description:
What happened:
Expected behavior:
Actual behavior:
Steps to reproduce:
Browser/Environment:

Labels: Bug, High Priority
Severity: Critical/High/Medium/Low
```

### Feature Request Template
```
Feature: [Name]

Why:
What problem does it solve?

How:
How should it work?

Acceptance Criteria:
☐ Requirement 1
☐ Requirement 2
☐ Requirement 3
```

---

## Trello Power-Ups (Optional)

Recommended free add-ons:
- **Calendar** - See due dates in calendar view
- **Voting** - Team votes on priority
- **Custom Fields** - Add effort/time estimates
- **Timeline** - Gantt chart view

---

## Team Collaboration

### If Working in a Team:
1. **Invite members** to board
2. **Assign cards** to team members
3. **Use comments** for discussions
4. **@mention** for quick alerts
5. **Due dates** for accountability

### Daily Standup Format:
```
What I finished yesterday:
- [Card 1]
- [Card 2]

What I'm doing today:
- [Card 3]
- [Card 4]

Blockers:
- [Issue or question]
```

---

## Metrics to Track

### Velocity
Count cards completed per week:
- Week 1: 8 cards
- Week 2: 12 cards
- Week 3: 10 cards
- Average: ~10 cards/week

### Burndown
Cards remaining vs. time:
```
Monday: 35 cards
Tuesday: 30 cards
Wednesday: 25 cards
Thursday: 20 cards
Friday: 15 cards
```

### Cycle Time
Time from "To Do" to "Done":
- Quick tasks: 1 day
- Medium tasks: 3-4 days
- Complex tasks: 5+ days

---

## Export & Reporting

### Weekly Report Format:
```
## Week of [Date]

**Completed:**
- 12 cards finished
- 45 hours of work
- [List key accomplishments]

**In Progress:**
- 3 cards (80% done)
- [What's next]

**Blockers:**
- [Any issues]

**Next Week:**
- [Planned tasks]
```

---

## Sample Full Board View

```
BACKLOG | TO DO | IN PROGRESS | REVIEW | DONE
---------|-------|-------------|--------|-----
         | Setup |  Backend    | Tests  | ✓ Git
         | Tests | Frontend    | Deploy | ✓ Node
         | Docs  | Integration |        | ✓ Mongo
         |       | VLAN Setup  |        | ✓ Auth
         |       |             |        | ✓ Chat
```

---

## Quick Start Setup (5 minutes)

1. Create board: "Jazz IT 340"
2. Add 5 lists: Backlog, To Do, In Progress, Review, Done
3. Add Phase 1 tasks from "Task Breakdown" section
4. Start with "Prerequisites" (top 4 items)
5. Move to "To Do"
6. Drag to "In Progress" as you work
7. Check off items
8. Move to "Done" when complete

**That's it! Now you have a visual project tracker.**

---

## Trello Board Sharing

### GitHub Integration:
1. Go to board settings
2. Connect GitHub
3. Auto-link commits to cards

### Example commit:
```bash
git commit -m "Setup authentication #3"
# This links to card #3 in Trello
```

---

**Next: Start moving "Prerequisites" cards to "To Do" and begin Phase 1!**
