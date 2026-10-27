package com.rubber.disease.ui.fragments

import android.content.Context
import android.content.SharedPreferences
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.app.AppCompatDelegate
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.rubber.disease.R
import com.rubber.disease.databinding.FragmentSettingsBinding
import com.rubber.disease.utils.LanguageHelper

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!
    private lateinit var prefs: SharedPreferences

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)

        binding.toolbarSettings.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        // 1. Load toggle states
        binding.switchDarkMode.isChecked = prefs.getBoolean("dark_mode", false)
        binding.switchTts.isChecked = prefs.getBoolean("tts_enabled", true)
        binding.switchNotifications.isChecked = prefs.getBoolean("notifications_enabled", true)

        // 2. Set toggle listeners
        binding.switchDarkMode.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("dark_mode", isChecked).apply()
            if (isChecked) {
                AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
            } else {
                AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
            }
        }

        binding.switchTts.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("tts_enabled", isChecked).apply()
        }

        binding.switchNotifications.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("notifications_enabled", isChecked).apply()
        }

        // 3. Set navigation row clicks
        binding.tvSettingsLanguage.setOnClickListener {
            val newLang = LanguageHelper.toggleLanguage(requireContext())
            val msg = if (newLang == "kn") "ಭಾಷೆಯನ್ನು ಕನ್ನಡಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗಿದೆ" else "Language changed to English"
            Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
            requireActivity().recreate()
        }

        binding.tvSettingsAbout.setOnClickListener {
            findNavController().navigate(R.id.action_settingsFragment_to_aboutFragment)
        }

        binding.tvSettingsHelp.setOnClickListener {
            findNavController().navigate(R.id.action_settingsFragment_to_helpFaqFragment)
        }

        binding.tvSettingsExpert.setOnClickListener {
            findNavController().navigate(R.id.action_settingsFragment_to_contactExpertFragment)
        }

        binding.tvSettingsPrivacy.setOnClickListener {
            showPrivacyPolicyDialog()
        }

        // 4. Logout click listener
        binding.btnLogout.setOnClickListener {
            prefs.edit().apply {
                putBoolean("is_logged_in", false)
                putBoolean("is_guest", false)
                remove("farmer_id")
                remove("farmer_name")
                remove("farmer_username")
                remove("last_scan_disease")
                remove("last_scan_severity")
                apply()
            }
            Toast.makeText(context, "Logged out successfully.", Toast.LENGTH_SHORT).show()
            findNavController().navigate(R.id.action_settingsFragment_to_welcomeFragment)
        }
    }

    private fun showPrivacyPolicyDialog() {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("Privacy Policy")
            .setMessage(
                "RubberGuard AI is designed with offline-first security. " +
                "All image captures, TensorFlow Lite model classifications, OpenCV calculations, and diagnostic scan histories " +
                "are computed and stored locally on your device.\n\n" +
                "No leaf images, farmer profiles, or location coordinates are uploaded to external cloud servers, " +
                "ensuring complete data ownership and security for Karnataka's rubber growers."
            )
            .setPositiveButton("OK", null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
