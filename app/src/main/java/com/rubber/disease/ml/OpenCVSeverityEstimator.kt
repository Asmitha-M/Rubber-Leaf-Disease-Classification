package com.rubber.disease.ml

import android.graphics.Bitmap
import org.opencv.android.Utils
import org.opencv.core.Core
import org.opencv.core.Mat
import org.opencv.core.Scalar
import org.opencv.core.MatOfPoint
import org.opencv.core.MatOfInt
import org.opencv.core.Point
import org.opencv.imgproc.Imgproc

data class SeverityResult(
    val severityPercentage: Float,
    val severityLabel: String,
    val colorCode: Int, // Hex color representing severity
    val leafRatio: Float, // Ratio of leaf pixels to total image pixels
    val organicRatio: Float, // Ratio of green/yellow-brown pixels to total image pixels
    val solidity: Float, // Solidity of the main leaf contour (area / convex hull area)
    val mainContourRatio: Float // Ratio of the largest contour area to total image area
)

class OpenCVSeverityEstimator {

    companion object {
        init {
            try {
                if (!org.opencv.android.OpenCVLoader.initDebug()) {
                    System.loadLibrary("opencv_java4")
                }
            } catch (e: UnsatisfiedLinkError) {
                try {
                    System.loadLibrary("opencv_java4")
                } catch (ex: Exception) {
                    ex.printStackTrace()
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun estimateSeverity(bitmap: Bitmap, isHealthyClass: Boolean): SeverityResult {
        val originalMat = Mat()
        Utils.bitmapToMat(bitmap, originalMat)

        // Convert RGB to HSV
        val hsvMat = Mat()
        Imgproc.cvtColor(originalMat, hsvMat, Imgproc.COLOR_RGB2HSV)

        // Masks for segmentation
        val greenMask = Mat()
        val yellowBrownMask = Mat()
        val darkMask = Mat()
        val whiteMask = Mat()

        // 1. Healthy Green Region
        Core.inRange(hsvMat, Scalar(35.0, 30.0, 30.0), Scalar(85.0, 255.0, 255.0), greenMask)

        // 2. Yellow / Brown Spots (Anthracnose, Leaf Blight, Leaf Spot, Corynespora)
        Core.inRange(hsvMat, Scalar(10.0, 30.0, 30.0), Scalar(35.0, 255.0, 255.0), yellowBrownMask)

        // 3. Dark/Black Spots (Black Spot, Necrotic spots, Bird's eye spot centers)
        Core.inRange(hsvMat, Scalar(0.0, 0.0, 0.0), Scalar(180.0, 255.0, 60.0), darkMask)

        // 4. White/Grey Spots (Powdery Mildew)
        Core.inRange(hsvMat, Scalar(0.0, 0.0, 150.0), Scalar(180.0, 50.0, 255.0), whiteMask)

        // Combine diseased regions
        val diseasedMask1 = Mat()
        val diseasedMask = Mat()
        Core.bitwise_or(yellowBrownMask, darkMask, diseasedMask1)
        Core.bitwise_or(diseasedMask1, whiteMask, diseasedMask)

        // Combine to get overall leaf mask
        val leafMask = Mat()
        Core.bitwise_or(greenMask, diseasedMask, leafMask)

        // Count pixels
        val totalLeafPixels = Core.countNonZero(leafMask)
        val totalDiseasedPixels = Core.countNonZero(diseasedMask)
        val totalPixels = bitmap.width * bitmap.height
        val leafRatio = totalLeafPixels.toFloat() / totalPixels.toFloat()

        val greenCount = Core.countNonZero(greenMask)
        val yellowBrownCount = Core.countNonZero(yellowBrownMask)
        val organicRatio = (greenCount + yellowBrownCount).toFloat() / totalPixels.toFloat()

        // Run leaf contour/shape validation
        val contours = ArrayList<MatOfPoint>()
        val hierarchy = Mat()
        Imgproc.findContours(leafMask, contours, hierarchy, Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_SIMPLE)

        var maxArea = 0.0
        var largestContour: MatOfPoint? = null
        for (contour in contours) {
            val area = Imgproc.contourArea(contour)
            if (area > maxArea) {
                maxArea = area
                largestContour = contour
            }
        }

        var solidityValue = 0.0f
        var mainContourRatioValue = 0.0f

        if (largestContour != null) {
            mainContourRatioValue = (maxArea / totalPixels.toDouble()).toFloat()
            try {
                val hull = MatOfInt()
                Imgproc.convexHull(largestContour, hull)
                
                val hullPoints = ArrayList<Point>()
                val contourPoints = largestContour.toList()
                val hullIndices = hull.toList()
                for (index in hullIndices) {
                    hullPoints.add(contourPoints[index])
                }
                
                val hullMat = MatOfPoint().apply {
                    fromList(hullPoints)
                }
                val hullArea = Imgproc.contourArea(hullMat)
                solidityValue = if (hullArea > 0.0) (maxArea / hullArea).toFloat() else 0.0f
                
                hullMat.release()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        hierarchy.release()
        for (contour in contours) {
            contour.release()
        }

        // Cleanup mats
        originalMat.release()
        hsvMat.release()
        greenMask.release()
        yellowBrownMask.release()
        darkMask.release()
        whiteMask.release()
        diseasedMask1.release()
        diseasedMask.release()
        leafMask.release()

        if (isHealthyClass) {
            return SeverityResult(0.0f, "Healthy", 0xFF2E7D32.toInt(), leafRatio, organicRatio, solidityValue, mainContourRatioValue)
        }

        if (totalLeafPixels == 0) {
            // Fallback if no leaf pixels detected (e.g. invalid background)
            return SeverityResult(15.0f, "Mild", 0xFFFBC02D.toInt(), 0.0f, 0.0f, 0.0f, 0.0f)
        }

        val percentage = (totalDiseasedPixels.toFloat() / totalLeafPixels.toFloat()) * 100f

        // Classify severity based on percentage thresholds
        val (label, color) = when {
            percentage < 5.0f -> Pair("Healthy/Trace", 0xFF2E7D32.toInt()) // Green
            percentage < 20.0f -> Pair("Mild", 0xFFFBC02D.toInt())         // Yellow/Gold
            percentage < 50.0f -> Pair("Moderate", 0xFFF57C00.toInt())     // Orange
            else -> Pair("Severe", 0xFFD32F2F.toInt())                     // Red
        }

        return SeverityResult(percentage, label, color, leafRatio, organicRatio, solidityValue, mainContourRatioValue)
    }
}
