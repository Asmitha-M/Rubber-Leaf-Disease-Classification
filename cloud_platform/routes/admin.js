const express = require('express');
const router = express.Router();
const { dbRun, dbGet, dbAll } = require('../database');
const { authenticateToken } = require('./auth');

// Middleware to enforce admin role
function requireAdmin(req, res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ success: false, error: 'Administrator access required' });
  }
  next();
}

router.use(authenticateToken);
router.use(requireAdmin);

// GET /api/admin/metrics
router.get('/metrics', async (req, res) => {
  try {
    const totalUsers = await dbGet("SELECT COUNT(*) as count FROM users WHERE role = 'tester'");
    const activeTesters = await dbGet("SELECT COUNT(DISTINCT id) as count FROM users WHERE role = 'tester' AND (last_login_at IS NOT NULL OR uid IN (SELECT DISTINCT tester_id FROM scans))");
    const testersWithScans = await dbGet("SELECT COUNT(DISTINCT tester_id) as count FROM scans WHERE scan_status = 'ACCEPTED'");
    const totalScans = await dbGet("SELECT COUNT(*) as count FROM scans");
    const acceptedScans = await dbGet("SELECT COUNT(*) as count FROM scans WHERE scan_status = 'ACCEPTED'");
    const rejectedScans = await dbGet("SELECT COUNT(*) as count FROM scans WHERE scan_status = 'REJECTED'");

    const codesIssued = await dbGet("SELECT COUNT(*) as count FROM verification_codes");
    const codesUsed = await dbGet("SELECT COUNT(*) as count FROM verification_codes WHERE status = 'USED'");

    const verifiedFeedback = await dbGet("SELECT COUNT(*) as count FROM feedback WHERE verification_status = 'VERIFIED'");
    const invalidFeedback = await dbGet("SELECT COUNT(*) as count FROM feedback WHERE verification_status = 'INVALID'");
    const avgRating = await dbGet("SELECT AVG(overall_rating) as avg FROM feedback WHERE verification_status = 'VERIFIED'");

    // Disease breakdown
    const diseaseBreakdown = await dbAll(
      `SELECT predicted_disease as disease, COUNT(*) as count
       FROM scans WHERE scan_status = 'ACCEPTED'
       GROUP BY predicted_disease ORDER BY count DESC`
    );

    // Target calculation (e.g. 20 reviewers)
    const TARGET_REVIEWERS = 20;
    const currentVerified = verifiedFeedback ? verifiedFeedback.count : 0;
    const progressPercent = Math.min(100, Math.round((currentVerified / TARGET_REVIEWERS) * 100));

    res.json({
      success: true,
      metrics: {
        testersCount: totalUsers ? totalUsers.count : 0,
        activeTesters: activeTesters ? activeTesters.count : 0,
        testersWithScans: testersWithScans ? testersWithScans.count : 0,
        totalScans: totalScans ? totalScans.count : 0,
        acceptedScans: acceptedScans ? acceptedScans.count : 0,
        rejectedScans: rejectedScans ? rejectedScans.count : 0,
        codesIssued: codesIssued ? codesIssued.count : 0,
        codesUsed: codesUsed ? codesUsed.count : 0,
        verifiedFeedback: currentVerified,
        invalidFeedback: invalidFeedback ? invalidFeedback.count : 0,
        averageRating: avgRating && avgRating.avg ? parseFloat(avgRating.avg).toFixed(1) : '0.0',
        targetReviewers: TARGET_REVIEWERS,
        progressPercent,
        diseaseBreakdown
      }
    });
  } catch (err) {
    console.error('Admin metrics error:', err);
    res.status(500).json({ success: false, error: 'Failed to calculate metrics' });
  }
});

// GET /api/admin/testers
router.get('/testers', async (req, res) => {
  try {
    const testers = await dbAll(`
      SELECT u.id, u.uid, u.username, u.email, u.full_name, u.phone, u.location, u.created_at, u.last_login_at,
             (SELECT COUNT(*) FROM scans s WHERE s.tester_id = u.uid AND s.scan_status = 'ACCEPTED') as accepted_scans,
             (SELECT code FROM verification_codes vc WHERE vc.tester_id = u.uid ORDER BY vc.id DESC LIMIT 1) as verification_code,
             (SELECT status FROM verification_codes vc WHERE vc.tester_id = u.uid ORDER BY vc.id DESC LIMIT 1) as code_status,
             (SELECT verification_status FROM feedback f WHERE f.tester_id = u.uid ORDER BY f.id DESC LIMIT 1) as feedback_status
      FROM users u
      WHERE u.role = 'tester'
      ORDER BY u.id DESC
    `);

    res.json({ success: true, testers });
  } catch (err) {
    console.error('Admin testers fetch error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch testers' });
  }
});

// GET /api/admin/scans
router.get('/scans', async (req, res) => {
  try {
    const scans = await dbAll(`
      SELECT s.id, s.scan_id, s.farmer_name, s.timestamp, s.predicted_disease, s.confidence,
             s.severity_label, s.severity_percentage, s.model_version, s.scan_status, s.rejection_reason,
             s.verification_code_id, u.username, u.email
      FROM scans s
      LEFT JOIN users u ON s.tester_id = u.uid
      ORDER BY s.id DESC
    `);

    res.json({ success: true, scans });
  } catch (err) {
    console.error('Admin scans fetch error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch scans' });
  }
});

// GET /api/admin/feedback
router.get('/feedback', async (req, res) => {
  try {
    const feedbackList = await dbAll(`
      SELECT f.id, f.feedback_id, f.verification_code, f.submission_timestamp, f.overall_rating,
             f.ease_of_use, f.disease_accuracy_rating, f.severity_usefulness, f.recommendation_usefulness,
             f.comments, f.verification_status, f.status_reason,
             u.full_name as tester_name, u.email as tester_email
      FROM feedback f
      LEFT JOIN users u ON f.tester_id = u.uid
      ORDER BY f.id DESC
    `);

    res.json({ success: true, feedback: feedbackList });
  } catch (err) {
    console.error('Admin feedback fetch error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch feedback' });
  }
});

// Helper: Escape CSV string
function escapeCsv(field) {
  if (field === null || field === undefined) return '""';
  const stringValue = String(field).replace(/"/g, '""');
  return `"${stringValue}"`;
}

// GET /api/admin/export/testers.csv
router.get('/export/testers.csv', async (req, res) => {
  try {
    const testers = await dbAll(`
      SELECT u.uid, u.username, u.email, u.full_name, u.phone, u.location, u.created_at,
             (SELECT COUNT(*) FROM scans s WHERE s.tester_id = u.uid AND s.scan_status = 'ACCEPTED') as accepted_scans,
             (SELECT code FROM verification_codes vc WHERE vc.tester_id = u.uid ORDER BY vc.id DESC LIMIT 1) as verification_code,
             (SELECT status FROM verification_codes vc WHERE vc.tester_id = u.uid ORDER BY vc.id DESC LIMIT 1) as code_status,
             (SELECT verification_status FROM feedback f WHERE f.tester_id = u.uid ORDER BY f.id DESC LIMIT 1) as feedback_status
      FROM users u
      WHERE u.role = 'tester'
      ORDER BY u.id ASC
    `);

    let csv = 'UID,Username,Email,Full Name,Phone,Location,Registration Date,Accepted Scans,Verification Code,Code Status,Feedback Status\n';
    testers.forEach(t => {
      csv += [
        escapeCsv(t.uid),
        escapeCsv(t.username),
        escapeCsv(t.email),
        escapeCsv(t.full_name),
        escapeCsv(t.phone),
        escapeCsv(t.location),
        escapeCsv(t.created_at),
        escapeCsv(t.accepted_scans),
        escapeCsv(t.verification_code || 'None'),
        escapeCsv(t.code_status || 'N/A'),
        escapeCsv(t.feedback_status || 'PENDING')
      ].join(',') + '\n';
    });

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="RubberGuard_Testers_Registry.csv"');
    res.send(csv);
  } catch (err) {
    console.error('CSV export error:', err);
    res.status(500).send('Failed to export CSV');
  }
});

// GET /api/admin/export/scans.csv
router.get('/export/scans.csv', async (req, res) => {
  try {
    const scans = await dbAll(`
      SELECT s.scan_id, u.full_name as tester_name, s.timestamp, s.predicted_disease,
             s.confidence, s.severity_label, s.severity_percentage, s.scan_status,
             s.rejection_reason, s.verification_code_id
      FROM scans s
      LEFT JOIN users u ON s.tester_id = u.uid
      ORDER BY s.id ASC
    `);

    let csv = 'Scan ID,Tester Name,Timestamp,Predicted Disease,Confidence,Severity Label,Severity %,Status,Rejection Reason,Verification Code\n';
    scans.forEach(s => {
      csv += [
        escapeCsv(s.scan_id),
        escapeCsv(s.tester_name || 'N/A'),
        escapeCsv(s.timestamp),
        escapeCsv(s.predicted_disease),
        escapeCsv((s.confidence * 100).toFixed(1) + '%'),
        escapeCsv(s.severity_label),
        escapeCsv(s.severity_percentage ? s.severity_percentage.toFixed(1) + '%' : '0%'),
        escapeCsv(s.scan_status),
        escapeCsv(s.rejection_reason || 'None'),
        escapeCsv(s.verification_code_id || 'None')
      ].join(',') + '\n';
    });

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="RubberGuard_Scan_Records.csv"');
    res.send(csv);
  } catch (err) {
    console.error('CSV export error:', err);
    res.status(500).send('Failed to export CSV');
  }
});

// GET /api/admin/export/feedback.csv
router.get('/export/feedback.csv', async (req, res) => {
  try {
    const feedbackList = await dbAll(`
      SELECT f.feedback_id, f.verification_code, f.submission_timestamp, f.overall_rating,
             f.ease_of_use, f.disease_accuracy_rating, f.severity_usefulness, f.recommendation_usefulness,
             f.comments, f.verification_status, u.full_name as tester_name, u.email as tester_email
      FROM feedback f
      LEFT JOIN users u ON f.tester_id = u.uid
      ORDER BY f.id ASC
    `);

    let csv = 'Feedback ID,Verification Code,Submission Date,Tester Name,Tester Email,Overall Rating (1-5),Ease of Use,Accuracy Rating,Severity Rating,Recommendation Rating,Comments,Verification Status\n';
    feedbackList.forEach(f => {
      csv += [
        escapeCsv(f.feedback_id),
        escapeCsv(f.verification_code),
        escapeCsv(f.submission_timestamp),
        escapeCsv(f.tester_name || 'Anonymous'),
        escapeCsv(f.tester_email || 'N/A'),
        escapeCsv(f.overall_rating),
        escapeCsv(f.ease_of_use),
        escapeCsv(f.disease_accuracy_rating),
        escapeCsv(f.severity_usefulness),
        escapeCsv(f.recommendation_usefulness),
        escapeCsv(f.comments),
        escapeCsv(f.verification_status)
      ].join(',') + '\n';
    });

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="RubberGuard_Verified_Feedback.csv"');
    res.send(csv);
  } catch (err) {
    console.error('CSV export error:', err);
    res.status(500).send('Failed to export CSV');
  }
});

module.exports = router;