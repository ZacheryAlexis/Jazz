// Jazz MEAN Stack Backend - Express.js Server
// This server provides authentication and chat API endpoints
// that integrate with the local Jazz CLI assistant

const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const { spawn } = require('child_process');
const speakeasy = require('speakeasy');
const QRCode = require('qrcode');
require('dotenv').config();

const path = require('path');
const fs = require('fs');

const app = express();

// ============ MIDDLEWARE ============
app.use(cors());
app.use(express.json());

// If the frontend has been built into `frontend/dist/frontend`, serve its
// browser bundle and fallback to the CSR index (or index.html) for client-side routes.
const builtFrontendDir = path.join(__dirname, '..', 'frontend', 'dist', 'frontend');
const builtBrowserDir = path.join(builtFrontendDir, 'browser');
if (fs.existsSync(builtBrowserDir)) {
  app.use(express.static(builtBrowserDir));

  app.get('*', (req, res, next) => {
    // Let API routes be handled normally
    if (req.path.startsWith('/api') || req.path.startsWith('/auth') || req.path.startsWith('/mfa')) return next();

    // Prefer standard index.html, but Angular's CSR build may produce index.csr.html
    const indexHtml = path.join(builtBrowserDir, 'index.html');
    const csrIndex = path.join(builtBrowserDir, 'index.csr.html');
    if (fs.existsSync(indexHtml)) {
      return res.sendFile(indexHtml);
    }
    if (fs.existsSync(csrIndex)) {
      return res.sendFile(csrIndex);
    }
    // Fallback to top-level index if present
    const topLevelIndex = path.join(builtFrontendDir, 'index.html');
    if (fs.existsSync(topLevelIndex)) {
      return res.sendFile(topLevelIndex);
    }

    // No static index found; continue to next handler
    return next();
  });
}

// ============ DATABASE SETUP ============
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/jazz';

mongoose.connect(MONGODB_URI)
  .then(() => console.log('✓ MongoDB connected'))
  .catch(err => console.error('✗ MongoDB connection error:', err));

// ============ DATABASE SCHEMAS ============

// User Schema
const userSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  mfaSecret: { type: String }, // MFA/2FA secret
  mfaEnabled: { type: Boolean, default: false }, // MFA status
  createdAt: { type: Date, default: Date.now }
});

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (err) {
    next(err);
  }
});

// Compare password method
userSchema.methods.comparePassword = function(enteredPassword) {
  return bcrypt.compare(enteredPassword, this.password);
};

// Chat Log Schema
const chatLogSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  userMessage: { type: String, required: true },
  assistantResponse: { type: String, required: true },
  assistantMeta: { type: Object, default: {} },
  timestamp: { type: Date, default: Date.now }
});

const User = mongoose.model('User', userSchema);
const ChatLog = mongoose.model('ChatLog', chatLogSchema);

// ============ MIDDLEWARE: AUTHENTICATION ============

const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, process.env.JWT_SECRET || 'your_secret_key', (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = user;
    next();
  });
};

// ============ ROUTES: HEALTH & STATUS ============

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'Jazz Backend',
    timestamp: new Date().toISOString(),
    mongodb: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected'
  });
});

// Root
app.get('/', (req, res) => {
  // If a built frontend exists, serve its index.html for the root path so users
  // hitting the backend in a browser will see the UI instead of a JSON payload.
  const builtIndex = path.join(__dirname, '..', 'frontend', 'dist', 'frontend', 'index.html');
  if (fs.existsSync(builtIndex)) {
    res.sendFile(builtIndex);
    return;
  }

  res.json({ 
    message: 'Jazz MEAN Stack Backend API',
    version: '1.0.0',
    endpoints: {
      health: '/api/health',
      register: 'POST /api/auth/register',
      login: 'POST /api/auth/login',
      chat: 'POST /api/chat (requires auth)'
    }
  });
});

// ============ ROUTES: AUTHENTICATION ============

// Register
app.post('/api/auth/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;

    if (!username || !email || !password) {
      return res.status(400).json({ error: 'All fields required' });
    }

    // Check if user exists
    let user = await User.findOne({ $or: [{ email }, { username }] });
    if (user) {
      return res.status(409).json({ error: 'User already exists' });
    }

    // Create new user
    user = new User({ username, email, password });
    await user.save();

    // Generate JWT token
    const token = jwt.sign(
      { id: user._id, username: user.username },
      process.env.JWT_SECRET || 'your_secret_key',
      { expiresIn: '7d' }
    );

    res.status(201).json({ 
      success: true,
      token,
      user: { id: user._id, username: user.username, email: user.email }
    });
  } catch (err) {
    console.error('Register error:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

// Login
app.post('/api/auth/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password required' });
    }

    const user = await User.findOne({ username });
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const isPasswordValid = await user.comparePassword(password);
    if (!isPasswordValid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Check if MFA is enabled
    if (user.mfaEnabled) {
      // Return partial success - client must provide MFA token
      return res.json({
        success: false,
        mfaRequired: true,
        userId: user._id,
        message: 'MFA token required'
      });
    }

    const token = jwt.sign(
      { id: user._id, username: user.username },
      process.env.JWT_SECRET || 'your_secret_key',
      { expiresIn: '7d' }
    );

    res.json({ 
      success: true,
      token,
      user: { id: user._id, username: user.username, email: user.email, mfaEnabled: user.mfaEnabled }
    });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

// ============ ROUTES: MFA ============

// Setup MFA - Generate QR code
app.post('/api/mfa/setup', authenticateToken, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Generate secret
    const secret = speakeasy.generateSecret({
      name: `Jazz (${user.username})`,
      issuer: 'Jazz MEAN Stack'
    });

    // Save secret to user (but don't enable MFA yet)
    user.mfaSecret = secret.base32;
    await user.save();

    // Generate QR code
    const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url);

    res.json({
      success: true,
      secret: secret.base32,
      qrCode: qrCodeUrl,
      message: 'Scan QR code with authenticator app (Google Authenticator, Authy, etc.)'
    });
  } catch (err) {
    console.error('MFA setup error:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

// Verify and enable MFA
app.post('/api/mfa/verify', authenticateToken, async (req, res) => {
  try {
    const { token } = req.body;
    if (!token) {
      return res.status(400).json({ error: 'Token required' });
    }

    const user = await User.findById(req.user.id);
    if (!user || !user.mfaSecret) {
      return res.status(404).json({ error: 'MFA not set up' });
    }

    // Verify token
    const verified = speakeasy.totp.verify({
      secret: user.mfaSecret,
      encoding: 'base32',
      token: token,
      window: 2
    });

    if (!verified) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    // Enable MFA
    user.mfaEnabled = true;
    await user.save();

    res.json({
      success: true,
      message: 'MFA enabled successfully'
    });
  } catch (err) {
    console.error('MFA verify error:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

// Verify MFA token during login
app.post('/api/mfa/login', async (req, res) => {
  try {
    const { userId, token } = req.body;
    if (!userId || !token) {
      return res.status(400).json({ error: 'User ID and token required' });
    }

    const user = await User.findById(userId);
    if (!user || !user.mfaEnabled) {
      return res.status(404).json({ error: 'MFA not enabled' });
    }

    // Verify token
    const verified = speakeasy.totp.verify({
      secret: user.mfaSecret,
      encoding: 'base32',
      token: token,
      window: 2
    });

    if (!verified) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    // Generate JWT
    const jwtToken = jwt.sign(
      { id: user._id, username: user.username },
      process.env.JWT_SECRET || 'your_secret_key',
      { expiresIn: '7d' }
    );

    res.json({
      success: true,
      token: jwtToken,
      user: { id: user._id, username: user.username, email: user.email, mfaEnabled: user.mfaEnabled }
    });
  } catch (err) {
    console.error('MFA login error:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

// Disable MFA
app.post('/api/mfa/disable', authenticateToken, async (req, res) => {
  try {
    const { password } = req.body;
    if (!password) {
      return res.status(400).json({ error: 'Password required' });
    }

    const user = await User.findById(req.user.id);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Verify password
    const isPasswordValid = await user.comparePassword(password);
    if (!isPasswordValid) {
      return res.status(401).json({ error: 'Invalid password' });
    }

    // Disable MFA
    user.mfaEnabled = false;
    user.mfaSecret = null;
    await user.save();

    res.json({
      success: true,
      message: 'MFA disabled successfully'
    });
  } catch (err) {
    console.error('MFA disable error:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

// ============ ROUTES: CHAT ============

// Send chat message - integrates with Jazz CLI
app.post('/api/chat', authenticateToken, async (req, res) => {
  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message required' });
    }

    // Create an AbortController to cancel the CLI if client disconnects
    const controller = new AbortController();
    const signal = controller.signal;

    // If the client disconnects, abort the CLI process
    req.on('close', () => {
      try {
        console.log('Client disconnected, aborting Jazz CLI');
        controller.abort();
      } catch (e) {}
    });

    // Debug: log incoming chat request (mask token)
    try {
      const authHeader = req.headers['authorization'] || '';
      const tokenShort = authHeader.split(' ')[1] ? (authHeader.split(' ')[1].slice(0, 8) + '...') : null;
      console.log(`POST /api/chat from user=${req.user && req.user.id ? req.user.id : 'anon'} token=${tokenShort} message=${(message || '').slice(0,120)}`);
    } catch (e) {}

    // Call Jazz CLI to get response; pass the abort signal so it can be killed
    let jazzResult;
    try {
      // pass userId for rate limiting/concurrency
      jazzResult = await callJazzCLI(message, { signal, userId: req.user && (req.user.id || req.user._id || req.user.userId) });
    } catch (err) {
      console.error('Chat processing error:', err.message || err);
      if (err.message === 'aborted') {
        // Client aborted; respond with 499-like status if still connected
        if (!res.headersSent) return res.status(499).json({ error: 'Client aborted request' });
        return;
      }
      if (err.message === 'too_many_concurrent_requests') return res.status(429).json({ error: 'Server busy, try again shortly' });
      if (err.message === 'rate_limited') return res.status(429).json({ error: 'Rate limit exceeded' });
      return res.status(500).json({ error: 'Failed to process chat message' });
    }

    const assistantText = jazzResult && jazzResult.response ? jazzResult.response : (typeof jazzResult === 'string' ? jazzResult : 'No response');
    const assistantMeta = jazzResult && jazzResult.meta ? jazzResult.meta : {};

    // Short-term UX improvement: if the assistant response is long or
    // contains planning/web-search scaffolding (which can be noisy),
    // generate a concise extracted summary for the UI and keep the
    // original text in assistantMeta.full_response for debugging.
    try {
      const noisyMarkers = ['Web Result', 'Web Results Used', 'I will', 'Let me check', 'Page Not Found', 'Web Result 1:'];
      const isNoisy = noisyMarkers.some(m => typeof assistantText === 'string' && assistantText.includes(m));
      const tooLong = typeof assistantText === 'string' && assistantText.length > 600;

      if (isNoisy || tooLong) {
        assistantMeta.full_response = assistantText;

        // Attempt to extract a concise answer: prefer first paragraph or first sentence.
        let concise = '';
        // Split into paragraphs
        const paragraphs = assistantText.split(/\n\s*\n/).map(p => p.trim()).filter(Boolean);
        if (paragraphs.length > 0) {
          concise = paragraphs[0];
        } else {
          concise = assistantText;
        }

        // Extract first sentence up to reasonable length
        const match = concise.match(/([^.!?]{10,}?[.!?])/);
        if (match && match[1]) {
          concise = match[1].trim();
        }

        if (concise.length > 400) concise = concise.slice(0, 400).trim() + '...';

        // If the concise text is still not helpful, give a clear fallback message
        if (!concise || /I will|Let me|Web Result/i.test(concise)) {
          concise = 'I attempted to look up live results but could not fetch a concise score; please try refreshing or ask me to check again.';
        }

        // Use concise text for the assistantResponse sent to the UI
        assistantText = concise;
      }
    } catch (e) {
      // If anything goes wrong in summarization, keep the original response
      console.error('Response summarization error:', e);
    }

    // Store in database
    const chatLog = new ChatLog({
      userId: req.user.id,
      userMessage: message,
      assistantResponse: assistantText,
      assistantMeta: assistantMeta,
    });
    await chatLog.save();

    res.json({
      success: true,
      userMessage: message,
      assistantResponse: assistantText,
      assistantMeta: assistantMeta,
      timestamp: new Date(),
    });
  } catch (err) {
    console.error('Chat error:', err);
    res.status(500).json({ error: 'Failed to process chat message' });
  }
});

// Get chat history for user
app.get('/api/chat/history', authenticateToken, async (req, res) => {
  try {
    const logs = await ChatLog.find({ userId: req.user.id })
      .sort({ timestamp: -1 })
      .limit(50);
    res.json({ success: true, history: logs });
  } catch (err) {
    console.error('History error:', err);
    res.status(500).json({ error: 'Failed to fetch history' });
  }
});

// ============ HELPER FUNCTIONS ============

// Call Jazz CLI and return response
const JAZZ_PROJECT_PATH = '/home/zach/Jazz';

// Simple in-memory rate limiting and concurrency protection
const GLOBAL_MAX_CONCURRENT_CLI = parseInt(process.env.MAX_CONCURRENT_CLI || '2', 10);
const PER_USER_MAX_CONCURRENT_CLI = parseInt(process.env.PER_USER_MAX_CONCURRENT_CLI || '1', 10);
const RATE_LIMIT_WINDOW_SEC = parseInt(process.env.RATE_LIMIT_WINDOW_SEC || '60', 10);
const RATE_LIMIT_MAX_REQS = parseInt(process.env.RATE_LIMIT_MAX_REQS || '10', 10);

let globalActiveCli = 0;
const perUserActiveCli = new Map(); // userId -> number
const perUserRequests = new Map(); // userId -> [timestamps]

function canSpawnForUser(userId) {
  if (globalActiveCli >= GLOBAL_MAX_CONCURRENT_CLI) return false;
  const userActive = perUserActiveCli.get(userId) || 0;
  if (userActive >= PER_USER_MAX_CONCURRENT_CLI) return false;
  return true;
}

function acquireSpawn(userId) {
  globalActiveCli += 1;
  perUserActiveCli.set(userId, (perUserActiveCli.get(userId) || 0) + 1);
}

function releaseSpawn(userId) {
  globalActiveCli = Math.max(0, globalActiveCli - 1);
  perUserActiveCli.set(userId, Math.max(0, (perUserActiveCli.get(userId) || 1) - 1));
}

function checkRateLimit(userId) {
  try {
    const now = Date.now();
    const windowStart = now - RATE_LIMIT_WINDOW_SEC * 1000;
    const arr = perUserRequests.get(userId) || [];
    const filtered = arr.filter(ts => ts >= windowStart);
    if (filtered.length >= RATE_LIMIT_MAX_REQS) {
      return false;
    }
    filtered.push(now);
    perUserRequests.set(userId, filtered);
    return true;
  } catch (e) {
    return true;
  }
}

function extractShortAnswer(text) {
  if (!text) return text;
  const t = text.trim();
  // Try to capture the first sentence ending with . ? or !
  const m = t.match(/^[\s\S]*?[\.\?!](?=\s|$)/);
  if (m && m[0]) return m[0].trim();
  // Fallback to first non-empty line or truncate
  const lines = t.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
  if (lines.length) return lines[0];
  return t.length > 200 ? t.slice(0,200) + '...' : t;
}

function callJazzCLI(message, options = {}) {
  // Ensure message is a string
  const instr = process.env.JAZZ_CONCISE_PROMPT || 'Answer in one short sentence. If you need to consult the web, give the one-sentence answer first, then list sources.';
  const userPrompt = `${instr}\n\n${message}`;
  const signal = options.signal;
  return new Promise((resolve, reject) => {
    try {
      // Enforce concurrency and rate limits when provided a userId
      const userId = options.userId || (options.user && (options.user.id || options.user.userId));
      if (userId) {
        if (!checkRateLimit(userId)) {
          return reject(new Error('rate_limited'));
        }
        if (!canSpawnForUser(userId)) {
          return reject(new Error('too_many_concurrent_requests'));
        }
        acquireSpawn(userId);
      } else {
        // If no userId, still enforce global cap
        if (globalActiveCli >= GLOBAL_MAX_CONCURRENT_CLI) {
          return reject(new Error('too_many_concurrent_requests'));
        }
        globalActiveCli += 1;
      }

      const python = spawn(
        `${JAZZ_PROJECT_PATH}/venv/bin/python3`,
        [
          `${JAZZ_PROJECT_PATH}/main.py`,
          '-d',
          `${JAZZ_PROJECT_PATH}`,
            '--once',
            '--json',
          '-p',
          userPrompt,
        ],
        {
          env: {
            ...process.env,
            TERM: 'dumb',
            PYTHONUNBUFFERED: '1',
            NO_COLOR: '1',
            PYTHONWARNINGS: 'ignore',
          },
        }
      );

      let output = '';
      let errorOutput = '';
      let settled = false;

      console.log(`Spawned Jazz CLI pid=${python.pid}`);

      const onStdout = (data) => {
        const s = data.toString();
        output += s;
        console.log('[Jazz stdout]', s);
      };

      const onStderr = (data) => {
        const s = data.toString();
        errorOutput += s;
        console.error('[Jazz stderr]', s);
      };

      python.stdout.on('data', onStdout);
      python.stderr.on('data', onStderr);

      const cliTimeout = process.env.JAZZ_CLI_TIMEOUT_MS ? parseInt(process.env.JAZZ_CLI_TIMEOUT_MS) : 120000;
      const timeoutHandle = setTimeout(() => {
        if (settled) return;
        try { python.kill(); } catch (e) {}
        settled = true;
        reject(new Error('Jazz CLI timeout'));
      }, cliTimeout);

      let onAbort = null;
      if (signal) {
        if (signal.aborted) {
          try { python.kill(); } catch (e) {}
          settled = true;
          reject(new Error('aborted'));
          return;
        }
        onAbort = () => {
          if (settled) return;
          try { python.kill(); } catch (e) {}
          settled = true;
          reject(new Error('aborted'));
        };
        signal.addEventListener('abort', onAbort);
      }

      python.on('close', (code) => {
        if (settled) return;
        settled = true;
        clearTimeout(timeoutHandle);
        if (signal && onAbort) {
          try { signal.removeEventListener('abort', onAbort); } catch (e) {}
        }

        // Release spawn counters
        try {
          if (options.userId) releaseSpawn(options.userId);
          else if (options.user && (options.user.id || options.user.userId)) releaseSpawn(options.user.id || options.user.userId);
          else globalActiveCli = Math.max(0, globalActiveCli - 1);
        } catch (e) {}

        if (code === 0) {
          if (output && output.trim()) {
            try {
              const firstBrace = output.indexOf('{');
              const lastBrace = output.lastIndexOf('}');
              if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
                const candidate = output.slice(firstBrace, lastBrace + 1).trim();
                const parsed = JSON.parse(candidate);
                if (parsed && parsed.response) {
                  const full = (parsed.response || '').trim();
                  const concise = extractShortAnswer(full) || 'No response';
                  resolve({ response: concise, meta: { model: parsed.model, provider: parsed.provider, duration_ms: parsed.duration_ms, warnings: parsed.warnings || [], full_response: full } });
                  return;
                }
              }
            } catch (e) {
              // fallthrough
            }

            if (output.includes('JAZZ_SINGLE_SHOT_RESPONSE_START')) {
              try {
                const afterStart = output.split('JAZZ_SINGLE_SHOT_RESPONSE_START').pop();
                const between = afterStart.split('JAZZ_SINGLE_SHOT_RESPONSE_END')[0];
                resolve({ response: between.trim() || 'No response', meta: {} });
                return;
              } catch (e) {}
            }
          }

          resolve({ response: output.trim() || 'No response', meta: {} });
        } else {
          reject(new Error(`Jazz CLI exited with code ${code}: ${errorOutput}`));
        }
      });

    } catch (err) {
      reject(err);
    }
  });
}

// ============ LIVE SCORE FAST PATH (ESPN scoreboard) ============
const https = require('https');

function fetchEspnScore() {
  // Returns a Promise resolving to parsed scoreboard JSON for today
  const url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard';
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(parsed);
        } catch (e) { reject(e); }
      });
    }).on('error', (e) => reject(e));
  });
}

function findGameFromScoreboard(scoreboard, teamA, teamB) {
  if (!scoreboard || !scoreboard.events) return null;
  const a = teamA.toLowerCase();
  const b = teamB.toLowerCase();
  for (const ev of scoreboard.events) {
    try {
      const competitors = ev.competitions && ev.competitions[0] && ev.competitions[0].competitors;
      if (!competitors) continue;
      const names = competitors.map(c => (c.team && (c.team.abbreviation || c.team.displayName || c.team.shortDisplayName) || '').toLowerCase());
      if (names.some(n => n.includes(a)) && names.some(n => n.includes(b))) {
        return { event: ev, competitors };
      }
    } catch (e) { continue; }
  }
  return null;
}

app.get('/api/live_score', authenticateToken, async (req, res) => {
  try {
    const q = (req.query.q || '').toString().trim();
    if (!q) return res.status(400).json({ error: 'Query required (e.g. ?q=Thunder+Spurs)' });
    // Try to split into two team tokens
    const parts = q.split(/[,:;\-\/]+|\s+vs\.?\s+|\s+v\.?\s+|\s+vs\s+/i).map(s => s.trim()).filter(Boolean);
    let teamA = parts[0] || '';
    let teamB = parts[1] || '';
    if (!teamB) {
      // If only one token, try splitting by space and take last word as second team
      const words = q.split('\n')[0].split(' ').filter(Boolean);
      if (words.length >= 2) {
        teamB = words.pop();
        teamA = words.join(' ');
      }
    }

    if (!teamA || !teamB) return res.status(400).json({ error: 'Please provide two teams (e.g. Thunder Spurs)' });

    const scoreboard = await fetchEspnScore();
    const match = findGameFromScoreboard(scoreboard, teamA, teamB);
    if (!match) return res.json({ success: false, message: 'No matching game found on today\'s scoreboard' });

    const ev = match.event;
    const comp = match.competitors;
    // Extract scores and status
    const status = ev.status && ev.status.type && ev.status.type.detail ? ev.status.type.detail : (ev.status && ev.status.type && ev.status.type.state) || 'unknown';
    const scores = comp.map(c => ({ name: (c.team && (c.team.displayName || c.team.shortDisplayName || c.team.abbreviation)) || c.team, score: c.score, winner: c.winner }));

    // Build concise result
    let resultText = `Status: ${status}. `;
    for (const s of scores) {
      resultText += `${s.name}: ${s.score} `;
    }
    // Determine winner if available
    const winner = scores.find(s => s.winner);
    if (winner) resultText = `${winner.name} won (${scores.map(s => `${s.name} ${s.score}`).join(', ')})`; 

    return res.json({ success: true, status, scores, text: resultText });
  } catch (err) {
    console.error('Live score error:', err);
    return res.status(500).json({ error: 'Failed to fetch live scores' });
  }
});

// Issue a short-lived stream token for SSE (safer than sending user JWT in query)
app.post('/api/stream_token', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id || req.user._id || req.user.userId;
    if (!userId) return res.status(400).json({ error: 'Invalid user' });
    const ttl = parseInt(process.env.STREAM_TOKEN_TTL_SECONDS || '60', 10);
    const streamSecret = process.env.STREAM_SECRET || (process.env.JWT_SECRET || 'your_secret_key');
    const payload = { type: 'stream', userId };
    const token = jwt.sign(payload, streamSecret, { expiresIn: `${ttl}s` });
    return res.json({ success: true, token, expires_in: ttl });
  } catch (err) {
    console.error('Stream token error:', err);
    return res.status(500).json({ error: 'Failed to issue stream token' });
  }
});

// ============ Streaming SSE endpoint ============
// Note: EventSource doesn't support custom headers, so we accept token via query param.
app.get('/api/chat/stream', async (req, res) => {
  try {
    const token = req.query.token ? req.query.token.toString() : null;
    const message = req.query.message ? req.query.message.toString() : null;
    if (!token) return res.status(401).end('Missing token');
    if (!message) return res.status(400).end('Missing message');
    // verify token: accept either a short-lived stream token (signed with STREAM_SECRET)
    // or a regular user JWT (for backward compatibility). Prefer stream token.
    let user;
    try {
      // Try stream token first
      const streamSecret = process.env.STREAM_SECRET || (process.env.JWT_SECRET || 'your_secret_key');
      try {
        const decoded = jwt.verify(token, streamSecret);
        // prefer stream token payload
        if (decoded && (decoded.type === 'stream' || decoded.userId)) {
          const uid = decoded.userId || decoded.id || decoded._id;
          if (!uid) throw new Error('Invalid stream token');
          user = { id: uid };
        } else {
          // not a stream token, try regular JWT
          const regular = jwt.verify(token, process.env.JWT_SECRET || 'your_secret_key');
          user = { id: regular.id || regular._id || regular.userId };
        }
      } catch (inner) {
        // fallback: verify as regular JWT
        const regular = jwt.verify(token, process.env.JWT_SECRET || 'your_secret_key');
        user = { id: regular.id || regular._id || regular.userId };
      }
      if (!user || !user.id) return res.status(403).end('Invalid token');
    } catch (e) {
      return res.status(403).end('Invalid token');
    }

    // Setup SSE headers
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive'
    });
    res.write('\n');

    // Spawn python CLI and stream stdout lines as SSE data events.
    // Accumulate output so we can save a ChatLog record when done.
    const instr = process.env.JAZZ_CONCISE_PROMPT || 'Answer in one short sentence. If you need to consult the web, give the one-sentence answer first, then list sources.';
    const userPrompt = `${instr}\n\n${message}`;

    // Enforce rate limits / concurrency for SSE user
    try {
      if (!checkRateLimit(user.id)) {
        res.statusCode = 429;
        res.end('Rate limit exceeded');
        return;
      }
      if (!canSpawnForUser(user.id)) {
        res.statusCode = 429;
        res.end('Server busy, try again later');
        return;
      }
      acquireSpawn(user.id);
    } catch (e) {
      // continue but do not block execution
    }

    const python = spawn(
      `${JAZZ_PROJECT_PATH}/venv/bin/python3`,
      [ `${JAZZ_PROJECT_PATH}/main.py`, '-d', `${JAZZ_PROJECT_PATH}`, '--once', '--json', '-p', userPrompt ],
      { env: { ...process.env, TERM: 'dumb', PYTHONUNBUFFERED: '1', NO_COLOR: '1' } }
    );

    console.log(`SSE Spawned Jazz CLI pid=${python.pid} for user=${user && user.id}`);

    let accumulated = '';
    let parsedSent = false;

    python.stdout.on('data', (chunk) => {
      const s = chunk.toString();
      accumulated += s;

      // Quick heuristic: inspect each new line for a short, definitive answer
      // and emit it immediately to improve latency for simple questions.
      if (!parsedSent) {
        const newLines = s.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
        for (const line of newLines) {
          try {
            // Extract a short sentence candidate
            const cand = extractShortAnswer(line);
            if (cand) {
              const isShort = cand.length <= 80; // more conservative
              const isLikelyDefinitive = /\b(is|equals|=)\b/i.test(cand) || /\d+\s*[\+\-\*\/]\s*\d+/.test(cand);
              // require short length and explicit 'is' or numeric pattern to avoid false positives
              if (isShort && isLikelyDefinitive) {
                res.write(`data: ${cand.replace(/\r?\n+/g,' ')}\n\n`);
                // Also emit a lightweight meta so frontend can stop loading
                res.write(`event: meta\ndata: ${JSON.stringify({ model: null, provider: null, duration_ms: null, full_response: accumulated.trim() })}\n\n`);
                parsedSent = true;
                break;
              }
            }
          } catch (e) {
            // ignore
          }
        }
      }

      // Attempt to parse JSON response from accumulated output
      try {
        const firstBrace = accumulated.indexOf('{');
        const lastBrace = accumulated.lastIndexOf('}');
        if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
          const candidate = accumulated.slice(firstBrace, lastBrace + 1).trim();
          const parsed = JSON.parse(candidate);
          if (parsed && parsed.response) {
            // Send the concise parsed response (first sentence) as the primary data event
            if (!parsedSent) {
              const full = (parsed.response || '').trim();
              const concise = extractShortAnswer(full).replace(/\r?\n+/g, ' ').trim();
              res.write(`data: ${concise}\n\n`);
              // send meta as separate event including full response
              res.write(`event: meta\ndata: ${JSON.stringify({ model: parsed.model, provider: parsed.provider, duration_ms: parsed.duration_ms || null, full_response: full })}\n\n`);
              parsedSent = true;
            }
            // After we've parsed and emitted the concise answer, don't spam raw lines.
            return;
          }
        }
      } catch (e) {
        // ignore parse errors and continue
      }

      // If we haven't found the final JSON yet, buffer but do not send noisy preface lines.
      // Once we've already sent the parsed response, stream further output as `detail` events.
      if (parsedSent) {
        const lines = s.split(/\r?\n/).filter(Boolean);
        for (const line of lines) {
          res.write(`event: detail\ndata: ${line.replace(/\n/g, ' ')}\n\n`);
        }
      }
    });

    python.stderr.on('data', (chunk) => {
      const s = chunk.toString();
      // Send stderr as a separate event
      res.write(`event: stderr\ndata: ${s.replace(/\n/g,' ')}\n\n`);
    });

    python.on('close', async (code) => {
      // Try to parse accumulated output as JSON response (same logic as callJazzCLI)
      let assistantText = accumulated.trim() || 'No response';
      try {
        const firstBrace = assistantText.indexOf('{');
        const lastBrace = assistantText.lastIndexOf('}');
        if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
          const candidate = assistantText.slice(firstBrace, lastBrace + 1).trim();
          const parsed = JSON.parse(candidate);
          if (parsed && parsed.response) {
            assistantText = parsed.response.trim() || assistantText;
          }
        }
      } catch (e) {
        // ignore parse errors
      }

      // Save chat log with assistantText and meta
      try {
        const chatLog = new ChatLog({
          userId: user.id,
          userMessage: message,
          assistantResponse: assistantText,
          assistantMeta: { streamed: true, exitCode: code }
        });
        await chatLog.save();
      } catch (e) {
        console.error('Failed to save streamed chat log:', e);
      }

      // release spawn counters
      try { releaseSpawn(user.id); } catch (e) {}

      res.write(`event: done\ndata: ${JSON.stringify({ code })}\n\n`);
      res.end();
    });

    req.on('close', () => {
      try { python.kill(); } catch (e) {}
    });

  } catch (err) {
    console.error('SSE error:', err);
    res.status(500).end();
  }
});

// ============ ERROR HANDLING ============

app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ============ START SERVER ============

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✓ Jazz backend running on http://localhost:${PORT}`);
  console.log(`✓ MongoDB: ${MONGODB_URI}`);
});
