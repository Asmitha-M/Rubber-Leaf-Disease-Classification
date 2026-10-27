package com.rubber.disease.ui.fragments

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.google.android.material.tabs.TabLayout
import com.rubber.disease.databinding.FragmentGradcamBinding
import java.io.File

class GradCamFragment : Fragment() {

    private var _binding: FragmentGradcamBinding? = null
    private val binding get() = _binding!!

    private var originalBitmap: Bitmap? = null
    private var heatmapBitmap: Bitmap? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentGradcamBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.toolbarGradcam.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        val imagePath = arguments?.getString("imagePath")
        val heatmapPath = arguments?.getString("heatmapPath")

        // Load Bitmaps offline
        if (imagePath != null) {
            val file = File(imagePath)
            if (file.exists()) {
                originalBitmap = BitmapFactory.decodeFile(file.absolutePath)
                // Set default display to original
                binding.ivGradcamDisplay.setImageBitmap(originalBitmap)
            }
        }

        if (heatmapPath != null) {
            val file = File(heatmapPath)
            if (file.exists()) {
                heatmapBitmap = BitmapFactory.decodeFile(file.absolutePath)
            }
        }

        // TabLayout Listener to toggle images
        binding.tabLayoutGradcam.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab?) {
                when (tab?.position) {
                    0 -> {
                        if (originalBitmap != null) {
                            binding.ivGradcamDisplay.setImageBitmap(originalBitmap)
                        }
                    }
                    1 -> {
                        if (heatmapBitmap != null) {
                            binding.ivGradcamDisplay.setImageBitmap(heatmapBitmap)
                        }
                    }
                }
            }

            override fun onTabUnselected(tab: TabLayout.Tab?) {}
            override fun onTabReselected(tab: TabLayout.Tab?) {}
        })
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
        // Recycle bitmaps to save memory
        originalBitmap?.recycle()
        heatmapBitmap?.recycle()
    }
}
