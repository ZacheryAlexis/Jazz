# Demo Checklist — Jazz AI Assistant

This checklist covers the quick steps to run the project locally for a demo and the key verification points (SSE streaming, quick answers, MFA, smoke test).

Prerequisites
- Node.js 18+ (LTS)
- npm
- Python 3 for some helper scripts (optional)
- Docker (optional) if you want the compose-based demo

Quick start (local, non-Docker)
1. Install dependencies for backend and frontend (if you will build the frontend):

```bash
cd backend
npm install
cd ../frontend
npm install
```

2. Start local services (recommended scripts exist):

```bash
./start_all.sh    # starts backend + frontend + mongodb if scripted
# or (backend only):
cd backend && npm run dev
```

3. Verify backend health:

```bash
curl http://localhost:3000/api/health
```

4. Run smoke test (fast SSE checks + basic queries):

```bash
./scripts/smoke_test.sh
```

What to look for in smoke test output
- Short math: `data: 4` (quick path)
- Short summary placeholder: `data: Working on a concise answer...` and `meta: {"pending":true}` for longer lookups
- No model or provider in the client-visible meta

MFA demo (UI and API)
1. Create a test user in the UI or via API `/api/auth/register`.
2. Login — if MFA is disabled the Chat UI shows a small banner prompting setup (or visit `/account`).
3. Visit `/account` and click `Setup MFA` — scan the QR or copy the `secret` into an authenticator app.
4. Enter the 6-digit TOTP and click `Verify` — backend will enable MFA.
5. Logout, then re-login — the server will return `mfaRequired:true` and you can call `/api/mfa/login` (UI handles this) to complete login.

E2E & CI notes
- A GitHub Actions workflow `/.github/workflows/backend-tests.yml` runs backend Jest tests on push and PR to `main`.
- Playwright E2E is scaffolded in the frontend, but installing Playwright is optional locally. If you want me to run E2E tests, I can install the Playwright dependency and run them (takes a few minutes).

Troubleshooting
- If SSE does not stream: check backend logs for the spawned CLI process and ensure `python main.py`/CLI path is valid in `backend/server.js`.
- If Angular complains about Zone.js, ensure `zone.js` is installed and imported in `frontend/src/main.ts`.

Contact / demo script
- For your live demo: boot the stack (or Docker compose if you prefer), run `./scripts/smoke_test.sh` to show automated checks, then open the UI: ask a quick math question (2+2) and a longer lookup to demonstrate placeholder→concise answer behavior. Finally, show the `Show details` modal to reveal the full_response (kept in meta for debugging).
