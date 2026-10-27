package com.rubber.disease.ui.fragments

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.rubber.disease.R
import com.rubber.disease.databinding.FragmentGalleryBinding
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Locale
import kotlin.math.min

class GalleryFragment : Fragment() {

    private var _binding: FragmentGalleryBinding? = null
    private val binding get() = _binding!!

    private var selectedImageUri: Uri? = null

    private val selectImageLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            selectedImageUri = uri
            binding.ivGalleryPreview.setImageURI(uri)
            binding.ivGalleryPreview.imageTintList = null // Remove green tint from placeholder
            binding.tvGalleryPlaceholder.visibility = View.GONE
            binding.btnAnalyzeGallery.isEnabled = true
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentGalleryBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.toolbarGallery.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        binding.btnSelectGallery.setOnClickListener {
            selectImageLauncher.launch("image/*")
        }

        binding.btnAnalyzeGallery.setOnClickListener {
            val uri = selectedImageUri ?: return@setOnClickListener
            cropAndAnalyze(uri)
        }
    }

    private fun cropAndAnalyze(uri: Uri) {
        try {
            val inputStream = requireContext().contentResolver.openInputStream(uri)
            val originalBitmap = BitmapFactory.decodeStream(inputStream)
            inputStream?.close()

            if (originalBitmap == null) {
                Toast.makeText(context, "Error reading image file", Toast.LENGTH_SHORT).show()
                return
            }

            // Perform center square crop
            val width = originalBitmap.width
            val height = originalBitmap.height
            val side = min(width, height)
            val x = (width - side) / 2
            val y = (height - side) / 2
            val croppedBitmap = Bitmap.createBitmap(originalBitmap, x, y, side, side)

            // Save cropped bitmap to local storage
            val croppedFile = File(
                requireContext().getExternalFilesDir(Environment.DIRECTORY_PICTURES),
                "gallery_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(System.currentTimeMillis())}.jpg"
            )
            
            val out = FileOutputStream(croppedFile)
            croppedBitmap.compress(Bitmap.CompressFormat.JPEG, 90, out)
            out.flush()
            out.close()

            originalBitmap.recycle()
            croppedBitmap.recycle()

            // Navigate to Prediction
            val bundle = Bundle().apply {
                putString("imagePath", croppedFile.absolutePath)
            }
            findNavController().navigate(R.id.action_galleryFragment_to_predictionFragment, bundle)

        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(context, "Failed to crop image: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
