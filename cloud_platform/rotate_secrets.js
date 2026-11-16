const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const bcrypt = require('bcryptjs');
const dotenv = require('dotenv');

// Load environment from cloud_platform/.env
const envPath = path.join(__dirname, '.env');
if (!fs.existsSync(envPath)) {
  console.error('.env file not found at:', envPath);
  process.exit(1);
}

const envConfig = dotenv.parse(fs.readFileSync(envPath));

function generateSecurePassword(length = 24) {
  // Use characters safe from shell and dotenv comment interpretation
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@$%^&*()_+=';
  let password = '';
  const randomBytes = crypto.randomBytes(length);
  for (let i = 0; i < length; i++) {
    password += chars[randomBytes[i] % chars.length];
  }
  return password;
}

async function runRotation() {
  console.log('--- Rotating Production Secrets ---');

  // 1. Generate secrets
  const newJwtSecret = crypto.randomBytes(32).toString('hex');
  const newAdminPassword = generateSecurePassword(24);
  const passwordHash = await bcrypt.hash(newAdminPassword, 10);
  const adminEmail = envConfig.ADMIN_EMAIL || 'admin@rubberguard.org';

  console.log('Generated new 256-bit JWT secret (64-character hex).');
  console.log('Generated new high-entropy admin password (24 characters).');

  // 2. Update PostgreSQL (Neon)
  if (envConfig.DATABASE_URL) {
    const { Pool } = require('pg');
    const pool = new Pool({
      connectionString: envConfig.DATABASE_URL,
      ssl: { rejectUnauthorized: false }
    });
    try {
      const res = await pool.query(
        'UPDATE users SET password_hash = $1 WHERE email = $2 OR username = $3',
        [passwordHash, adminEmail, 'admin']
      );
      console.log(`Neon PostgreSQL admin password hash updated. Rows affected: ${res.rowCount}`);
    } catch (err) {
      console.error('PostgreSQL update error:', err.message);
    } finally {
      await pool.end();
    }
  }

  // 3. Update local SQLite database
  const sqlite3 = require('sqlite3').verbose();
  const dbPath = path.join(__dirname, 'rubberguard_cloud.db');
  if (fs.existsSync(dbPath)) {
    const sqliteDb = new sqlite3.Database(dbPath);
    await new Promise((resolve) => {
      sqliteDb.run(
        'UPDATE users SET password_hash = ? WHERE email = ? OR username = ?',
        [passwordHash, adminEmail, 'admin'],
        function(err) {
          if (err) {
            console.error('SQLite update error:', err.message);
          } else {
            console.log(`Local SQLite admin password hash updated. Rows affected: ${this.changes}`);
          }
          sqliteDb.close();
          resolve();
        }
      );
    });
  }

  // 4. Update .env file content securely without printing secrets
  let envRaw = fs.readFileSync(envPath, 'utf8');
  if (envRaw.includes('JWT_SECRET=')) {
    envRaw = envRaw.replace(/^JWT_SECRET=.*$/m, `JWT_SECRET=${newJwtSecret}`);
  } else {
    envRaw += `\nJWT_SECRET=${newJwtSecret}`;
  }

  if (envRaw.includes('ADMIN_PASSWORD=')) {
    envRaw = envRaw.replace(/^ADMIN_PASSWORD=.*$/m, `ADMIN_PASSWORD="${newAdminPassword}"`);
  } else {
    envRaw += `\nADMIN_PASSWORD="${newAdminPassword}"`;
  }

  fs.writeFileSync(envPath, envRaw, 'utf8');
  console.log('Updated cloud_platform/.env with rotated credentials.');
  console.log('Rotation completed successfully. No credentials printed to console.');
}

runRotation().catch(err => {
  console.error('Rotation failed:', err.message);
  process.exit(1);
});
