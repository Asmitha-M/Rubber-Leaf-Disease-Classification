package com.rubber.disease.ui.fragments

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Environment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.rubber.disease.R
import com.rubber.disease.data.AppDatabase
import com.rubber.disease.data.ScanRecordEntity
import com.rubber.disease.databinding.FragmentPredictionBinding
import com.rubber.disease.databinding.ItemProbabilityRowBinding
import com.rubber.disease.ml.OpenCVSeverityEstimator
import com.rubber.disease.ml.PredictionResult
import com.rubber.disease.ml.SeverityResult
import com.rubber.disease.ml.TFLiteClassifier
import com.rubber.disease.ml.ImagePreprocessor
import com.rubber.disease.utils.*
import com.rubber.disease.viewmodels.MainViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.*

class PredictionFragment : Fragment() {

    private var _binding: FragmentPredictionBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: MainViewModel

    private var imagePath: String? = null
    private var croppedBitmap: Bitmap? = null

    private var classifier: TFLiteClassifier? = null
    private val severityEstimator = OpenCVSeverityEstimator()
    
    private var prediction: PredictionResult? = null
    private var severity: SeverityResult? = null
    private var heatmapOverlayPath: String? = null
    private var cleanLeafPath: String? = null
    
    private var ttsHelper: TextToSpeechHelper? = null
    private var isSaved = false
    private var savedRecordId: Long = -1

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentPredictionBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel = ViewModelProvider(requireActivity())[MainViewModel::class.java]
        imagePath = arguments?.getString("imagePath")
        val passedRecordId = arguments?.getLong("recordId", -1L) ?: -1L
        if (passedRecordId != -1L) {
            savedRecordId = passedRecordId
            isSaved = true
            binding.btnSaveRecord.isEnabled = false
            binding.btnSaveRecord.text = "Saved"
        }

        binding.toolbarPrediction.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        // Initialize TTS
        val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
        val isTtsEnabled = prefs.getBoolean("tts_enabled", true)
        val lang = LanguageHelper.getLanguage(requireContext())
        
        if (isTtsEnabled) {
            ttsHelper = TextToSpeechHelper(requireContext()) {
                ttsHelper?.setLanguage(lang)
            }
        }

        // Process image
        if (imagePath != null) {
            val file = File(imagePath!!)
            if (file.exists()) {
                croppedBitmap = BitmapFactory.decodeFile(file.absolutePath)
                binding.ivPredictionImage.setImageBitmap(croppedBitmap)
                
                // Run inference and calculations in coroutine
                runOfflineAnalysis(lang)
            } else {
                Toast.makeText(context, "Image file not found.", Toast.LENGTH_LONG).show()
                findNavController().navigateUp()
            }
        } else {
            findNavController().navigateUp()
        }

        // Action click bindings
        binding.btnFlowSeverity.setOnClickListener {
            val bundle = Bundle().apply {
                putString("imagePath", imagePath)
                putBoolean("isHealthy", prediction?.diseaseName.equals("Healthy", ignoreCase = true))
            }
            findNavController().navigate(R.id.action_predictionFragment_to_severityFragment, bundle)
        }

        binding.btnFlowGradcam.setOnClickListener {
            val bundle = Bundle().apply {
                putString("imagePath", imagePath)
                putString("heatmapPath", heatmapOverlayPath)
            }
            findNavController().navigate(R.id.action_predictionFragment_to_gradCamFragment, bundle)
        }

        binding.btnFlowRecs.setOnClickListener {
            val bundle = Bundle().apply {
                putString("diseaseName", prediction?.diseaseName)
            }
            findNavController().navigate(R.id.action_predictionFragment_to_recommendationFragment, bundle)
        }

        binding.btnSaveRecord.setOnClickListener {
            saveRecordToDatabase()
        }

        binding.btnExportPdfPrediction.setOnClickListener {
            exportPdfReport()
        }
    }

    private fun runOfflineAnalysis(lang: String) {
        val bitmap = croppedBitmap ?: return
        
        lifecycleScope.launch(Dispatchers.Default) {
            // Run preprocessing and validation checks first
            val preprocessResult = ImagePreprocessor.preprocessAndValidate(bitmap)
            
            if (preprocessResult is ImagePreprocessor.PreprocessResult.Failure) {
                // If validation checks fail, create a PredictionResult with the failure message
                val finalResult = PredictionResult(
                    diseaseName = preprocessResult.message,
                    confidence = 0.0f,
                    inferenceTimeMs = 0L,
                    classProbabilities = emptyList(),
                    heatmap = Array(7) { FloatArray(7) }
                )
                prediction = finalResult
                
                withContext(Dispatchers.Main) {
                    displayResults(finalResult, SeverityResult(0f, "Healthy/Trace", 0, 0f, 0f, 0f, 0f), lang)
                }
                return@launch
            }
            
            val cleanBitmap = (preprocessResult as ImagePreprocessor.PreprocessResult.Success).bitmap
            
            // Initialize classifier if null
            if (classifier == null) {
                classifier = TFLiteClassifier(requireContext())
            }

            // Run TFLite inference on the cleaned leaf image
            val result = classifier?.classify(cleanBitmap)
            
            if (result != null) {
                val isHealthy = result.diseaseName.equals("Healthy", ignoreCase = true)
                
                // Run OpenCV Severity Analysis on original image
                val sevResult = severityEstimator.estimateSeverity(bitmap, isHealthy)
                severity = sevResult

                // Only flag out-of-distribution clutter if confidence is below 35% or identified as Background
                val isClutter = result.diseaseName.equals("Background / Non-Rubber Leaf", ignoreCase = true) ||
                                result.diseaseName.equals("Invalid / Non-Rubber Leaf", ignoreCase = true) ||
                                result.confidence < 0.35f

                val finalResult = if (isClutter) {
                    result.copy(
                        diseaseName = "Uncertain / Non-Rubber Leaf. Please capture a closer photo."
                    )
                } else {
                    result
                }
                prediction = finalResult
                
                // Save Clean Leaf image locally for 1:1 Grad-CAM overlay comparison
                val cleanFile = File(
                    requireContext().getExternalFilesDir(Environment.DIRECTORY_PICTURES),
                    "clean_${File(imagePath!!).name}"
                )
                try {
                    val fos = FileOutputStream(cleanFile)
                    cleanBitmap.compress(Bitmap.CompressFormat.JPEG, 95, fos)
                    fos.flush()
                    fos.close()
                    cleanLeafPath = cleanFile.absolutePath
                } catch (e: Exception) {
                    e.printStackTrace()
                }

                // Generate Grad-CAM Heatmap overlay on original photo
                val overlayBitmap = GradCamUtils.generateOverlay(bitmap, finalResult.heatmap)
                
                // Save Heatmap overlay locally
                val heatmapFile = File(
                    requireContext().getExternalFilesDir(Environment.DIRECTORY_PICTURES),
                    "heatmap_${File(imagePath!!).name}"
                )
                try {
                    val fos = FileOutputStream(heatmapFile)
                    overlayBitmap.compress(Bitmap.CompressFormat.JPEG, 95, fos)
                    fos.flush()
                    fos.close()
                    heatmapOverlayPath = heatmapFile.absolutePath
                } catch (e: Exception) {
                    e.printStackTrace()
                }
                overlayBitmap.recycle()


                // Update UI on main thread
                withContext(Dispatchers.Main) {
                    displayResults(finalResult, sevResult, lang)
                }
            }
        }
    }

    private fun displayResults(result: PredictionResult, sev: SeverityResult, lang: String) {
        if (_binding == null) return

        binding.tvPredictedDisease.text = result.diseaseName

        val isHealthy = result.diseaseName.equals("Healthy", ignoreCase = true)
        val isInvalid = result.diseaseName.contains("Uncertain", ignoreCase = true) ||
                        result.diseaseName.contains("No leaf detected", ignoreCase = true) ||
                        result.diseaseName.contains("severely blurred", ignoreCase = true) ||
                        result.diseaseName.contains("confidence is low", ignoreCase = true) ||
                        result.diseaseName.equals("Invalid / Non-Rubber Leaf", ignoreCase = true) ||
                        result.diseaseName.equals("Background / Non-Rubber Leaf", ignoreCase = true)

        if (!isInvalid && result.confidence in 0.35f..0.70f) {
            binding.tvConfidence.text = String.format("%.1f%% (Soft Focus)", result.confidence * 100)
        } else {
            binding.tvConfidence.text = String.format("%.1f%%", result.confidence * 100)
        }
        binding.tvLatency.text = "${result.inferenceTimeMs} ms"

        // Set Health Status Badge
        binding.tvHealthStatus.text = if (isInvalid) {
            binding.tvHealthStatus.setBackgroundColor(requireContext().getColor(R.color.dark_gray))
            "Invalid Image"
        } else if (isHealthy) {
            binding.tvHealthStatus.setBackgroundColor(requireContext().getColor(R.color.severity_healthy))
            getString(R.string.status_healthy)
        } else {
            binding.tvHealthStatus.setBackgroundColor(requireContext().getColor(R.color.error))
            getString(R.string.status_diseased)
        }

        // Adjust buttons based on Healthy/Invalid class
        if (isInvalid) {
            binding.btnFlowSeverity.visibility = View.GONE
            binding.btnFlowGradcam.visibility = View.GONE
            binding.btnFlowRecs.visibility = View.GONE
            binding.btnSaveRecord.visibility = View.GONE
            binding.btnExportPdfPrediction.visibility = View.GONE
        } else if (isHealthy) {
            binding.btnFlowSeverity.visibility = View.GONE
            binding.btnFlowGradcam.visibility = View.GONE
            binding.btnFlowRecs.visibility = View.VISIBLE
            binding.btnSaveRecord.visibility = View.VISIBLE
            binding.btnExportPdfPrediction.visibility = View.VISIBLE
        } else {
            binding.btnFlowSeverity.visibility = View.VISIBLE
            binding.btnFlowGradcam.visibility = View.VISIBLE
            binding.btnFlowRecs.visibility = View.VISIBLE
            binding.btnSaveRecord.visibility = View.VISIBLE
            binding.btnExportPdfPrediction.visibility = View.VISIBLE
        }

        // Populate Class Probabilities row list
        binding.llProbabilityList.removeAllViews()
        val inflater = LayoutInflater.from(context)
        
        if (!isInvalid) {
            result.classProbabilities.forEach { (className, prob) ->
                val rowBinding = ItemProbabilityRowBinding.inflate(inflater, binding.llProbabilityList, false)
                rowBinding.tvProbClassName.text = className
                rowBinding.pbProbBar.progress = (prob * 100).toInt()
                rowBinding.tvProbPercent.text = String.format("%.1f%%", prob * 100)
                
                binding.llProbabilityList.addView(rowBinding.root)
            }
        } else {
            val rowBinding = ItemProbabilityRowBinding.inflate(inflater, binding.llProbabilityList, false)
            rowBinding.tvProbClassName.text = result.diseaseName
            rowBinding.pbProbBar.visibility = View.GONE
            rowBinding.tvProbPercent.text = "⚠️"
            binding.llProbabilityList.addView(rowBinding.root)
        }

        // Speak aloud predictions via TTS
        val isKannada = lang.equals("kn", ignoreCase = true)
        val readText = if (isInvalid) {
            if (isKannada) {
                "ಅಮಾನ್ಯ ಚಿತ್ರ ಪತ್ತೆಯಾಗಿದೆ. ದಯವಿಟ್ಟು ರಬ್ಬರ್ ಎಲೆಯ ಸ್ಪಷ್ಟ ಚಿತ್ರವನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ."
            } else {
                "Invalid image detected. Please capture a clear, close-up photo of a rubber leaf."
            }
        } else if (isHealthy) {
            if (isKannada) {
                "ಪತ್ತೆಯಾದ ರೋಗ ಆರೋಗ್ಯಕರ, ದಯವಿಟ್ಟು ವರದಿಯನ್ನು ಉಳಿಸಿ."
            } else {
                "The leaf is healthy. Please save the record."
            }
        } else {
            if (isKannada) {
                "ಪತ್ತೆಯಾದ ರೋಗ ${result.diseaseName}, ತೀವ್ರತೆ ${sev.severityLabel}. ದಯವಿಟ್ಟು ವರದಿಯನ್ನು ಉಳಿಸಿ."
            } else {
                "Detected disease is ${result.diseaseName}, with ${sev.severityLabel} severity. Please review the recommendations."
            }
        }
        ttsHelper?.speak(readText)

        // Save last scan details in SharedPreferences for Chatbot context
        if (!isInvalid) {
            val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
            prefs.edit().apply {
                putString("last_scan_disease", result.diseaseName)
                putString("last_scan_severity", "${sev.severityLabel} (${String.format("%.1f%%", sev.severityPercentage)})")
                apply()
            }
        }
    }

    private fun saveRecordToDatabase(onSaved: () -> Unit = {}) {
        if (isSaved && savedRecordId != -1L) {
            onSaved()
            return
        }
        val pred = prediction ?: return
        val sev = severity ?: return
        val path = imagePath ?: return
        val heatPath = heatmapOverlayPath ?: ""

        val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
        val farmerName = prefs.getString("farmer_name", "Farmer") ?: "Farmer"

        val record = ScanRecordEntity(
            farmerName = farmerName,
            diseaseName = pred.diseaseName,
            confidence = pred.confidence,
            severityLabel = sev.severityLabel,
            severityPercentage = sev.severityPercentage,
            dateString = SimpleDateFormat("dd MMM yyyy, HH:mm", Locale.getDefault()).format(Date()),
            imagePath = path,
            heatmapPath = heatPath
        )

        viewModel.saveScanRecord(record) { id ->
            savedRecordId = id
            isSaved = true
            activity?.runOnUiThread {
                binding.btnSaveRecord.isEnabled = false
                Toast.makeText(context, "Report saved to history successfully!", Toast.LENGTH_SHORT).show()
                onSaved()
            }
        }
    }

    private fun exportPdfReport() {
        if (prediction == null || severity == null) return
        
        val runExport = {
            lifecycleScope.launch(Dispatchers.IO) {
                // Fetch the record we just saved
                val db = AppDatabase.getDatabase(requireContext())
                val record = db.scanRecordDao().getRecordById(savedRecordId.toInt())
                
                if (record != null) {
                    val pdfFile = File(
                        requireContext().getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS),
                        "RubberReport_${record.id}.pdf"
                    )
                    
                    val isKannada = LanguageHelper.getLanguage(requireContext()) == "kn"
                    PdfGenerator.generateReport(requireContext(), record, pdfFile, isKannada)
                    
                    withContext(Dispatchers.Main) {
                        showPdfOptionsDialog(pdfFile)
                    }
                }
            }
        }

        if (!isSaved) {
            // Save automatically first, then run export
            saveRecordToDatabase {
                runExport()
            }
        } else {
            runExport()
        }
    }

    private fun showPdfOptionsDialog(pdfFile: File) {
        val context = requireContext()
        val uri = androidx.core.content.FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            pdfFile
        )

        val isKannada = LanguageHelper.getLanguage(context) == "kn"
        val title = if (isKannada) "ಪಿಡಿಎಫ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ" else "PDF Report Ready"
        val message = if (isKannada) "ವರದಿಯನ್ನು ತೆರೆಯಲು ಅಥವಾ ಹಂಚಿಕೊಳ್ಳಲು ಬಯಸುವಿರಾ?" else "Would you like to open or share the diagnostic report?"
        val openText = if (isKannada) "ತೆರೆ" else "Open"
        val shareText = if (isKannada) "ಹಂಚಿಕೊ" else "Share"
        val cancelText = if (isKannada) "ರದ್ದುಮಾಡು" else "Cancel"

        android.app.AlertDialog.Builder(context)
            .setTitle(title)
            .setMessage(message)
            .setPositiveButton(openText) { _, _ ->
                val intent = android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, "application/pdf")
                    addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                try {
                    startActivity(intent)
                } catch (e: Exception) {
                    Toast.makeText(context, if (isKannada) "ಪಿಡಿಎಫ್ ವೀಕ್ಷಕ ಅಪ್ಲಿಕೇಶನ್ ಇಲ್ಲ." else "No PDF viewer app found.", Toast.LENGTH_LONG).show()
                }
            }
            .setNegativeButton(shareText) { _, _ ->
                val intent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                    type = "application/pdf"
                    putExtra(android.content.Intent.EXTRA_STREAM, uri)
                    addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                startActivity(android.content.Intent.createChooser(intent, if (isKannada) "ವರದಿ ಹಂಚಿಕೊಳ್ಳಿ" else "Share Diagnostic Report"))
            }
            .setNeutralButton(cancelText, null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
        classifier?.close()
        classifier = null
        ttsHelper?.shutdown()
        ttsHelper = null
    }
}
