const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const APK_PATH = path.join(__dirname, '..', 'public', 'apk', 'RubberGuard-AI-release.apk');

// GET /api/apk/info
router.get('/info', (req, res) => {
  let sizeMb = '162.4';
  let sizeBytes = 170288508;

  if (fs.existsSync(APK_PATH)) {
    const stats = fs.statSync(APK_PATH);
    sizeMb = (stats.size / (1024 * 1024)).toFixed(1);
    sizeBytes = stats.size;
  }

  res.json({
    success: true,
    appName: 'RubberGuard AI',
    fileName: 'RubberGuard-AI-release.apk',
    versionName: '1.0.0',
    versionCode: 1,
    fileSize: `${sizeMb} MB`,
    sizeBytes,
    releaseDate: '2026-10-28',
    minimumAndroid: 'Android 8.0 (API Level 26)',
    targetAndroid: 'Android 14 (API Level 34)',
    architecture: 'Universal (arm64-v8a, armeabi-v7a, x86_64)',
    bundledEngine: 'MobileNetV2 (TFLite) + OpenCV Android SDK',
    downloadUrl: '/api/apk/download'
  });
});

// GET /api/apk/download
router.get('/download', (req, res) => {
  // If external release URL is configured (e.g. GitHub Releases for >100MB files), redirect directly
  if (process.env.APK_DOWNLOAD_URL) {
    return res.redirect(302, process.env.APK_DOWNLOAD_URL);
  }

  if (!fs.existsSync(APK_PATH)) {
    return res.status(404).send('APK file not found on server. Please download from the official GitHub Release or contact administrator.');
  }

  const stat = fs.statSync(APK_PATH);
  res.writeHead(200, {
    'Content-Type': 'application/vnd.android.package-archive',
    'Content-Length': stat.size,
    'Content-Disposition': 'attachment; filename="RubberGuard-AI-release.apk"'
  });

  const readStream = fs.createReadStream(APK_PATH);
  readStream.pipe(res);
});

module.exports = router;