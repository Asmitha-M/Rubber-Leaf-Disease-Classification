const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const { dbRun, dbGet, dbAll } = require('../database');

const JWT_SECRET = process.env.JWT_SECRET || 'rubberguard_super_secure_jwt_secret_2026';

// Helper: Authenticate JWT middleware
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (!token) {
    return res.status(401).json({ success: false, error: 'Access token required' });
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ success: false, error: 'Invalid or expired token' });
    }
    req.user = user;
    next();
  });
}

// POST /api/auth/register
router.post('/register', async (req, res) => {
  try {
    const { username, email, password, fullName, phone, location, registeredVia } = req.body;

    if (!username || !email || !password || !fullName) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: username, email, password, and fullName are mandatory'
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        success: false,
        error: 'Password must be at least 6 characters long'
      });
    }

    // Check if username or email already exists
    const existing = await dbGet('SELECT uid, username, email FROM users WHERE username = ? OR email = ?', [
      username.trim(),
      email.trim().toLowerCase()
    ]);

    if (existing) {
      if (existing.username.toLowerCase() === username.trim().toLowerCase()) {
        return res.status(409).json({ success: false, error: 'Username already taken' });
      }
      return res.status(409).json({ success: false, error: 'Email already registered' });
    }

    // Generate secure UID & hash password
    const uid = 'usr_' + crypto.randomBytes(6).toString('hex');
    const passwordHash = await bcrypt.hash(password, 10);

    await dbRun(
      `INSERT INTO users (uid, username, email, password_hash, full_name, phone, location, role, registered_via, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, 'tester', ?, CURRENT_TIMESTAMP)`,
      [
        uid,
        username.trim(),
        email.trim().toLowerCase(),
        passwordHash,
        fullName.trim(),
        phone ? phone.trim() : '',
        location ? location.trim() : 'Karnataka, India',
        registeredVia || 'web'
      ]
    );

    // Audit log
    await dbRun(
      `INSERT INTO audit_logs (event_type, actor_id, details, ip_address)
       VALUES ('USER_REGISTERED', ?, ?, ?)`,
      [uid, `User ${username} registered via ${registeredVia || 'web'}`, req.ip || '127.0.0.1']
    );

    // Generate JWT token
    const token = jwt.sign(
      { uid, username: username.trim(), email: email.trim().toLowerCase(), role: 'tester', fullName: fullName.trim() },
      JWT_SECRET,
      { expiresIn: '30d' }
    );

    res.status(201).json({
      success: true,
      message: 'Registration successful',
      token,
      user: {
        uid,
        username: username.trim(),
        email: email.trim().toLowerCase(),
        fullName: fullName.trim(),
        role: 'tester'
      }
    });
  } catch (err) {
    console.error('Registration error:', err);
    res.status(500).json({ success: false, error: 'Internal server error during registration' });
  }
});

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { identifier, password } = req.body;
    if (!identifier || !password) {
      return res.status(400).json({ success: false, error: 'Username/Email and password are required' });
    }

    const cleanIdentifier = identifier.trim().toLowerCase();
    const user = await dbGet(
      'SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?',
      [cleanIdentifier, cleanIdentifier]
    );

    if (!user) {
      return res.status(401).json({ success: false, error: 'Invalid username/email or password' });
    }

    // Compare bcrypt hash
    const match = await bcrypt.compare(password, user.password_hash);

    // Also allow SHA-256 fallback if user migrated from Android local DB
    let isShaMatch = false;
    if (!match) {
      const sha256Hash = crypto.createHash('sha256').update(password).digest('hex');
      if (user.password_hash === sha256Hash) {
        isShaMatch = true;
        // Upgrade to bcrypt
        const upgradedHash = await bcrypt.hash(password, 10);
        await dbRun('UPDATE users SET password_hash = ? WHERE id = ?', [upgradedHash, user.id]);
      }
    }

    if (!match && !isShaMatch) {
      return res.status(401).json({ success: false, error: 'Invalid username/email or password' });
    }

    // Update last_login_at
    await dbRun('UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?', [user.id]);

    // Audit log
    await dbRun(
      `INSERT INTO audit_logs (event_type, actor_id, details, ip_address)
       VALUES ('USER_LOGIN', ?, ?, ?)`,
      [user.uid, `User ${user.username} logged in`, req.ip || '127.0.0.1']
    );

    // Sign JWT
    const token = jwt.sign(
      { uid: user.uid, username: user.username, email: user.email, role: user.role, fullName: user.full_name },
      JWT_SECRET,
      { expiresIn: '30d' }
    );

    res.json({
      success: true,
      message: 'Login successful',
      token,
      user: {
        uid: user.uid,
        username: user.username,
        email: user.email,
        fullName: user.full_name,
        role: user.role,
        phone: user.phone,
        location: user.location
      }
    });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ success: false, error: 'Internal server error during login' });
  }
});

// GET /api/auth/me
router.get('/me', authenticateToken, async (req, res) => {
  try {
    const user = await dbGet('SELECT id, uid, username, email, full_name, phone, location, role, created_at, last_login_at FROM users WHERE uid = ?', [req.user.uid]);
    if (!user) {
      return res.status(404).json({ success: false, error: 'User profile not found' });
    }

    // Get tester scan count & verification code
    const scanCount = await dbGet("SELECT COUNT(*) as count FROM scans WHERE tester_id = ? AND scan_status = 'ACCEPTED'", [user.uid]);
    const activeCode = await dbGet('SELECT code, created_at, expires_at, status FROM verification_codes WHERE tester_id = ? ORDER BY id DESC LIMIT 1', [user.uid]);
    const feedbackRecord = await dbGet('SELECT feedback_id, submission_timestamp, verification_status FROM feedback WHERE tester_id = ? ORDER BY id DESC LIMIT 1', [user.uid]);

    res.json({
      success: true,
      user: {
        uid: user.uid,
        username: user.username,
        email: user.email,
        fullName: user.full_name,
        phone: user.phone,
        location: user.location,
        role: user.role,
        registeredAt: user.created_at,
        lastLoginAt: user.last_login_at
      },
      evaluation: {
        acceptedScansCount: scanCount ? scanCount.count : 0,
        verificationCode: activeCode ? activeCode.code : null,
        codeStatus: activeCode ? activeCode.status : 'NOT_ISSUED',
        codeExpiry: activeCode ? activeCode.expires_at : null,
        feedbackStatus: feedbackRecord ? feedbackRecord.verification_status : 'PENDING'
      }
    });
  } catch (err) {
    console.error('Profile fetch error:', err);
    res.status(500).json({ success: false, error: 'Failed to retrieve profile' });
  }
});

// POST /api/auth/reset-password
router.post('/reset-password', async (req, res) => {
  try {
    const { email, newPassword } = req.body;
    if (!email || !newPassword) {
      return res.status(400).json({ success: false, error: 'Email and new password are required' });
    }
    if (newPassword.length < 6) {
      return res.status(400).json({ success: false, error: 'Password must be at least 6 characters' });
    }

    const user = await dbGet('SELECT id, uid FROM users WHERE LOWER(email) = ?', [email.trim().toLowerCase()]);
    if (!user) {
      return res.status(404).json({ success: false, error: 'No account found with this email address' });
    }

    const newHash = await bcrypt.hash(newPassword, 10);
    await dbRun('UPDATE users SET password_hash = ? WHERE id = ?', [newHash, user.id]);

    await dbRun(
      `INSERT INTO audit_logs (event_type, actor_id, details, ip_address)
       VALUES ('PASSWORD_RESET', ?, 'User reset password successfully', ?)`,
      [user.uid, req.ip || '127.0.0.1']
    );

    res.json({ success: true, message: 'Password updated successfully. You can now login with your new password.' });
  } catch (err) {
    console.error('Password reset error:', err);
    res.status(500).json({ success: false, error: 'Failed to reset password' });
  }
});

module.exports = {
  router,
  authenticateToken,
  JWT_SECRET
};