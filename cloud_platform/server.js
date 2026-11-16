require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const { initDatabase } = require('./database');

const authRoutes = require('./routes/auth').router;
const scansRoutes = require('./routes/scans');
const feedbackRoutes = require('./routes/feedback');
const adminRoutes = require('./routes/admin');
const apkRoutes = require('./routes/apk');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static frontend assets
app.use(express.static(path.join(__dirname, 'public')));

// Mount API routes
app.use('/api/auth', authRoutes);
app.use('/api/scans', scansRoutes);
app.use('/api/feedback', feedbackRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/apk', apkRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ONLINE',
    system: 'RubberGuard AI Cloud Hub',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Route fallbacks for static HTML pages
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/login', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

app.get('/register', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'register.html'));
});

app.get('/tester-dashboard', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'tester-dashboard.html'));
});

app.get('/admin-dashboard', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'admin-dashboard.html'));
});

app.get('/feedback-portal', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'feedback-portal.html'));
});

// Start Server after Database Initialization
async function startServer() {
  try {
    await initDatabase();
    app.listen(PORT, '0.0.0.0', () => {
      console.log(`=======================================================`);
      console.log(`RubberGuard AI Cloud Server running on port ${PORT}`);
      console.log(`Public Web Portal: http://localhost:${PORT}`);
      console.log(`Admin Dashboard:   http://localhost:${PORT}/admin-dashboard`);
      console.log(`APK Download URL:  http://localhost:${PORT}/api/apk/download`);
      console.log(`=======================================================`);
    });
  } catch (err) {
    console.error('Fatal: Failed to start RubberGuard server:', err);
    process.exit(1);
  }
}

startServer();