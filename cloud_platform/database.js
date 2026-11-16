const path = require('path');
const bcrypt = require('bcryptjs');

const isPgMode = !!process.env.DATABASE_URL;

let db = null;
let pgPool = null;

// Convert SQLite '?' positional parameters to PostgreSQL '$1, $2, ...'
function convertSql(sql) {
  let paramIndex = 1;
  return sql.replace(/\?/g, () => `$${paramIndex++}`);
}

if (isPgMode) {
  const { Pool } = require('pg');
  pgPool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.DATABASE_SSL === 'false' ? false : { rejectUnauthorized: false }
  });
  console.log('Database Mode: Managed PostgreSQL (Neon / Cloud)');
} else {
  const sqlite3 = require('sqlite3').verbose();
  const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'rubberguard_cloud.db');
  db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
      console.error('Error connecting to SQLite database:', err.message);
    } else {
      console.log('Database Mode: Local SQLite at:', DB_PATH);
    }
  });
}

// Unified dbRun
async function dbRun(sql, params = []) {
  if (isPgMode) {
    let pgSql = convertSql(sql);
    // If INSERT and doesn't have RETURNING, append RETURNING id so lastID is available
    if (/^\s*INSERT\s+INTO/i.test(pgSql) && !/RETURNING/i.test(pgSql)) {
      pgSql += ' RETURNING id';
    }
    const res = await pgPool.query(pgSql, params);
    const lastID = res.rows && res.rows[0] && res.rows[0].id ? res.rows[0].id : null;
    return { lastID, changes: res.rowCount };
  } else {
    return new Promise((resolve, reject) => {
      db.run(sql, params, function (err) {
        if (err) return reject(err);
        resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }
}

// Unified dbGet
async function dbGet(sql, params = []) {
  if (isPgMode) {
    const pgSql = convertSql(sql);
    const res = await pgPool.query(pgSql, params);
    return res.rows[0] || null;
  } else {
    return new Promise((resolve, reject) => {
      db.get(sql, params, (err, row) => {
        if (err) return reject(err);
        resolve(row || null);
      });
    });
  }
}

// Unified dbAll
async function dbAll(sql, params = []) {
  if (isPgMode) {
    const pgSql = convertSql(sql);
    const res = await pgPool.query(pgSql, params);
    return res.rows || [];
  } else {
    return new Promise((resolve, reject) => {
      db.all(sql, params, (err, rows) => {
        if (err) return reject(err);
        resolve(rows || []);
      });
    });
  }
}

// Atomic transaction helper
async function dbTransaction(callback) {
  if (isPgMode) {
    const client = await pgPool.connect();
    try {
      await client.query('BEGIN');
      const runner = {
        run: async (sql, params = []) => {
          let s = convertSql(sql);
          if (/^\s*INSERT\s+INTO/i.test(s) && !/RETURNING/i.test(s)) s += ' RETURNING id';
          const r = await client.query(s, params);
          return { lastID: r.rows && r.rows[0] ? r.rows[0].id : null, changes: r.rowCount };
        },
        get: async (sql, params = []) => {
          const r = await client.query(convertSql(sql), params);
          return r.rows[0] || null;
        },
        all: async (sql, params = []) => {
          const r = await client.query(convertSql(sql), params);
          return r.rows || [];
        }
      };
      const result = await callback(runner);
      await client.query('COMMIT');
      return result;
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  } else {
    await dbRun('BEGIN TRANSACTION');
    try {
      const runner = {
        run: dbRun,
        get: dbGet,
        all: dbAll
      };
      const result = await callback(runner);
      await dbRun('COMMIT');
      return result;
    } catch (err) {
      await dbRun('ROLLBACK');
      throw err;
    }
  }
}

// Initialize tables
async function initDatabase() {
  if (isPgMode) {
    // PostgreSQL schema
    await pgPool.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        uid TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        location TEXT,
        role TEXT DEFAULT 'tester',
        registered_via TEXT DEFAULT 'web',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMPTZ
      );

      CREATE TABLE IF NOT EXISTS scans (
        id SERIAL PRIMARY KEY,
        scan_id TEXT UNIQUE NOT NULL,
        tester_id TEXT NOT NULL,
        farmer_name TEXT,
        timestamp TIMESTAMPTZ NOT NULL,
        predicted_disease TEXT NOT NULL,
        confidence REAL NOT NULL,
        severity_label TEXT,
        severity_percentage REAL,
        model_version TEXT DEFAULT 'MobileNetV2-1.0',
        app_version TEXT DEFAULT '1.0',
        platform TEXT DEFAULT 'ANDROID',
        scan_status TEXT DEFAULT 'ACCEPTED',
        rejection_reason TEXT,
        sync_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        verification_code_id TEXT
      );

      CREATE TABLE IF NOT EXISTS verification_codes (
        id SERIAL PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        tester_id TEXT NOT NULL,
        scan_id TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL,
        used_at TIMESTAMPTZ,
        status TEXT DEFAULT 'ISSUED'
      );

      CREATE TABLE IF NOT EXISTS feedback (
        id SERIAL PRIMARY KEY,
        feedback_id TEXT UNIQUE NOT NULL,
        verification_code TEXT NOT NULL,
        tester_id TEXT,
        submission_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        overall_rating INTEGER,
        ease_of_use TEXT,
        disease_accuracy_rating TEXT,
        severity_usefulness TEXT,
        recommendation_usefulness TEXT,
        comments TEXT,
        answers_json TEXT,
        verification_status TEXT DEFAULT 'VERIFIED',
        status_reason TEXT
      );

      CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        event_type TEXT NOT NULL,
        actor_id TEXT,
        details TEXT,
        ip_address TEXT,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
      );
    `);
  } else {
    // SQLite schema
    await dbRun(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        location TEXT,
        role TEXT DEFAULT 'tester',
        registered_via TEXT DEFAULT 'web',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login_at DATETIME
      )
    `);

    await dbRun(`
      CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT UNIQUE NOT NULL,
        tester_id TEXT NOT NULL,
        farmer_name TEXT,
        timestamp DATETIME NOT NULL,
        predicted_disease TEXT NOT NULL,
        confidence REAL NOT NULL,
        severity_label TEXT,
        severity_percentage REAL,
        model_version TEXT DEFAULT 'MobileNetV2-1.0',
        app_version TEXT DEFAULT '1.0',
        platform TEXT DEFAULT 'ANDROID',
        scan_status TEXT DEFAULT 'ACCEPTED',
        rejection_reason TEXT,
        sync_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        verification_code_id TEXT,
        FOREIGN KEY (tester_id) REFERENCES users(uid)
      )
    `);

    await dbRun(`
      CREATE TABLE IF NOT EXISTS verification_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        tester_id TEXT NOT NULL,
        scan_id TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        used_at DATETIME,
        status TEXT DEFAULT 'ISSUED',
        FOREIGN KEY (tester_id) REFERENCES users(uid),
        FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
      )
    `);

    await dbRun(`
      CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feedback_id TEXT UNIQUE NOT NULL,
        verification_code TEXT NOT NULL,
        tester_id TEXT,
        submission_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        overall_rating INTEGER,
        ease_of_use TEXT,
        disease_accuracy_rating TEXT,
        severity_usefulness TEXT,
        recommendation_usefulness TEXT,
        comments TEXT,
        answers_json TEXT,
        verification_status TEXT DEFAULT 'VERIFIED',
        status_reason TEXT
      )
    `);

    await dbRun(`
      CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        actor_id TEXT,
        details TEXT,
        ip_address TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  }

  // Default Admin Account initialization
  const adminEmail = process.env.ADMIN_EMAIL || 'admin@rubberguard.org';
  const existingAdmin = await dbGet('SELECT * FROM users WHERE email = ? OR username = ?', [adminEmail, 'admin']);
  if (!existingAdmin) {
    const adminPassword = process.env.ADMIN_PASSWORD || require('crypto').randomBytes(12).toString('hex');
    const hash = await bcrypt.hash(adminPassword, 10);
    const adminUid = 'admin-' + Math.random().toString(36).substring(2, 10);
    await dbRun(`
      INSERT INTO users (uid, username, email, password_hash, full_name, phone, location, role, registered_via)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [adminUid, 'admin', adminEmail, hash, 'System Administrator', '1800-425-5522', 'Mangaluru, Karnataka', 'admin', 'system']);
    console.log(`Default admin account initialized for: ${adminEmail}`);
  }
}

module.exports = {
  db,
  pgPool,
  isPgMode,
  dbRun,
  dbGet,
  dbAll,
  dbTransaction,
  initDatabase
};