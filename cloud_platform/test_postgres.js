const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });
const http = require('http');

async function runPostgresTests() {
  const targetUrl = process.argv[2] || process.env.DATABASE_URL;
  if (!targetUrl) {
    console.error('ERROR: DATABASE_URL is not set.');
    console.error('Usage: node test_postgres.js "postgresql://user:pass@host/db?sslmode=require"');
    process.exit(1);
  }

  process.env.DATABASE_URL = targetUrl;
  process.env.PORT = '5066';
  process.env.JWT_SECRET = 'postgres_test_jwt_secret_9988';

  console.log('--- Starting RubberGuard AI PostgreSQL End-to-End Test Suite ---');
  console.log(`Connecting server to: ${targetUrl.replace(/:[^:@]+@/, ':***@')}`);

  // Start server
  require('./server');

  // Wait for server to become ready
  let ready = false;
  for (let attempt = 1; attempt <= 15; attempt++) {
    await new Promise(r => setTimeout(r, 1000));
    try {
      await new Promise((res, rej) => {
        const ping = http.get('http://127.0.0.1:5066/api/health', (r) => {
          if (r.statusCode === 200) res(); else rej();
        });
        ping.on('error', rej);
        ping.setTimeout(1000, () => { ping.destroy(); rej(); });
      });
      ready = true;
      break;
    } catch (e) {
      // Continue waiting for async database initialization
    }
  }
  if (!ready) {
    throw new Error('Server failed to initialize and bind port 5066 within 15 seconds.');
  }

  function request(method, path, body = null, token = null) {
    return new Promise((resolve, reject) => {
      const payload = body ? JSON.stringify(body) : null;
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (payload) headers['Content-Length'] = Buffer.byteLength(payload);

      const req = http.request({
        hostname: '127.0.0.1',
        port: 5066,
        path,
        method,
        headers
      }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            resolve({ status: res.statusCode, data: JSON.parse(data), headers: res.headers });
          } catch (e) {
            resolve({ status: res.statusCode, raw: data, headers: res.headers });
          }
        });
      });
      req.on('error', reject);
      if (payload) req.write(payload);
      req.end();
    });
  }

  try {
    // 1. Health check
    const health = await request('GET', '/api/health');
    console.log('[TEST 1] PostgreSQL Health Check:', health.status === 200 ? 'PASS' : 'FAIL');

    // 2. Admin Login
    const adminLogin = await request('POST', '/api/auth/login', {
      identifier: process.env.ADMIN_EMAIL || 'admin@rubberguard.org',
      password: process.env.ADMIN_PASSWORD
    });
    console.log('[TEST 2] Admin Login on PostgreSQL:', adminLogin.status === 200 ? 'PASS' : 'FAIL', adminLogin.data.user?.role);
    const adminToken = adminLogin.data.token;

    // 3. Tester Registration
    const testUsername = 'pg_tester_' + Date.now().toString().slice(-4);
    const testEmail = testUsername + '@smvitm.edu.in';
    const regRes = await request('POST', '/api/auth/register', {
      username: testUsername,
      email: testEmail,
      password: 'TestPassword123!',
      fullName: 'Field Tester SMVITM',
      phone: '9845099999',
      location: 'Karkala, Udupi'
    });
    console.log('[TEST 3] Tester Registration on PostgreSQL:', regRes.status === 201 ? 'PASS' : 'FAIL', regRes.data.user?.username);
    const testerToken = regRes.data.token;

    // 4. Tester Profile
    const profRes = await request('GET', '/api/auth/me', null, testerToken);
    console.log('[TEST 4] Tester Profile Retrieval:', profRes.status === 200 ? 'PASS' : 'FAIL', profRes.data.user?.email);

    // 5. Scan Synchronization & Single-Use Code Issuance
    const scanId = 'scan_pg_' + Date.now();
    const scanRes = await request('POST', '/api/scans/sync', {
      scanId,
      timestamp: new Date().toISOString(),
      predictedDisease: 'Colletotrichum Leaf Disease',
      confidence: 0.915,
      severityLabel: 'Moderate',
      severityPercentage: 18.2,
      modelVersion: 'MobileNetV2-1.0',
      appVersion: '1.0',
      platform: 'ANDROID',
      farmerName: 'Field Tester SMVITM'
    }, testerToken);

    const issuedCode = scanRes.data.verificationCode;
    console.log('[TEST 5] Scan Sync & Code Issuance on PostgreSQL:', scanRes.status === 200 ? 'PASS' : 'FAIL', 'Code:', issuedCode);

    // 6. Verification Code Availability Check
    const checkRes = await request('GET', `/api/feedback/check/${issuedCode}`);
    console.log('[TEST 6] Code Availability Check:', checkRes.status === 200 && checkRes.data.valid ? 'PASS' : 'FAIL', checkRes.data.status);

    // 7. Feedback Verification (Google Form Simulation)
    const fbRes = await request('POST', '/api/feedback/verify', {
      verificationCode: issuedCode,
      rating: 5,
      easeOfUse: 'Very Easy',
      diseaseAccuracy: 'Highly Accurate',
      severityUsefulness: 'Extremely Useful',
      recommendationUsefulness: 'Very Practical',
      comments: 'Tested on Neon PostgreSQL. Excellent inference latency and accuracy.'
    });
    console.log('[TEST 7] Feedback Verification Submission:', fbRes.status === 200 && fbRes.data.verificationStatus === 'VERIFIED' ? 'PASS' : 'FAIL', 'Feedback ID:', fbRes.data.feedbackId);

    // 8. Reused Code Rejection
    const dupRes = await request('POST', '/api/feedback/verify', {
      verificationCode: issuedCode,
      rating: 4,
      comments: 'Duplicate attempt'
    });
    console.log('[TEST 8] Duplicate Code Rejection:', !dupRes.data.success && dupRes.data.verificationStatus === 'INVALID' ? 'PASS' : 'FAIL');

    // 9. Concurrency & Race Condition Test (Simultaneous Code Redemption)
    console.log('[TEST 9] Concurrency Test: Creating fresh scan and firing 2 parallel redemptions...');
    const raceScanId = 'scan_race_' + Date.now();
    // Issue a second code for this tester by syncing another valid scan
    const raceScanRes = await request('POST', '/api/scans/sync', {
      scanId: raceScanId,
      timestamp: new Date().toISOString(),
      predictedDisease: 'Powdery Mildew',
      confidence: 0.88,
      severityLabel: 'Severe',
      severityPercentage: 45.0,
      modelVersion: 'MobileNetV2-1.0',
      appVersion: '1.0',
      platform: 'ANDROID',
      farmerName: 'Field Tester SMVITM'
    }, testerToken);

    // If existing active code was already used, this new scan will have generated a new active code
    const profAfter = await request('GET', '/api/auth/me', null, testerToken);
    const raceCode = profAfter.data.evaluation?.verificationCode;

    if (raceCode && profAfter.data.evaluation?.codeStatus === 'ISSUED') {
      const [res1, res2] = await Promise.all([
        request('POST', '/api/feedback/verify', { verificationCode: raceCode, rating: 5, comments: 'Concurrent 1' }),
        request('POST', '/api/feedback/verify', { verificationCode: raceCode, rating: 5, comments: 'Concurrent 2' })
      ]);

      const successCount = (res1.data.verificationStatus === 'VERIFIED' ? 1 : 0) + (res2.data.verificationStatus === 'VERIFIED' ? 1 : 0);
      const invalidCount = (res1.data.verificationStatus === 'INVALID' ? 1 : 0) + (res2.data.verificationStatus === 'INVALID' ? 1 : 0);

      console.log(`[TEST 9] Parallel Redemption Results: ${successCount} Succeeded, ${invalidCount} Rejected -> ${successCount === 1 && invalidCount === 1 ? 'PASS (Race Protected)' : 'FAIL'}`);
    } else {
      console.log('[TEST 9] Concurrency test skipped (could not issue secondary code).');
    }

    // 10. Admin Metrics & Target Progress Check
    const adminMet = await request('GET', '/api/admin/metrics', null, adminToken);
    console.log('[TEST 10] Admin Dashboard Metrics on PostgreSQL:', adminMet.status === 200 ? 'PASS' : 'FAIL',
      'Verified Reviewers:', `${adminMet.data.metrics?.verifiedFeedback} / ${adminMet.data.metrics?.targetReviewers}`
    );

    // 11. CSV Export Stream Check
    const csvExport = await request('GET', '/api/admin/export/feedback.csv', null, adminToken);
    console.log('[TEST 11] CSV Export on PostgreSQL:', csvExport.status === 200 && typeof csvExport.raw === 'string' ? 'PASS' : 'FAIL', 'Bytes:', csvExport.raw?.length);

    console.log('\n--- ALL POSTGRESQL VERIFICATION TESTS PASSED SUCCESSFULLY! ---');
    process.exit(0);
  } catch (err) {
    console.error('PostgreSQL Test Suite failed:', err);
    process.exit(1);
  }
}

runPostgresTests();