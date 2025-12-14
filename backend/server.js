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

const app = express();

// ============ MIDDLEWARE ============
app.use(cors());
app.use(express.json());

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

    // Call Jazz CLI to get response
    // This spawns a child process running: python main.py "<message>"
    const jazzResponse = await callJazzCLI(message);

    // Store in database
    const chatLog = new ChatLog({
      userId: req.user.id,
      userMessage: message,
      assistantResponse: jazzResponse
    });
    await chatLog.save();

    res.json({
      success: true,
      userMessage: message,
      assistantResponse: jazzResponse,
      timestamp: new Date()
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

function callJazzCLI(message) {
  return new Promise((resolve, reject) => {
    try {
      // Call via Python virtual environment using the new CLI flag syntax (-p)
      // main.py now expects a prompt via -p/--p, so pass the flag before the message.
      const python = spawn(
        `${JAZZ_PROJECT_PATH}/venv/bin/python3`,
        [
          `${JAZZ_PROJECT_PATH}/main.py`,
          '-d',
          `${JAZZ_PROJECT_PATH}`,
          '--once',
          '-p',
          message,
        ],
        {
          env: {
            ...process.env,
            TERM: 'dumb',
            PYTHONUNBUFFERED: '1',
            NO_COLOR: '1',
          },
        }
      );

      let output = '';
      let errorOutput = '';

      console.log(`Spawned Jazz CLI pid=${python.pid}`);
      python.stdout.on('data', (data) => {
        const s = data.toString();
        output += s;
        console.log('[Jazz stdout]', s);
      });

      python.stderr.on('data', (data) => {
        const s = data.toString();
        errorOutput += s;
        console.error('[Jazz stderr]', s);
      });

      python.on('close', (code) => {
        if (code === 0) {
          // If the CLI ran in single-shot mode it will print sentinel markers
          // around the assistant response. Prefer extracting that block.
          if (output && output.includes('JAZZ_SINGLE_SHOT_RESPONSE_START')) {
            try {
              const afterStart = output.split('JAZZ_SINGLE_SHOT_RESPONSE_START').pop();
              const between = afterStart.split('JAZZ_SINGLE_SHOT_RESPONSE_END')[0];
              resolve(between.trim() || 'No response');
              return;
            } catch (e) {
              // fallthrough to return full output
            }
          }
          resolve(output.trim() || 'No response');
        } else {
          reject(new Error(`Jazz CLI exited with code ${code}: ${errorOutput}`));
        }
      });

      // Timeout after 120 seconds (models can take longer to respond)
      const cliTimeout = process.env.JAZZ_CLI_TIMEOUT_MS ? parseInt(process.env.JAZZ_CLI_TIMEOUT_MS) : 120000;
      const timeoutHandle = setTimeout(() => {
        try {
          python.kill();
        } catch (e) {
          // ignore
        }
        reject(new Error('Jazz CLI timeout'));
      }, cliTimeout);

      // Clear timeout on successful close
      python.on('close', () => {
        clearTimeout(timeoutHandle);
      });

    } catch (err) {
      reject(err);
    }
  });
}

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
