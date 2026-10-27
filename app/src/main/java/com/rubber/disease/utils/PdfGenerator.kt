package com.rubber.disease.utils

import android.content.Context
import android.graphics.*
import android.graphics.pdf.PdfDocument
import com.rubber.disease.data.ScanRecordEntity
import java.io.File
import java.io.FileOutputStream

object PdfGenerator {

    /**
     * Generates a professional PDF diagnostic report for a rubber leaf scan.
     * @param context Android context.
     * @param record The scan record containing all metadata and image paths.
     * @param outputFile The destination file where the PDF will be saved.
     * @param isKannada Set true to output the report recommendations in Kannada.
     */
    fun generateReport(context: Context, record: ScanRecordEntity, outputFile: File, isKannada: Boolean) {
        val pdfDocument = PdfDocument()

        // Standard A4 Size: 595 x 842 points
        val pageInfo = PdfDocument.PageInfo.Builder(595, 842, 1).create()
        val page = pdfDocument.startPage(pageInfo)
        val canvas = page.canvas

        // Paint configurations
        val titlePaint = Paint().apply {
            color = 0xFF2E7D32.toInt() // Green
            textSize = 20f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }

        val textPaint = Paint().apply {
            color = Color.BLACK
            textSize = 12f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.NORMAL)
            isAntiAlias = true
        }

        val boldPaint = Paint().apply {
            color = Color.BLACK
            textSize = 12f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }

        val subHeaderPaint = Paint().apply {
            color = 0xFF1B5E20.toInt()
            textSize = 14f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }

        val rectPaint = Paint().apply {
            style = Paint.Style.FILL
            isAntiAlias = true
        }

        val borderPaint = Paint().apply {
            color = Color.LTGRAY
            style = Paint.Style.STROKE
            strokeWidth = 1f
            isAntiAlias = true
        }

        // 1. Draw Header Green Bar
        rectPaint.color = 0xFF2E7D32.toInt()
        canvas.drawRect(0f, 0f, 595f, 60f, rectPaint)

        titlePaint.color = Color.WHITE
        canvas.drawText("RUBBER LEAF DISEASE DIAGNOSIS REPORT", 25f, 38f, titlePaint)

        // 2. Draw Metadata Section
        var yPos = 90f
        canvas.drawText(if (isKannada) "ರೈತರ ಹೆಸರು:" else "Farmer Name:", 30f, yPos, boldPaint)
        canvas.drawText(record.farmerName, 150f, yPos, textPaint)

        canvas.drawText(if (isKannada) "ದಿನಾಂಕ:" else "Date:", 350f, yPos, boldPaint)
        canvas.drawText(record.dateString, 450f, yPos, textPaint)

        yPos += 20f
        canvas.drawText(if (isKannada) "ಸಲಕರಣೆ:" else "App Source:", 30f, yPos, boldPaint)
        canvas.drawText("RubberGuard AI Offline Engine", 150f, yPos, textPaint)

        // Draw horizontal divider line
        yPos += 20f
        canvas.drawLine(25f, yPos, 570f, yPos, borderPaint)

        // 3. Draw Diagnosis Section
        yPos += 25f
        subHeaderPaint.color = 0xFF1B5E20.toInt()
        canvas.drawText(if (isKannada) "ರೋಗ ತಪಾಸಣೆ ವಿವರಗಳು" else "Diagnostic Results", 30f, yPos, subHeaderPaint)

        yPos += 25f
        canvas.drawText(if (isKannada) "ಪತ್ತೆಯಾದ ರೋಗ:" else "Detected Class:", 30f, yPos, boldPaint)
        canvas.drawText(record.diseaseName, 160f, yPos, textPaint)

        canvas.drawText(if (isKannada) "ಖಾತರಿ ಶೇಕಡಾ:" else "Confidence:", 350f, yPos, boldPaint)
        canvas.drawText(String.format("%.1f%%", record.confidence * 100f), 450f, yPos, textPaint)

        yPos += 20f
        canvas.drawText(if (isKannada) "ರೋಗದ ತೀವ್ರತೆ:" else "Severity Level:", 30f, yPos, boldPaint)
        canvas.drawText("${record.severityLabel} (${String.format("%.1f%%", record.severityPercentage)})", 160f, yPos, textPaint)

        // Draw Severity Color Indicator
        rectPaint.color = when (record.severityLabel) {
            "Healthy", "Healthy/Trace" -> 0xFF2E7D32.toInt()
            "Mild" -> 0xFFFBC02D.toInt()
            "Moderate" -> 0xFFF57C00.toInt()
            else -> 0xFFD32F2F.toInt()
        }
        canvas.drawCircle(145f, yPos - 4f, 6f, rectPaint)

        // 4. Draw Images Section (Side-by-side)
        yPos += 25f
        val imageSize = 130
        
        // Load original bitmap
        val originalBitmap = loadScaledBitmap(record.imagePath, imageSize, imageSize)
        if (originalBitmap != null) {
            canvas.drawBitmap(originalBitmap, 30f, yPos, null)
            canvas.drawRect(30f, yPos, 30f + imageSize, yPos + imageSize, borderPaint)
            canvas.drawText(if (isKannada) "ಮೂಲ ಎಲೆ ಚಿತ್ರ" else "Original Image", 30f, yPos + imageSize + 15f, boldPaint)
            originalBitmap.recycle()
        } else {
            canvas.drawRect(30f, yPos, 30f + imageSize, yPos + imageSize, borderPaint)
            canvas.drawText("[Image Missing]", 50f, yPos + 70f, textPaint)
        }

        // Load Grad-CAM Heatmap overlay bitmap
        val heatmapBitmap = loadScaledBitmap(record.heatmapPath, imageSize, imageSize)
        if (heatmapBitmap != null) {
            canvas.drawBitmap(heatmapBitmap, 180f, yPos, null)
            canvas.drawRect(180f, yPos, 180f + imageSize, yPos + imageSize, borderPaint)
            canvas.drawText(if (isKannada) "ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ಹೀಟ್‌ಮ್ಯಾಪ್" else "Grad-CAM Heatmap", 180f, yPos + imageSize + 15f, boldPaint)
            heatmapBitmap.recycle()
        } else {
            canvas.drawRect(180f, yPos, 180f + imageSize, yPos + imageSize, borderPaint)
            canvas.drawText("[Heatmap Missing]", 195f, yPos + 70f, textPaint)
        }

        // Draw diagnosis summary details on the right side of the images
        val rightX = 330f
        var rightY = yPos + 20f
        val langCode = if (isKannada) "kn" else "en"
        val recs = RecommendationSystem.getRecommendation(record.diseaseName, langCode)

        canvas.drawText(if (isKannada) "ಚೇತರಿಕೆ ಸಮಯ:" else "Recovery Est:", rightX, rightY, boldPaint)
        canvas.drawText("${recs.recoveryTime} days", rightX + 110f, rightY, textPaint)

        rightY += 25f
        canvas.drawText(if (isKannada) "ರೋಗದ ಮೂಲ ಕಾರಣ:" else "Primary Cause:", rightX, rightY, boldPaint)
        
        // Wrap cause text to fit in layout
        rightY += 15f
        drawWrappedText(canvas, recs.causes, rightX, rightY, 230f, textPaint, 15f)

        // 5. Draw Recommendations Section
        yPos += imageSize + 40f
        canvas.drawLine(25f, yPos, 570f, yPos, borderPaint)

        yPos += 20f
        canvas.drawText(if (isKannada) "ಶಿಫಾರಸು ಮಾಡಿದ ನಿಯಂತ್ರಣ ಕ್ರಮಗಳು" else "Treatment & Control Measures", 30f, yPos, subHeaderPaint)

        yPos += 20f
        canvas.drawText(if (isKannada) "🍀 ಸಾವಯವ ನಿಯಂತ್ರಣ:" else "🍀 Organic Control:", 30f, yPos, boldPaint)
        yPos += 15f
        yPos = drawWrappedText(canvas, recs.organicTreatment, 40f, yPos, 510f, textPaint, 15f)

        yPos += 15f
        canvas.drawText(if (isKannada) "🧪 ರಾಸಾಯನಿಕ ಚಿಕಿತ್ಸೆ:" else "🧪 Chemical Treatment:", 30f, yPos, boldPaint)
        yPos += 15f
        yPos = drawWrappedText(canvas, recs.chemicalTreatment, 40f, yPos, 510f, textPaint, 15f)

        yPos += 15f
        canvas.drawText(if (isKannada) "🌾 ಶಿಫಾರಸು ಮಾಡಿದ ಗೊಬ್ಬರ:" else "🌾 Recommended Fertilizer:", 30f, yPos, boldPaint)
        yPos += 15f
        yPos = drawWrappedText(canvas, recs.recommendedFertilizer, 40f, yPos, 510f, textPaint, 15f)

        yPos += 15f
        canvas.drawText(if (isKannada) "🛡️ ಮುನ್ನೆಚ್ಚರಿಕೆ ಕ್ರಮಗಳು:" else "🛡️ Preventive Measures:", 30f, yPos, boldPaint)
        yPos += 15f
        drawWrappedText(canvas, recs.preventiveMeasures, 40f, yPos, 510f, textPaint, 15f)

        // 6. Draw Footer Page Boundaries
        rectPaint.color = 0xFFF5F5F5.toInt()
        canvas.drawRect(0f, 810f, 595f, 842f, rectPaint)

        val footerPaint = Paint().apply {
            color = Color.GRAY
            textSize = 9f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.ITALIC)
            isAntiAlias = true
        }
        canvas.drawText("Generated completely offline by MobileNetV2 ML classifier. For educational purposes.", 30f, 828f, footerPaint)

        pdfDocument.finishPage(page)

        // Save PDF to output stream
        val fos = FileOutputStream(outputFile)
        pdfDocument.writeTo(fos)
        fos.flush()
        fos.close()
        pdfDocument.close()
    }

    private fun loadScaledBitmap(filePath: String, reqWidth: Int, reqHeight: Int): Bitmap? {
        try {
            val file = File(filePath)
            if (!file.exists()) return null

            // First decode with inJustDecodeBounds=true to check dimensions
            val options = BitmapFactory.Options().apply {
                inJustDecodeBounds = true
            }
            BitmapFactory.decodeFile(filePath, options)

            // Calculate inSampleSize
            options.inSampleSize = calculateInSampleSize(options, reqWidth, reqHeight)

            // Decode bitmap with inSampleSize set
            options.inJustDecodeBounds = false
            val decoded = BitmapFactory.decodeFile(filePath, options) ?: return null

            // Scale to exact size
            return Bitmap.createScaledBitmap(decoded, reqWidth, reqHeight, true)
        } catch (e: Exception) {
            e.printStackTrace()
            return null
        }
    }

    private fun calculateInSampleSize(options: BitmapFactory.Options, reqWidth: Int, reqHeight: Int): Int {
        val (height: Int, width: Int) = options.outHeight to options.outWidth
        var inSampleSize = 1

        if (height > reqHeight || width > reqWidth) {
            val halfHeight: Int = height / 2
            val halfWidth: Int = width / 2
            while (halfHeight / inSampleSize >= reqHeight && halfWidth / inSampleSize >= reqWidth) {
                inSampleSize *= 2
            }
        }
        return inSampleSize
    }

    private fun drawWrappedText(
        canvas: Canvas,
        text: String,
        x: Float,
        startY: Float,
        maxWidth: Float,
        paint: Paint,
        lineHeight: Float
    ): Float {
        var y = startY
        val words = text.split(" ")
        var line = ""

        for (word in words) {
            val testLine = if (line.isEmpty()) word else "$line $word"
            val width = paint.measureText(testLine)
            if (width > maxWidth) {
                canvas.drawText(line, x, y, paint)
                line = word
                y += lineHeight
            } else {
                line = testLine
            }
        }
        if (line.isNotEmpty()) {
            canvas.drawText(line, x, y, paint)
            y += lineHeight
        }
        return y
    }
}
