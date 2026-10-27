package com.rubber.disease.ui.fragments

import android.graphics.BitmapFactory
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.rubber.disease.databinding.FragmentSeverityBinding
import com.rubber.disease.ml.OpenCVSeverityEstimator
import java.io.File

class SeverityFragment : Fragment() {

    private var _binding: FragmentSeverityBinding? = null
    private val binding get() = _binding!!
    private val severityEstimator = OpenCVSeverityEstimator()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSeverityBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.toolbarSeverity.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        val imagePath = arguments?.getString("imagePath")
        val isHealthy = arguments?.getBoolean("isHealthy") ?: false

        if (imagePath != null) {
            val file = File(imagePath)
            if (file.exists()) {
                val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                binding.ivSeverityImage.setImageBitmap(bitmap)

                // Compute Severity offline using OpenCV
                val result = severityEstimator.estimateSeverity(bitmap, isHealthy)

                // Update UI elements
                binding.tvSeverityPercentage.text = String.format("%.1f%%", result.severityPercentage)
                binding.lpiSeverityMeter.progress = result.severityPercentage.toInt()
                binding.lpiSeverityMeter.setIndicatorColor(result.colorCode)
                
                binding.tvSeverityLabel.text = result.severityLabel
                
                // Colorize badge dynamically
                val drawable = binding.tvSeverityLabel.background as? GradientDrawable
                    ?: GradientDrawable().apply { cornerRadius = 8f }
                drawable.setColor(result.colorCode)
                binding.tvSeverityLabel.background = drawable
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
