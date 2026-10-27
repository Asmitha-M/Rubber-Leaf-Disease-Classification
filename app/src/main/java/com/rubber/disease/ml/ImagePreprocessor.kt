package com.rubber.disease.ml

import android.graphics.Bitmap
import org.opencv.android.Utils
import org.opencv.core.*
import org.opencv.imgproc.Imgproc
import java.util.ArrayList
import kotlin.math.max
import kotlin.math.min

object ImagePreprocessor {

    sealed class PreprocessResult {
        data class Success(
            val bitmap: Bitmap,
            val boundingBox: Rect? = null,
            val laplacianVariance: Double = 50.0
        ) : PreprocessResult()
        data class Failure(val message: String) : PreprocessResult()
    }

    fun preprocessAndValidate(inputBitmap: Bitmap): PreprocessResult {
        val originalMat = Mat()
        Utils.bitmapToMat(inputBitmap, originalMat)

        val targetWidth = originalMat.cols()
        val targetHeight = originalMat.rows()
        val numPixels = targetWidth * targetHeight

        if (numPixels <= 0) {
            originalMat.release()
            return PreprocessResult.Failure("Invalid image dimensions.")
        }

        // Convert to RGB
        val rgbMat = Mat()
        Imgproc.cvtColor(originalMat, rgbMat, Imgproc.COLOR_RGBA2RGB)

        // Convert to HSV for robust background/paper/shadow separation
        val hsvMat = Mat()
        Imgproc.cvtColor(rgbMat, hsvMat, Imgproc.COLOR_RGB2HSV)

        val rgbBytes = ByteArray(numPixels * 3)
        rgbMat.get(0, 0, rgbBytes)

        val hsvBytes = ByteArray(numPixels * 3)
        hsvMat.get(0, 0, hsvBytes)

        val leafRawBytes = ByteArray(numPixels)

        // Robust leaf pixel segmentation (rejection of white paper, shadows, void, hand)
        for (i in 0 until numPixels) {
            val idx3 = i * 3
            val r = (rgbBytes[idx3].toInt() and 0xFF).toFloat()
            val g = (rgbBytes[idx3 + 1].toInt() and 0xFF).toFloat()
            val b = (rgbBytes[idx3 + 2].toInt() and 0xFF).toFloat()

            val s = (hsvBytes[idx3 + 1].toInt() and 0xFF).toFloat()
            val v = (hsvBytes[idx3 + 2].toInt() and 0xFF).toFloat()

            // Paper (white, gray shadow, warm shadow): Saturation < 38
            val isPaperOrShadow = s < 38.0f
            val isBrightWhite = r > 175.0f && g > 175.0f && b > 175.0f
            val isCoolShadow = b > (g + 3.0f) && b > (r + 8.0f)
            val isDarkVoid = v < 22.0f
            val isHand = r > 115.0f && r > (g + 16.0f) && b < 120.0f

            val isBg = isPaperOrShadow || isBrightWhite || isCoolShadow || isDarkVoid || isHand
            leafRawBytes[i] = if (!isBg) 255.toByte() else 0.toByte()
        }

        val leafRawMat = Mat(targetHeight, targetWidth, CvType.CV_8UC1)
        leafRawMat.put(0, 0, leafRawBytes)

        val kernel = Imgproc.getStructuringElement(Imgproc.MORPH_ELLIPSE, Size(7.0, 7.0))
        val leafClosedMat = Mat()
        Imgproc.morphologyEx(leafRawMat, leafClosedMat, Imgproc.MORPH_CLOSE, kernel)

        // Find contours
        val contours = ArrayList<MatOfPoint>()
        val hierarchy = Mat()
        Imgproc.findContours(leafClosedMat, contours, hierarchy, Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_SIMPLE)

        var maxArea = 0.0
        var largestContour: MatOfPoint? = null
        for (contour in contours) {
            val area = Imgproc.contourArea(contour)
            if (area > maxArea) {
                maxArea = area
                largestContour = contour
            }
        }

        // Bounding box determination:
        // If clear leaf contour exists and is >= 5% of image, crop to contour.
        // Otherwise, if leaf fills full frame (macro shot), use full frame.
        val boundingBox: Rect = if (largestContour != null && maxArea > (numPixels * 0.05)) {
            Imgproc.boundingRect(largestContour)
        } else {
            Rect(0, 0, targetWidth, targetHeight)
        }

        // Cleanup intermediate mats
        leafRawMat.release()
        kernel.release()
        leafClosedMat.release()
        hierarchy.release()
        contours.forEach { it.release() }
        hsvMat.release()

        // Crop leaf region
        val croppedRgbMat = Mat(rgbMat, boundingBox)

        // Measure focus blur via Laplacian variance on cropped leaf
        val grayMat = Mat()
        Imgproc.cvtColor(croppedRgbMat, grayMat, Imgproc.COLOR_RGB2GRAY)
        val laplacianMat = Mat()
        Imgproc.Laplacian(grayMat, laplacianMat, CvType.CV_64F)
        val lapMean = MatOfDouble()
        val lapStddev = MatOfDouble()
        Core.meanStdDev(laplacianMat, lapMean, lapStddev)
        val std = lapStddev.toArray()[0]
        val variance = std * std

        grayMat.release()
        laplacianMat.release()

        // Only reject catastrophic pitch-black or unrecognizable blur (variance < 6.0)
        if (variance < 6.0) {
            originalMat.release()
            rgbMat.release()
            croppedRgbMat.release()
            return PreprocessResult.Failure("Image is severely blurred or dark. Please hold camera steady and scan again.")
        }

        // 3. Adaptive Sharpness Restoration for Blurry / Soft Images:
        // If image is soft or slightly blurred (variance < 75.0), apply Unsharp Masking
        // to restore fine lesion boundaries, fungal mycelium, and concentric spot edges!
        val enhancedMat = Mat()
        if (variance < 75.0) {
            val blurMat = Mat()
            Imgproc.GaussianBlur(croppedRgbMat, blurMat, Size(0.0, 0.0), 2.5)
            // Adaptive boost: softer images receive higher edge amplification
            val boost = min(1.7, max(0.7, (75.0 - variance) / 35.0))
            Core.addWeighted(croppedRgbMat, 1.0 + boost, blurMat, -boost, 0.0, enhancedMat)
            blurMat.release()
        } else {
            // Already sharp: mild bilateral filter to eliminate digital noise
            Imgproc.bilateralFilter(croppedRgbMat, enhancedMat, 5, 30.0, 30.0)
        }

        croppedRgbMat.release()
        rgbMat.release()

        // 4. Resize to standard 224x224 model input
        val finalResizedMat = Mat()
        Imgproc.resize(enhancedMat, finalResizedMat, Size(224.0, 224.0))
        enhancedMat.release()

        val finalRgbaMat = Mat()
        Imgproc.cvtColor(finalResizedMat, finalRgbaMat, Imgproc.COLOR_RGB2RGBA)
        finalResizedMat.release()

        // Convert back to Bitmap
        val outputBitmap = Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888)
        Utils.matToBitmap(finalRgbaMat, outputBitmap)
        finalRgbaMat.release()
        originalMat.release()

        return PreprocessResult.Success(outputBitmap, boundingBox, variance)
    }
}
