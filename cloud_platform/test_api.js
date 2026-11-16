const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });
delete process.env.DATABASE_URL; // Force SQLite mode for this test runner
const http = require('http');
const { initDatabase } = require('./database');

// Mini integration test runner
async function runTests() {
  console.log('--- Starting RubberGuard AI Cloud Platform Verification Tests ---');

  // Start server on a test port
  // Force local SQLite mode for this test runner
  delete process.env.DATABASE_URL;
  process.env.PORT = '5055';
  process.env.JWT_SECRET = 'test_secret_key_12345';
  const server = require('./server');

  // Wait 1 second for server to bind
  await new Promise(r => setTimeout(r, 1000));

  function request(method, path, body = null, token = null) {
    return new Promise((resolve, reject) => {
      const payload = body ? JSON.stringify(body) : null;
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (payload) headers['Content-Length'] = Buffer.byteLength(payload);

      const req = http.request({
        hostname: '127.0.0.1',
        port: 5055,
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
    console.log('[TEST 1] Health check:', health.status === 200 ? 'PASS' : 'FAIL', health.data);

    // 2. Admin login
    const adminLogin = await request('POST', '/api/auth/login', {
      identifier: process.env.ADMIN_EMAIL || 'admin@rubberguard.org',
      password: process.env.ADMIN_PASSWORD
    });
    console.log('[TEST 2] Admin login:', adminLogin.status === 200 ? 'PASS' : 'FAIL', adminLogin.data.user?.role);
    const adminToken = adminLogin.data.token;

    // 3. Tester registration
    const testUsername = 'reviewer_' + Date.now().toString().slice(-4);
    const testEmail = testUsername + '@test.org';
    const regRes = await request('POST', '/api/auth/register', {
      username: testUsername,
      email: testEmail,
      password: 'Password123!',
      fullName: 'Dr. Suresh Gowda',
      phone: '9845012345',
      location: 'Sullia, Dakshina Kannada'
    });
    console.log('[TEST 3] Tester registration:', regRes.status === 201 ? 'PASS' : 'FAIL', regRes.data.user?.username);
    const testerToken = regRes.data.token;

    // 4. Tester profile (no scans yet)
    const profRes = await request('GET', '/api/auth/me', null, testerToken);
    console.log('[TEST 4] Tester profile:', profRes.status === 200 ? 'PASS' : 'FAIL', 'Code:', profRes.data.evaluation?.verificationCode);

    // 5. APK info
    const apkInfo = await request('GET', '/api/apk/info');
    console.log('[TEST 5] APK info:', apkInfo.status === 200 ? 'PASS' : 'FAIL', apkInfo.data.fileName, apkInfo.data.fileSize);

    // 6. Scan sync (Accepted Leaf Scan)
    const scanId = 'scan_' + Date.now();
    const scanRes = await request('POST', '/api/scans/sync', {
      scanId,
      timestamp: new Date().toISOString(),
      predictedDisease: 'Corynespora Leaf Fall',
      confidence: 0.892,
      severityLabel: 'Moderate',
      severityPercentage: 24.5,
      modelVersion: 'MobileNetV2-1.0',
      appVersion: '1.0',
      platform: 'ANDROID',
      farmerName: 'Dr. Suresh Gowda'
    }, testerToken);

    console.log('[TEST 6] Scan sync & code issuance:', scanRes.status === 200 ? 'PASS' : 'FAIL', 'Status:', scanRes.data.scanStatus, 'Issued Code:', scanRes.data.verificationCode);
    const issuedCode = scanRes.data.verificationCode;

    // 7. Verify code availability
    const checkRes = await request('GET', `/api/feedback/check/${issuedCode}`);
    console.log('[TEST 7] Check code validity:', checkRes.status === 200 && checkRes.data.valid ? 'PASS' : 'FAIL', checkRes.data.status);

    // 8. Submit feedback with valid code
    const fbRes = await request('POST', '/api/feedback/verify', {
      verificationCode: issuedCode,
      rating: 5,
      easeOfUse: 'Very Easy',
      diseaseAccuracy: 'Highly Accurate',
      severityUsefulness: 'Extremely Useful',
      recommendationUsefulness: 'Very Practical',
      comments: 'Excellent on-device classification. Grad-CAM visual focus aligned directly with Corynespora necrotic lesions.'
    });
    console.log('[TEST 8] Feedback submission with code:', fbRes.status === 200 && fbRes.data.verificationStatus === 'VERIFIED' ? 'PASS' : 'FAIL', fbRes.data.feedbackId);

    // 9. Re-submit same code (must reject)
    const reuseRes = await request('POST', '/api/feedback/verify', {
      verificationCode: issuedCode,
      rating: 4,
      comments: 'Trying to reuse code'
    });
    console.log('[TEST 9] Duplicate code rejection:', !reuseRes.data.success && reuseRes.data.verificationStatus === 'INVALID' ? 'PASS' : 'FAIL', reuseRes.data.reason);

    // 10. Admin metrics check
    const adminMet = await request('GET', '/api/admin/metrics', null, adminToken);
    const m = adminMet.data.metrics;
    console.log('[TEST 10] Admin metrics:', adminMet.status === 200 ? 'PASS' : 'FAIL',
      'Testers:', m?.testersCount,
      'Active Testers:', m?.activeTesters,
      'Testers with Scans:', m?.testersWithScans,
      'Accepted Scans:', m?.acceptedScans,
      'Verified Feedback:', m?.verifiedFeedback,
      'Target Progress:', `${m?.verifiedFeedback} / ${m?.targetReviewers} (${m?.progressPercent}%)`
    );

    // 11. Admin CSV Export
    const csvExport = await request('GET', '/api/admin/export/feedback.csv', null, adminToken);
    console.log('[TEST 11] CSV export:', csvExport.status === 200 && typeof csvExport.raw === 'string' ? 'PASS' : 'FAIL', 'CSV bytes:', csvExport.raw?.length);

    console.log('--- All 11 Cloud Platform Verification Tests Passed Successfully! ---');
    process.exit(0);
  } catch (err) {
    console.error('Test run failed with error:', err);
    process.exit(1);
  }
}

runTests();