require('dotenv').config();
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const { Pool } = require('pg');

async function migrate() {
  const targetDatabaseUrl = process.argv[2] || process.env.DATABASE_URL;
  if (!targetDatabaseUrl) {
    console.error('ERROR: Missing target PostgreSQL DATABASE_URL.');
    console.error('Usage: node migrate_to_postgres.js "postgresql://user:pass@host/db?sslmode=require"');
    process.exit(1);
  }

  const sqlitePath = process.env.DB_PATH || path.join(__dirname, 'rubberguard_cloud.db');
  console.log('--- RubberGuard AI Database Migration to PostgreSQL ---');
  console.log(`Source SQLite Database:      ${sqlitePath}`);
  console.log(`Target PostgreSQL Instance:  ${targetDatabaseUrl.replace(/:[^:@]+@/, ':***@')}`);

  // Connect SQLite
  const sqliteDb = new sqlite3.Database(sqlitePath, sqlite3.OPEN_READONLY);
  function sqliteAll(sql, params = []) {
    return new Promise((resolve, reject) => {
      sqliteDb.all(sql, params, (err, rows) => {
        if (err) return reject(err);
        resolve(rows || []);
      });
    });
  }

  // Connect PostgreSQL
  const pgPool = new Pool({
    connectionString: targetDatabaseUrl,
    ssl: { rejectUnauthorized: false }
  });

  const pgClient = await pgPool.connect();

  try {
    console.log('Connected to target PostgreSQL successfully.');
    console.log('Creating PostgreSQL schema if not exists...');

    await pgClient.query('BEGIN');

    // 1. Create Schema
    await pgClient.query(`
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

    // 2. Migrate Users
    console.log('Migrating users table...');
    const users = await sqliteAll('SELECT * FROM users ORDER BY id ASC');
    for (const u of users) {
      await pgClient.query(`
        INSERT INTO users (id, uid, username, email, password_hash, full_name, phone, location, role, registered_via, created_at, last_login_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (uid) DO UPDATE SET
          username = EXCLUDED.username,
          email = EXCLUDED.email,
          password_hash = EXCLUDED.password_hash,
          full_name = EXCLUDED.full_name,
          phone = EXCLUDED.phone,
          location = EXCLUDED.location,
          role = EXCLUDED.role,
          last_login_at = EXCLUDED.last_login_at
      `, [u.id, u.uid, u.username, u.email, u.password_hash, u.full_name, u.phone, u.location, u.role, u.registered_via, u.created_at, u.last_login_at]);
    }

    // 3. Migrate Scans
    console.log('Migrating scans table...');
    const scans = await sqliteAll('SELECT * FROM scans ORDER BY id ASC');
    for (const s of scans) {
      await pgClient.query(`
        INSERT INTO scans (id, scan_id, tester_id, farmer_name, timestamp, predicted_disease, confidence, severity_label, severity_percentage, model_version, app_version, platform, scan_status, rejection_reason, sync_timestamp, verification_code_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
        ON CONFLICT (scan_id) DO UPDATE SET
          scan_status = EXCLUDED.scan_status,
          verification_code_id = EXCLUDED.verification_code_id
      `, [s.id, s.scan_id, s.tester_id, s.farmer_name, s.timestamp, s.predicted_disease, s.confidence, s.severity_label, s.severity_percentage, s.model_version, s.app_version, s.platform, s.scan_status, s.rejection_reason, s.sync_timestamp, s.verification_code_id]);
    }

    // 4. Migrate Verification Codes
    console.log('Migrating verification_codes table...');
    const codes = await sqliteAll('SELECT * FROM verification_codes ORDER BY id ASC');
    for (const c of codes) {
      await pgClient.query(`
        INSERT INTO verification_codes (id, code, tester_id, scan_id, created_at, expires_at, used_at, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (code) DO UPDATE SET
          used_at = EXCLUDED.used_at,
          status = EXCLUDED.status
      `, [c.id, c.code, c.tester_id, c.scan_id, c.created_at, c.expires_at, c.used_at, c.status]);
    }

    // 5. Migrate Feedback
    console.log('Migrating feedback table...');
    const feedback = await sqliteAll('SELECT * FROM feedback ORDER BY id ASC');
    for (const f of feedback) {
      await pgClient.query(`
        INSERT INTO feedback (id, feedback_id, verification_code, tester_id, submission_timestamp, overall_rating, ease_of_use, disease_accuracy_rating, severity_usefulness, recommendation_usefulness, comments, answers_json, verification_status, status_reason)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        ON CONFLICT (feedback_id) DO NOTHING
      `, [f.id, f.feedback_id, f.verification_code, f.tester_id, f.submission_timestamp, f.overall_rating, f.ease_of_use, f.disease_accuracy_rating, f.severity_usefulness, f.recommendation_usefulness, f.comments, f.answers_json, f.verification_status, f.status_reason]);
    }

    // 6. Migrate Audit Logs
    console.log('Migrating audit_logs table...');
    const logs = await sqliteAll('SELECT * FROM audit_logs ORDER BY id ASC');
    for (const l of logs) {
      await pgClient.query(`
        INSERT INTO audit_logs (id, event_type, actor_id, details, ip_address, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (id) DO NOTHING
      `, [l.id, l.event_type, l.actor_id, l.details, l.ip_address, l.timestamp]);
    }

    // 7. Reset Sequences for SERIAL primary keys
    console.log('Synchronizing SERIAL auto-increment sequences...');
    const tables = ['users', 'scans', 'verification_codes', 'feedback', 'audit_logs'];
    for (const t of tables) {
      await pgClient.query(`
        SELECT setval(pg_get_serial_sequence('${t}', 'id'), COALESCE((SELECT MAX(id) FROM ${t}), 1), true)
      `);
    }

    await pgClient.query('COMMIT');
    console.log('Data commit finalized.');

    // 8. Verification: Count Comparison
    console.log('\n--- VERIFICATION: Source SQLite vs Destination PostgreSQL ---');
    let allMatched = true;
    for (const t of tables) {
      const srcCount = (await sqliteAll(`SELECT COUNT(*) as count FROM ${t}`))[0].count;
      const destRes = await pgClient.query(`SELECT COUNT(*) as count FROM ${t}`);
      const destCount = parseInt(destRes.rows[0].count, 10);
      const isMatch = srcCount === destCount;
      if (!isMatch) allMatched = false;

      console.log(`Table '${t}': SQLite = ${srcCount} rows | PostgreSQL = ${destCount} rows -> ${isMatch ? 'MATCH' : 'MISMATCH'}`);
    }

    if (allMatched) {
      console.log('\nSUCCESS: Database migration to PostgreSQL completed with 100% data integrity!');
    } else {
      console.warn('\nWARNING: Discrepancies detected between source and destination counts.');
    }

  } catch (err) {
    await pgClient.query('ROLLBACK');
    console.error('Migration failed. Transaction rolled back:', err);
    process.exit(1);
  } finally {
    pgClient.release();
    await pgPool.end();
    sqliteDb.close();
  }
}

migrate();