const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const { dbRun, dbGet, dbAll } = require('../database');

// GET /api/feedback/check/:code
// Publicly verify whether a code is valid, unused, and unexpired
router.get('/check/:code', async (req, res) => {
  try {
    const rawCode = req.params.code ? req.params.code.trim().toUpperCase() : '';
    if (!rawCode) {
      return res.status(400).json({ success: false, valid: false, error: 'Verification code required' });
    }

    const codeRecord = await dbGet('SELECT * FROM verification_codes WHERE code = ?', [rawCode]);
    if (!codeRecord) {
      return res.json({
        success: true,
        valid: false,
        status: 'NOT_FOUND',
        reason: 'Verification code does not exist. Ensure you completed a leaf scan in the RubberGuard Android app.'
      });
    }

    if (codeRecord.status === 'USED') {
      return res.json({
        success: true,
        valid: false,
        status: 'ALREADY_USED',
        reason: `Verification code was already used on ${codeRecord.used_at}.`
      });
    }

    const isExpired = new Date(codeRecord.expires_at) < new Date();
    if (isExpired) {
      return res.json({
        success: true,
        valid: false,
        status: 'EXPIRED',
        reason: 'Verification code has expired.'
      });
    }

    const tester = await dbGet('SELECT uid, full_name, username FROM users WHERE uid = ?', [codeRecord.tester_id]);

    res.json({
      success: true,
      valid: true,
      status: 'AVAILABLE',
      testerName: tester ? tester.full_name : 'Verified Tester',
      scanId: codeRecord.scan_id,
      expiresAt: codeRecord.expires_at
    });
  } catch (err) {
    console.error('Check code error:', err);
    res.status(500).json({ success: false, error: 'Failed to verify code' });
  }
});

// POST /api/feedback/verify
// Called by Google Apps Script onFormSubmit OR directly from web tester portal
router.post('/verify', async (req, res) => {
  try {
    const {
      verificationCode,
      rating,
      easeOfUse,
      diseaseAccuracy,
      severityUsefulness,
      recommendationUsefulness,
      comments,
      rawAnswers,
      respondentEmail
    } = req.body;

    const cleanCode = verificationCode ? verificationCode.trim().toUpperCase() : '';
    if (!cleanCode) {
      return res.status(400).json({
        success: false,
        verificationStatus: 'INVALID',
        reason: 'Verification code is missing from submission'
      });
    }

    const codeRecord = await dbGet('SELECT * FROM verification_codes WHERE code = ?', [cleanCode]);

    // Case 1: Code not found
    if (!codeRecord) {
      // Record rejected feedback for audit
      const rejectFbId = 'fb_rej_' + crypto.randomBytes(4).toString('hex');
      await dbRun(
        `INSERT INTO feedback (feedback_id, verification_code, overall_rating, comments, answers_json, verification_status, status_reason)
         VALUES (?, ?, ?, ?, ?, 'INVALID', 'Verification code does not exist in backend')`,
        [rejectFbId, cleanCode, rating || 0, comments || '', JSON.stringify(rawAnswers || {})]
      );

      return res.json({
        success: false,
        verificationStatus: 'INVALID',
        reason: 'Verification code not recognized. Tester must run a valid scan on the Android app first.'
      });
    }

    // Case 2: Code already used
    if (codeRecord.status === 'USED') {
      return res.json({
        success: false,
        verificationStatus: 'INVALID',
        reason: `Verification code was already redeemed on ${codeRecord.used_at}. One feedback per valid scan only.`
      });
    }

    // Case 3: Code expired
    if (new Date(codeRecord.expires_at) < new Date()) {
      return res.json({
        success: false,
        verificationStatus: 'INVALID',
        reason: 'Verification code has expired.'
      });
    }

    // Case 4: Valid code -> Atomically consume and record verified feedback
    const feedbackId = 'fb_' + crypto.randomBytes(6).toString('hex');

    // Mark code as USED
    await dbRun(
      "UPDATE verification_codes SET status = 'USED', used_at = CURRENT_TIMESTAMP WHERE id = ?",
      [codeRecord.id]
    );

    // Insert verified feedback
    await dbRun(
      `INSERT INTO feedback (
        feedback_id, verification_code, tester_id, submission_timestamp,
        overall_rating, ease_of_use, disease_accuracy_rating, severity_usefulness,
        recommendation_usefulness, comments, answers_json, verification_status, status_reason
      ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, 'VERIFIED', 'Successfully matched valid leaf scan')`,
      [
        feedbackId,
        cleanCode,
        codeRecord.tester_id,
        parseInt(rating || 5, 10),
        easeOfUse || 'Easy',
        diseaseAccuracy || 'Accurate',
        severityUsefulness || 'Very Useful',
        recommendationUsefulness || 'Helpful',
        comments || '',
        JSON.stringify(rawAnswers || {})
      ]
    );

    // Audit log
    await dbRun(
      `INSERT INTO audit_logs (event_type, actor_id, details, ip_address)
       VALUES ('FEEDBACK_VERIFIED', ?, ?, ?)`,
      [codeRecord.tester_id, `Feedback ${feedbackId} verified with code ${cleanCode}`, req.ip || '127.0.0.1']
    );

    res.json({
      success: true,
      verificationStatus: 'VERIFIED',
      feedbackId,
      message: 'Evaluation feedback successfully verified and recorded in RubberGuard AI cloud registry.'
    });
  } catch (err) {
    console.error('Feedback verification error:', err);
    res.status(500).json({ success: false, error: 'Internal server error processing feedback' });
  }
});

// GET /api/feedback/summary
router.get('/summary', async (req, res) => {
  try {
    const verifiedCount = await dbGet("SELECT COUNT(*) as count FROM feedback WHERE verification_status = 'VERIFIED'");
    const invalidCount = await dbGet("SELECT COUNT(*) as count FROM feedback WHERE verification_status = 'INVALID'");
    const avgRating = await dbGet("SELECT AVG(overall_rating) as avg FROM feedback WHERE verification_status = 'VERIFIED'");

    res.json({
      success: true,
      totalVerified: verifiedCount ? verifiedCount.count : 0,
      totalInvalid: invalidCount ? invalidCount.count : 0,
      averageRating: avgRating && avgRating.avg ? parseFloat(avgRating.avg).toFixed(2) : '5.00'
    });
  } catch (err) {
    console.error('Feedback summary error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch summary' });
  }
});

module.exports = router;