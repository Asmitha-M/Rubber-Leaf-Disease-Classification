package com.rubber.disease.ml

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.os.SystemClock
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel

data class PredictionResult(
    val diseaseName: String,
    val confidence: Float,
    val inferenceTimeMs: Long,
    val classProbabilities: List<Pair<String, Float>>,
    val heatmap: Array<FloatArray> // 7x7 normalized heatmap
)

class TFLiteClassifier(private val context: Context) {

    private var interpreter: Interpreter? = null
    private var denseWeights: FloatArray? = null

    companion object {
        private const val MODEL_PATH = "model.tflite"
        private const val WEIGHTS_PATH = "dense_weights.bin"
        private const val IMAGE_SIZE = 224
        private const val NUM_CLASSES = 9
        private const val FEATURE_CHANNELS = 1280
        private const val FEATURE_SIZE = 7

        val CLASSES = arrayOf(
            "Abnormal Leaf Fall",            // 0: Abnormal
            "Anthracnose",                   // 1: Anthracnose
            "Background / Non-Rubber Leaf",  // 2: Background
            "Black Spot / Bird's Eye",       // 3: Black_Spot
            "Dry Leaf",                      // 4: Dry_Leaf
            "Healthy",                       // 5: Healthy
            "Leaf Blight",                   // 6: Leaf_Blight
            "Leaf Spot",                     // 7: Leaf_Spot
            "Powdery Mildew"                 // 8: Powdery_Mildew
        )
    }

    init {
        loadModel()
        loadDenseWeights()
    }

    private fun loadModel() {
        try {
            val assetFileDescriptor = context.assets.openFd(MODEL_PATH)
            val fileInputStream = FileInputStream(assetFileDescriptor.fileDescriptor)
            val fileChannel = fileInputStream.channel
            val startOffset = assetFileDescriptor.startOffset
            val declaredLength = assetFileDescriptor.declaredLength
            val modelBuffer = fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
            
            val options = Interpreter.Options()
            options.setNumThreads(4)
            interpreter = Interpreter(modelBuffer, options)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun loadDenseWeights() {
        try {
            val inputStream = context.assets.open(WEIGHTS_PATH)
            val bytes = inputStream.readBytes()
            inputStream.close()
            
            val buffer = ByteBuffer.wrap(bytes)
            buffer.order(ByteOrder.nativeOrder())
            
            val count = bytes.size / 4 // float32 is 4 bytes
            denseWeights = FloatArray(count)
            for (i in 0 until count) {
                if (buffer.remaining() >= 4) {
                    denseWeights!![i] = buffer.float
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun classify(bitmap: Bitmap): PredictionResult? {
        val interp = interpreter ?: return null
        val weights = denseWeights ?: return null

        val startTime = SystemClock.uptimeMillis()

        // 1. Preprocess bitmap to ByteBuffer (1 * 224 * 224 * 3 * 4 bytes)
        val inputBuffer = convertBitmapToByteBuffer(bitmap)

        // 2. Prepare outputs (Direct ByteBuffers for crash-free JNI transfer)
        val featBufferSize = 1 * FEATURE_SIZE * FEATURE_SIZE * FEATURE_CHANNELS * 4
        val featureMapBuffer = ByteBuffer.allocateDirect(featBufferSize).apply {
            order(ByteOrder.nativeOrder())
        }

        val probBufferSize = 1 * NUM_CLASSES * 4
        val probBuffer = ByteBuffer.allocateDirect(probBufferSize).apply {
            order(ByteOrder.nativeOrder())
        }

        val outputs = HashMap<Int, Any>()
        outputs[0] = featureMapBuffer
        outputs[1] = probBuffer

        // 3. Run Inference
        interp.runForMultipleInputsOutputs(arrayOf(inputBuffer), outputs)

        val inferenceTime = SystemClock.uptimeMillis() - startTime

        // 4. Parse outputs from ByteBuffers into flat float arrays
        probBuffer.rewind()
        val probs = FloatArray(NUM_CLASSES)
        probBuffer.asFloatBuffer().get(probs)

        featureMapBuffer.rewind()
        val features = FloatArray(FEATURE_SIZE * FEATURE_SIZE * FEATURE_CHANNELS)
        featureMapBuffer.asFloatBuffer().get(features)

        // 5. Find predicted class
        var maxIdx = 0
        var maxVal = -1f
        for (i in probs.indices) {
            if (probs[i] > maxVal) {
                maxVal = probs[i]
                maxIdx = i
            }
        }

        // Apply OOD (Out-of-Distribution) confidence thresholding to flag invalid/unseen items
        val confidence = maxVal
        var predictedDisease = CLASSES[maxIdx]
        
        // If the model is extremely uncertain (e.g. < 35% confidence), it's likely a random object/unseen non-leaf!
        if (confidence < 0.35f) {
            predictedDisease = "Invalid / Non-Rubber Leaf"
        }

        // 6. Generate Grad-CAM 7x7 Heatmap Offline using flat features
        val heatmap = generateGradCamHeatmap(features, weights, maxIdx)

        // 7. Map probabilities
        val probList = CLASSES.mapIndexed { idx, className ->
            Pair(className, probs[idx])
        }.sortedByDescending { it.second }

        return PredictionResult(
            diseaseName = predictedDisease,
            confidence = confidence,
            inferenceTimeMs = inferenceTime,
            classProbabilities = probList,
            heatmap = heatmap
        )
    }

    private fun convertBitmapToByteBuffer(bitmap: Bitmap): ByteBuffer {
        val byteBuffer = ByteBuffer.allocateDirect(1 * IMAGE_SIZE * IMAGE_SIZE * 3 * 4)
        byteBuffer.order(ByteOrder.nativeOrder())
        
        val scaledBitmap = Bitmap.createScaledBitmap(bitmap, IMAGE_SIZE, IMAGE_SIZE, true)
        val intValues = IntArray(IMAGE_SIZE * IMAGE_SIZE)
        scaledBitmap.getPixels(intValues, 0, scaledBitmap.width, 0, 0, scaledBitmap.width, scaledBitmap.height)
        
        var pixel = 0
        for (i in 0 until IMAGE_SIZE) {
            for (j in 0 until IMAGE_SIZE) {
                val value = intValues[pixel++]
                // Pass raw float values in [0.0f, 255.0f] directly to the compiled graph
                val r = ((value shr 16) and 0xFF).toFloat()
                val g = ((value shr 8) and 0xFF).toFloat()
                val b = (value and 0xFF).toFloat()
                
                byteBuffer.putFloat(r)
                byteBuffer.putFloat(g)
                byteBuffer.putFloat(b)
            }
        }
        return byteBuffer
    }

    private fun generateGradCamHeatmap(
        features: FloatArray, // Flat array of shape [7 * 7 * 1280]
        weights: FloatArray,  // Flat array of shape [1280 * 8]
        classIndex: Int
    ): Array<FloatArray> {
        val heatmap = Array(FEATURE_SIZE) { FloatArray(FEATURE_SIZE) }

        // Compute linear combination of feature maps and dense weights for classIndex
        var maxVal = 0.0f
        for (y in 0 until FEATURE_SIZE) {
            for (x in 0 until FEATURE_SIZE) {
                var sum = 0.0f
                for (k in 0 until FEATURE_CHANNELS) {
                    val weightIndex = k * NUM_CLASSES + classIndex
                    val w = if (weightIndex < weights.size) weights[weightIndex] else 0.0f
                    val featIdx = (y * FEATURE_SIZE + x) * FEATURE_CHANNELS + k
                    sum += features[featIdx] * w
                }
                // ReLU: clip negative values
                val valReLu = if (sum > 0f) sum else 0f
                heatmap[y][x] = valReLu
                if (valReLu > maxVal) {
                    maxVal = valReLu
                }
            }
        }

        // Normalize to [0.0, 1.0]
        if (maxVal > 0.0f) {
            for (y in 0 until FEATURE_SIZE) {
                for (x in 0 until FEATURE_SIZE) {
                    heatmap[y][x] /= maxVal
                }
            }
        }

        return heatmap
    }

    fun close() {
        interpreter?.close()
    }
}
