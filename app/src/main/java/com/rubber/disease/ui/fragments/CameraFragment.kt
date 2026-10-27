package com.rubber.disease.ui.fragments

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.os.Bundle
import android.os.Environment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.rubber.disease.R
import com.rubber.disease.databinding.FragmentCameraBinding
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import kotlin.math.min

class CameraFragment : Fragment() {

    private var _binding: FragmentCameraBinding? = null
    private val binding get() = _binding!!

    private var imageCapture: ImageCapture? = null
    private lateinit var cameraExecutor: ExecutorService

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            startCamera()
        } else {
            Toast.makeText(context, "Camera permission is required to scan leaves.", Toast.LENGTH_LONG).show()
            findNavController().navigateUp()
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentCameraBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        cameraExecutor = Executors.newSingleThreadExecutor()

        // Check Permissions
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            requestPermissionLauncher.launch(Manifest.permission.CAMERA)
        }

        binding.btnShutter.setOnClickListener {
            takePhoto()
        }

        binding.btnCameraBack.setOnClickListener {
            findNavController().navigateUp()
        }
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(requireContext())
        cameraProviderFuture.addListener({
            val cameraProvider: ProcessCameraProvider = cameraProviderFuture.get()

            // Preview
            val preview = Preview.Builder()
                .build()
                .also {
                    it.setSurfaceProvider(binding.viewFinder.surfaceProvider)
                }

            // ImageCapture
            imageCapture = ImageCapture.Builder()
                .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                .build()

            // Select back camera as default
            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

            try {
                // Unbind use cases before rebinding
                cameraProvider.unbindAll()

                // Bind use cases to camera
                cameraProvider.bindToLifecycle(
                    viewLifecycleOwner, cameraSelector, preview, imageCapture
                )
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }, ContextCompat.getMainExecutor(requireContext()))
    }

    private fun takePhoto() {
        val imgCapture = imageCapture ?: return

        // Create time-stamped output file to hold the raw image
        val photoFile = File(
            requireContext().getExternalFilesDir(Environment.DIRECTORY_PICTURES),
            SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(System.currentTimeMillis()) + "_raw.jpg"
        )

        // Create output options object which contains file + metadata
        val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()

        binding.btnShutter.isEnabled = false

        imgCapture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(requireContext()),
            object : ImageCapture.OnImageSavedCallback {
                override fun onError(exc: ImageCaptureException) {
                    binding.btnShutter.isEnabled = true
                    Toast.makeText(context, "Capture failed: ${exc.message}", Toast.LENGTH_SHORT).show()
                }

                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    processAndCropImage(photoFile)
                }
            }
        )
    }

    private fun processAndCropImage(rawFile: File) {
        cameraExecutor.execute {
            try {
                // Load original bitmap
                val originalBitmap = BitmapFactory.decodeFile(rawFile.absolutePath)
                if (originalBitmap == null) {
                    activity?.runOnUiThread {
                        binding.btnShutter.isEnabled = true
                        Toast.makeText(context, "Error decoding image.", Toast.LENGTH_SHORT).show()
                    }
                    return@execute
                }

                // 1. Correct image rotation if necessary
                val correctedBitmap = correctImageOrientation(originalBitmap, rawFile.absolutePath)

                // 2. Perform a square crop centered on the image
                // This corresponds to the user centering the leaf inside the square overlay
                val width = correctedBitmap.width
                val height = correctedBitmap.height
                val side = min(width, height)
                val x = (width - side) / 2
                val y = (height - side) / 2
                val croppedBitmap = Bitmap.createBitmap(correctedBitmap, x, y, side, side)

                // 3. Save cropped bitmap back to file
                val croppedFile = File(
                    requireContext().getExternalFilesDir(Environment.DIRECTORY_PICTURES),
                    SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(System.currentTimeMillis()) + ".jpg"
                )
                
                val out = FileOutputStream(croppedFile)
                croppedBitmap.compress(Bitmap.CompressFormat.JPEG, 90, out)
                out.flush()
                out.close()

                // Recyle bitmaps
                originalBitmap.recycle()
                if (correctedBitmap != originalBitmap) correctedBitmap.recycle()
                croppedBitmap.recycle()

                // Delete raw temp file
                rawFile.delete()

                // 4. Navigate back to UI thread and transition to Prediction screen
                activity?.runOnUiThread {
                    binding.btnShutter.isEnabled = true
                    val bundle = Bundle().apply {
                        putString("imagePath", croppedFile.absolutePath)
                    }
                    findNavController().navigate(R.id.action_cameraFragment_to_predictionFragment, bundle)
                }
            } catch (e: Exception) {
                e.printStackTrace()
                activity?.runOnUiThread {
                    binding.btnShutter.isEnabled = true
                    Toast.makeText(context, "Error cropping image: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
    private fun correctImageOrientation(bitmap: Bitmap, path: String): Bitmap {
        try {
            val exifInterface = android.media.ExifInterface(path)
            val orientation = exifInterface.getAttributeInt(
                android.media.ExifInterface.TAG_ORIENTATION,
                android.media.ExifInterface.ORIENTATION_NORMAL
            )

            val matrix = Matrix()
            when (orientation) {
                android.media.ExifInterface.ORIENTATION_ROTATE_90 -> matrix.postRotate(90f)
                android.media.ExifInterface.ORIENTATION_ROTATE_180 -> matrix.postRotate(180f)
                android.media.ExifInterface.ORIENTATION_ROTATE_270 -> matrix.postRotate(270f)
                else -> return bitmap
            }
            return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
        } catch (e: Exception) {
            e.printStackTrace()
            return bitmap
        }
    }

    private fun allPermissionsGranted() = ContextCompat.checkSelfPermission(
        requireContext(), Manifest.permission.CAMERA
    ) == PackageManager.PERMISSION_GRANTED

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
        cameraExecutor.shutdown()
    }
}
