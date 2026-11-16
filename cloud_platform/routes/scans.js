const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const { dbRun, dbGet, dbAll } = require('../database');
const { authenticateToken } = require('./auth');

// Helper: Generate secure 6-character alphanumeric verification code formatted as RG-XXXXXX
function generateVerificationCode() {
  const chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'; // Exclude visually ambiguous chars: 0, 1, I, O
  let code = 'RG-';
  for (let i = 0; i < 6; i++) {
    const randomIndex = crypto.randomInt(0, chars.length);
    code += chars[randomIndex];
  }
  return code;
}

// POST /api/scans/sync
// Receives scan from Android app (or web tester simulator)
router.post('/sync', authenticateToken, async (req, res) => {
  try {
    const testerId = req.user.uid;
    const {
      scanId,
      timestamp,
      predictedDisease,
      confidence,
      severityLabel,
      severityPercentage,
      modelVersion,
      appVersion,
      platform,
      farmerName
    } = req.body;

    if (!scanId || !predictedDisease || confidence === undefined) {
      return res.status(400).json({
        success: false,
        error: 'Missing required scan data: scanId, predictedDisease, and confidence are mandatory'
      });
    }

    // Check duplicate scanId
    const existingScan = await dbGet('SELECT * FROM scans WHERE scan_id = ?', [scanId]);
    if (existingScan) {
      // If already recorded, return its current status and linked verification code
      const linkedCode = await dbGet('SELECT code, status FROM verification_codes WHERE scan_id = ?', [scanId]);
      return res.json({
        success: true,
        message: 'Scan already recorded',
        scanStatus: existingScan.scan_status,
        verificationCode: linkedCode ? linkedCode.code : null,
        codeStatus: linkedCode ? linkedCode.status : null
      });
    }

    // Validate Scan criteria
    const disLower = predictedDisease.toLowerCase();
    const isOodOrClutter =
      disLower.includes('uncertain') ||
      disLower.includes('invalid') ||
      disLower.includes('background') ||
      disLower.includes('no leaf') ||
      disLower.includes('blurred');

    let scanStatus = 'ACCEPTED';
    let rejectionReason = null;

    if (isOodOrClutter) {
      scanStatus = 'REJECTED';
      rejectionReason = 'Out of distribution / non-leaf clutter or blurred image';
    } else if (confidence < 0.40) {
      scanStatus = 'REJECTED';
      rejectionReason = 'Model confidence below acceptable evaluation threshold';
    }

    // Record scan in database
    await dbRun(
      `INSERT INTO scans (
        scan_id, tester_id, farmer_name, timestamp, predicted_disease, confidence,
        severity_label, severity_percentage, model_version, app_version, platform,
        scan_status, rejection_reason, sync_timestamp
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`,
      [
        scanId,
        testerId,
        farmerName || req.user.fullName || 'Tester',
        timestamp || new Date().toISOString(),
        predictedDisease,
        parseFloat(confidence),
        severityLabel || 'Trace',
        parseFloat(severityPercentage || 0),
        modelVersion || 'MobileNetV2-1.0',
        appVersion || '1.0',
        platform || 'ANDROID',
        scanStatus,
        rejectionReason
      ]
    );

    let issuedCode = null;
    let codeStatus = null;

    if (scanStatus === 'ACCEPTED') {
      // Check if user already has an active, unused verification code
      const existingActiveCode = await dbGet(
        "SELECT * FROM verification_codes WHERE tester_id = ? AND status = 'ISSUED'",
        [testerId]
      );

      if (existingActiveCode) {
        issuedCode = existingActiveCode.code;
        codeStatus = existingActiveCode.status;
        // Link this scan to the code
        await dbRun('UPDATE scans SET verification_code_id = ? WHERE scan_id = ?', [issuedCode, scanId]);
      } else {
        // Generate new single-use verification code
        let uniqueCode = generateVerificationCode();
        let codeCollision = await dbGet('SELECT id FROM verification_codes WHERE code = ?', [uniqueCode]);
        while (codeCollision) {
          uniqueCode = generateVerificationCode();
          codeCollision = await dbGet('SELECT id FROM verification_codes WHERE code = ?', [uniqueCode]);
        }

        const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(); // 30 days validity
        await dbRun(
          `INSERT INTO verification_codes (code, tester_id, scan_id, created_at, expires_at, status)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, 'ISSUED')`,
          [uniqueCode, testerId, scanId, expiresAt]
        );

        await dbRun('UPDATE scans SET verification_code_id = ? WHERE scan_id = ?', [uniqueCode, scanId]);
        issuedCode = uniqueCode;
        codeStatus = 'ISSUED';
      }

      // Audit log
      await dbRun(
        `INSERT INTO audit_logs (event_type, actor_id, details, ip_address)
         VALUES ('SCAN_ACCEPTED', ?, ?, ?)`,
        [testerId, `Scan ${scanId} accepted. Code: ${issuedCode}`, req.ip || '127.0.0.1']
      );
    } else {
      // Audit log for rejection
      await dbRun(
        `INSERT INTO audit_logs (event_type, actor_id, details, ip_address)
         VALUES ('SCAN_REJECTED', ?, ?, ?)`,
        [testerId, `Scan ${scanId} rejected: ${rejectionReason}`, req.ip || '127.0.0.1']
      );
    }

    res.json({
      success: true,
      scanStatus,
      rejectionReason,
      verificationCode: issuedCode,
      codeStatus,
      instructions: issuedCode
        ? 'Please use this verification code when filling out the project feedback Google Form.'
        : 'Scan did not meet criteria for verification code generation. Ensure the rubber leaf is clearly focused in natural lighting.'
    });
  } catch (err) {
    console.error('Scan sync error:', err);
    res.status(500).json({ success: false, error: 'Failed to record scan' });
  }
});

// GET /api/scans/my-scans
router.get('/my-scans', authenticateToken, async (req, res) => {
  try {
    const scans = await dbAll(
      `SELECT scan_id, timestamp, predicted_disease, confidence, severity_label,
              severity_percentage, scan_status, rejection_reason, verification_code_id
       FROM scans WHERE tester_id = ? ORDER BY id DESC`,
      [req.user.uid]
    );

    const activeCode = await dbGet(
      'SELECT code, status, expires_at, created_at FROM verification_codes WHERE tester_id = ? ORDER BY id DESC LIMIT 1',
      [req.user.uid]
    );

    res.json({
      success: true,
      scans,
      activeCode: activeCode || null
    });
  } catch (err) {
    console.error('Fetch scans error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch scans' });
  }
});

module.exports = router;