package com.rubber.disease.utils

import android.graphics.Bitmap
import org.opencv.android.Utils
import org.opencv.core.*
import org.opencv.imgproc.Imgproc
import kotlin.math.max
import kotlin.math.min

object GradCamUtils {

    /**
     * Converts a 7x7 normalized heatmap float array to a precision, spot-grounded Grad-CAM overlay:
     * - Physical Lesion Saliency: Evaluates luminance contrast, necrotic color bias (R relative to G),
     *   and chlorotic yellow halos to pinpoint real physical disease symptoms.
     * - Macro-Attention Modulation: Fuses the neural CAM attention map with the physical lesion map,
     *   so active lesions in the AI focus zone reach peak fiery crimson (0.8 - 1.0) and other confirmed
     *   spots glow warm orange/yellow (0.4 - 0.7).
     * - Background & Healthy Lamina Protection: Background paper/desk is 100% clean (zero heat bleeding),
     *   and healthy green lamina remains 100% natural, crisp leaf photo.
     *
     * @param originalBitmap The original leaf image bitmap.
     * @param heatmapArray The 7x7 normalized float array from TFLiteClassifier.
     * @return A new Bitmap containing the precision Grad-CAM overlay aligned 1:1 with originalBitmap.
     */
    fun generateOverlay(originalBitmap: Bitmap, heatmapArray: Array<FloatArray>): Bitmap {
        val size = 7
        val heatmapMat = Mat(size, size, CvType.CV_32FC1)
        val floatData = FloatArray(size * size)

        var index = 0
        for (y in 0 until size) {
            for (x in 0 until size) {
                floatData[index++] = heatmapArray[y][x]
            }
        }
        heatmapMat.put(0, 0, floatData)

        val maxDim = max(originalBitmap.width, originalBitmap.height)
        val workingBitmap = if (maxDim > 640) {
            val scale = 640.0f / maxDim.toFloat()
            val w = (originalBitmap.width * scale).toInt()
            val h = (originalBitmap.height * scale).toInt()
            Bitmap.createScaledBitmap(originalBitmap, w, h, true)
        } else {
            originalBitmap
        }

        val targetWidth = workingBitmap.width
        val targetHeight = workingBitmap.height
        val numPixels = targetWidth * targetHeight

        // 1. High-resolution bicubic resizing of 7x7 CAM to working dimensions
        val resizedHeatmapMat = Mat()
        Imgproc.resize(
            heatmapMat,
            resizedHeatmapMat,
            Size(targetWidth.toDouble(), targetHeight.toDouble()),
            0.0,
            0.0,
            Imgproc.INTER_CUBIC
        )

        // 2. Gaussian smoothing to produce organic, continuous activation contours
        val smoothCamMat = Mat()
        Imgproc.GaussianBlur(resizedHeatmapMat, smoothCamMat, Size(21.0, 21.0), 0.0)
        val camFloats = FloatArray(numPixels)
        smoothCamMat.get(0, 0, camFloats)

        // 3. Convert working bitmap to Mat RGB and HSV
        val originalMat = Mat()
        Utils.bitmapToMat(workingBitmap, originalMat)
        val origRgbMat = Mat()
        Imgproc.cvtColor(originalMat, origRgbMat, Imgproc.COLOR_RGBA2RGB)

        val origHsvMat = Mat()
        Imgproc.cvtColor(origRgbMat, origHsvMat, Imgproc.COLOR_RGB2HSV)

        val origBytes = ByteArray(numPixels * 3)
        val hsvBytes = ByteArray(numPixels * 3)
        origRgbMat.get(0, 0, origBytes)
        origHsvMat.get(0, 0, hsvBytes)

        // 4. Segmentation: Leaf vs Background (paper, shadows, hands)
        val leafRawBytes = ByteArray(numPixels)

        for (i in 0 until numPixels) {
            val idx3 = i * 3
            val r = (origBytes[idx3].toInt() and 0xFF).toFloat()
            val g = (origBytes[idx3 + 1].toInt() and 0xFF).toFloat()
            val b = (origBytes[idx3 + 2].toInt() and 0xFF).toFloat()

            val s = (hsvBytes[idx3 + 1].toInt() and 0xFF).toFloat()
            val v = (hsvBytes[idx3 + 2].toInt() and 0xFF).toFloat()

            // Paper (white, gray shadow, warm shadow): Saturation < 38
            val isPaperOrShadow = s < 38.0f
            val isBrightWhite = r > 175.0f && g > 175.0f && b > 175.0f
            val isCoolShadow = b > (g + 3.0f) && b > (r + 8.0f)
            val isDarkVoid = v < 25.0f
            val isHand = r > 115.0f && r > (g + 16.0f) && b < 120.0f

            val isBg = isPaperOrShadow || isBrightWhite || isCoolShadow || isDarkVoid || isHand
            leafRawBytes[i] = if (!isBg) 255.toByte() else 0.toByte()
        }

        val leafRawMat = Mat(targetHeight, targetWidth, CvType.CV_8UC1)
        leafRawMat.put(0, 0, leafRawBytes)

        val kernel = Imgproc.getStructuringElement(Imgproc.MORPH_ELLIPSE, Size(7.0, 7.0))
        val leafClosedMat = Mat()
        Imgproc.morphologyEx(leafRawMat, leafClosedMat, Imgproc.MORPH_CLOSE, kernel)

        // Find largest contour (the leaf) to preserve internal shot-holes while masking background
        val contours = ArrayList<MatOfPoint>()
        val hierarchy = Mat()
        Imgproc.findContours(leafClosedMat, contours, hierarchy, Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_SIMPLE)
        val leafMaskMat = Mat.zeros(Size(targetWidth.toDouble(), targetHeight.toDouble()), CvType.CV_8UC1)

        if (contours.isNotEmpty()) {
            var maxArea = -1.0
            var maxContour: MatOfPoint? = null
            for (c in contours) {
                val area = Imgproc.contourArea(c)
                if (area > maxArea) {
                    maxArea = area
                    maxContour = c
                }
            }
            if (maxContour != null && maxArea > 200.0) {
                Imgproc.drawContours(leafMaskMat, listOf(maxContour), -1, Scalar(255.0), -1)
            } else {
                leafClosedMat.copyTo(leafMaskMat)
            }
        } else {
            leafClosedMat.copyTo(leafMaskMat)
        }

        val leafMaskFloatMat = Mat()
        leafMaskMat.convertTo(leafMaskFloatMat, CvType.CV_32FC1, 1.0 / 255.0)
        val smoothLeafMaskMat = Mat()
        Imgproc.GaussianBlur(leafMaskFloatMat, smoothLeafMaskMat, Size(7.0, 7.0), 0.0)
        val leafMaskFloats = FloatArray(numPixels)
        smoothLeafMaskMat.get(0, 0, leafMaskFloats)

        // 5. Determine existing dominant leaf color: Is leaf predominantly GREEN or BROWN?
        val maskBytes = ByteArray(numPixels)
        leafMaskMat.get(0, 0, maskBytes)

        var leafPixelCount = 0
        var greenPixelCount = 0
        val histV = IntArray(256)

        for (i in 0 until numPixels) {
            if (maskBytes[i].toInt() != 0) {
                leafPixelCount++
                val idx3 = i * 3
                val h = hsvBytes[idx3].toInt() and 0xFF
                val s = hsvBytes[idx3 + 1].toInt() and 0xFF
                val v = hsvBytes[idx3 + 2].toInt() and 0xFF

                if (h in 35..95 && s > 30) {
                    greenPixelCount++
                }
                histV[v.coerceIn(0, 255)]++
            }
        }

        val isGreenLeaf = if (leafPixelCount > 0) (greenPixelCount.toFloat() / leafPixelCount.toFloat()) > 0.40f else true

        var medV = 80.0f
        if (leafPixelCount > 0) {
            val target = leafPixelCount / 2
            var cumsum = 0
            for (bin in 0 until 256) {
                cumsum += histV[bin]
                if (cumsum >= target) {
                    medV = bin.toFloat()
                    break
                }
            }
        }

        // 6. Damage Detection: Where color is DIFFERENT from the existing leaf tissue
        val rawDamageFloats = FloatArray(numPixels)

        for (i in 0 until numPixels) {
            if (maskBytes[i].toInt() == 0) {
                rawDamageFloats[i] = 0.0f
                continue
            }
            val idx3 = i * 3
            val r = (origBytes[idx3].toInt() and 0xFF).toFloat()
            val g = (origBytes[idx3 + 1].toInt() and 0xFF).toFloat()
            val b = (origBytes[idx3 + 2].toInt() and 0xFF).toFloat()

            val h = (hsvBytes[idx3].toInt() and 0xFF).toFloat()
            val s = (hsvBytes[idx3 + 1].toInt() and 0xFF).toFloat()
            val v = (hsvBytes[idx3 + 2].toInt() and 0xFF).toFloat()

            if (isGreenLeaf) {
                // EXISTING LEAF IS GREEN. Damage is where color differs from green:
                val hasChroma = if (s > 35.0f) 1.0f else 0.0f

                // A. Brown / bronze / necrotic lesions:
                val brownChroma = max(0.0f, min(1.0f, (r - b - 20.0f) / 25.0f))
                val redVsGreen = max(0.0f, min(1.0f, (r - (g - 5.0f)) / 20.0f))
                val brownLesion = brownChroma * redVsGreen * hasChroma

                // B. Yellow chlorotic halos:
                val minRg = min(r, g)
                val yellowDiff = max(0.0f, min(1.0f, ((minRg - b) - 20.0f) / 25.0f))
                val isYellowHue = if (h in 12.0f..38.0f) 1.0f else 0.0f
                val yellowHalo = yellowDiff * isYellowHue * hasChroma

                // C. Pale / dry / powdery spots / translucent shot-holes:
                val paleVal = max(0.0f, min(1.0f, (v - 130.0f) / 35.0f))
                val paleRedBias = max(0.0f, min(1.0f, (r - b - 15.0f) / 15.0f))
                val paleSpot = paleVal * paleRedBias

                // D. Dark necrotic centers:
                val darkDiff = max(0.0f, min(1.0f, ((medV - 18.0f) - v) / 20.0f))
                val notGreen = if (g - r < 8.0f) 1.0f else 0.0f
                val darkSpot = darkDiff * notGreen * hasChroma

                var d = max(brownLesion, yellowHalo)
                d = max(d, paleSpot)
                d = max(d, darkSpot)
                rawDamageFloats[i] = d
            } else {
                // EXISTING LEAF IS BROWN / DRY / TRANSITIONING. Damage differs from brown:
                val hasChroma = if (s > 35.0f) 1.0f else 0.0f
                val darkNecrosis = max(0.0f, min(1.0f, ((medV - 15.0f) - v) / 22.0f)) * hasChroma
                val paleBlight = max(0.0f, min(1.0f, (v - (medV + 20.0f)) / 22.0f)) * hasChroma
                rawDamageFloats[i] = max(darkNecrosis, paleBlight)
            }
        }

        val rawDamageMat = Mat(targetHeight, targetWidth, CvType.CV_32FC1)
        rawDamageMat.put(0, 0, rawDamageFloats)
        val smoothDamageMat = Mat()
        Imgproc.GaussianBlur(rawDamageMat, smoothDamageMat, Size(7.0, 7.0), 0.0)
        val damageGlowFloats = FloatArray(numPixels)
        smoothDamageMat.get(0, 0, damageGlowFloats)

        // 7. Spot-Grounded Heatmap Fusion
        val finalHeatFloats = FloatArray(numPixels)
        var maxFinalHeat = 0.0f
        for (i in 0 until numPixels) {
            val glow = min(1.0f, damageGlowFloats[i] * 1.8f)
            val cam = camFloats[i].coerceIn(0.0f, 1.0f)
            val mask = leafMaskFloats[i].coerceIn(0.0f, 1.0f)

            // Neural CAM modulates physical spots: primary AI focus zone reaches peak fiery crimson (0.8 - 1.0)
            // Healthy green lamina has glow = 0.0 -> stays 0.0 (100% natural leaf photo!)
            val fused = glow * (0.45f + 0.55f * cam) * mask
            finalHeatFloats[i] = fused
            if (fused > maxFinalHeat) maxFinalHeat = fused
        }

        // Normalize
        if (maxFinalHeat > 1e-6f) {
            for (i in 0 until numPixels) {
                finalHeatFloats[i] = (finalHeatFloats[i] / maxFinalHeat).coerceIn(0.0f, 1.0f)
            }
        }

        // 8. Colormap: Standard COLORMAP_JET
        val u8HeatmapMat = Mat(targetHeight, targetWidth, CvType.CV_8UC1)
        val u8Bytes = ByteArray(numPixels)
        for (i in 0 until numPixels) {
            u8Bytes[i] = (finalHeatFloats[i] * 255.0f).toInt().coerceIn(0, 255).toByte()
        }
        u8HeatmapMat.put(0, 0, u8Bytes)

        val jetColorMat = Mat()
        Imgproc.applyColorMap(u8HeatmapMat, jetColorMat, Imgproc.COLORMAP_JET)
        val jetRgbMat = Mat()
        Imgproc.cvtColor(jetColorMat, jetRgbMat, Imgproc.COLOR_BGR2RGB)
        val jetBytes = ByteArray(numPixels * 3)
        jetRgbMat.get(0, 0, jetBytes)

        // 9. Smooth Alpha Blending
        // Below 0.12: 100% natural photo (alpha = 0)
        // Above 0.12: smooth ramp up to vibrant 85% opacity over spot centers
        val threshold = 0.12f
        val outBytes = ByteArray(numPixels * 3)

        for (i in 0 until numPixels) {
            val act = finalHeatFloats[i]
            val alpha = if (act <= threshold) {
                0.0f
            } else {
                val normAct = (act - threshold) / (1.0f - threshold)
                Math.pow(normAct.toDouble(), 1.3).toFloat() * 0.85f
            }
            val invAlpha = 1.0f - alpha

            val idx3 = i * 3
            val rOrig = origBytes[idx3].toInt() and 0xFF
            val gOrig = origBytes[idx3 + 1].toInt() and 0xFF
            val bOrig = origBytes[idx3 + 2].toInt() and 0xFF

            val rJet = jetBytes[idx3].toInt() and 0xFF
            val gJet = jetBytes[idx3 + 1].toInt() and 0xFF
            val bJet = jetBytes[idx3 + 2].toInt() and 0xFF

            outBytes[idx3] = (rOrig * invAlpha + rJet * alpha).toInt().coerceIn(0, 255).toByte()
            outBytes[idx3 + 1] = (gOrig * invAlpha + gJet * alpha).toInt().coerceIn(0, 255).toByte()
            outBytes[idx3 + 2] = (bOrig * invAlpha + bJet * alpha).toInt().coerceIn(0, 255).toByte()
        }

        val blendedRgbMat = Mat(targetHeight, targetWidth, CvType.CV_8UC3)
        blendedRgbMat.put(0, 0, outBytes)

        val blendedRgbaMat = Mat()
        Imgproc.cvtColor(blendedRgbMat, blendedRgbaMat, Imgproc.COLOR_RGB2RGBA)

        val resultBitmap = Bitmap.createBitmap(targetWidth, targetHeight, Bitmap.Config.ARGB_8888)
        Utils.matToBitmap(blendedRgbaMat, resultBitmap)

        // Cleanup
        heatmapMat.release()
        resizedHeatmapMat.release()
        smoothCamMat.release()
        originalMat.release()
        origRgbMat.release()
        origHsvMat.release()
        leafRawMat.release()
        kernel.release()
        leafClosedMat.release()
        hierarchy.release()
        leafMaskMat.release()
        leafMaskFloatMat.release()
        smoothLeafMaskMat.release()
        rawDamageMat.release()
        smoothDamageMat.release()
        u8HeatmapMat.release()
        jetColorMat.release()
        jetRgbMat.release()
        blendedRgbMat.release()
        blendedRgbaMat.release()

        if (workingBitmap != originalBitmap) {
            workingBitmap.recycle()
        }

        return resultBitmap
    }
}
