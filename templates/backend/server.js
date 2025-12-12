// Jazz MEAN Stack Backend - Express.js Server
// This server provides authentication and chat API endpoints
// that integrate with the local Jazz CLI assistant

const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const { spawn } = require('child_process');
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

    const token = jwt.sign(
      { id: user._id, username: user.username },
      process.env.JWT_SECRET || 'your_secret_key',
      { expiresIn: '7d' }
    );

    res.json({ 
      success: true,
      token,
      user: { id: user._id, username: user.username, email: user.email }
    });
  } catch (err) {
    console.error('Login error:', err);
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
// TODO: Update this path to match your Jazz project location
const JAZZ_PROJECT_PATH = 'C:\\AI-Projects\\Jazz';

function callJazzCLI(message) {
  return new Promise((resolve, reject) => {
    try {
      // Option 1: Call via Python directly
      const python = spawn('python', [
        `${JAZZ_PROJECT_PATH}\\main.py`,
        message
      ]);

      let output = '';
      let errorOutput = '';

      python.stdout.on('data', (data) => {
        output += data.toString();
      });

      python.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      python.on('close', (code) => {
        if (code === 0) {
          resolve(output.trim() || 'No response');
        } else {
          reject(new Error(`Jazz CLI exited with code ${code}: ${errorOutput}`));
        }
      });

      // Timeout after 30 seconds
      setTimeout(() => {
        python.kill();
        reject(new Error('Jazz CLI timeout'));
      }, 30000);

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
