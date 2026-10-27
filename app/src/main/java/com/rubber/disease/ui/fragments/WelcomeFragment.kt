package com.rubber.disease.ui.fragments

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.rubber.disease.R
import com.rubber.disease.databinding.FragmentWelcomeBinding
import com.rubber.disease.utils.LanguageHelper

class WelcomeFragment : Fragment() {

    private var _binding: FragmentWelcomeBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentWelcomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
        val isLoggedIn = prefs.getBoolean("is_logged_in", false)

        // 1. If user is logged in, navigate straight to Home Dashboard
        if (isLoggedIn) {
            findNavController().navigate(R.id.action_welcomeFragment_to_homeFragment)
            return
        }

        // 2. Set current selected language in UI
        val currentLang = LanguageHelper.getLanguage(requireContext())
        if (currentLang == "kn") {
            binding.rbKannada.isChecked = true
        } else {
            binding.rbEnglish.isChecked = true
        }

        // 3. Language Selector Listener
        binding.rgLanguage.setOnCheckedChangeListener { _, checkedId ->
            val selectedLang = if (checkedId == R.id.rb_kannada) "kn" else "en"
            if (selectedLang != LanguageHelper.getLanguage(requireContext())) {
                LanguageHelper.setLanguage(requireContext(), selectedLang)
                // Recreate the activity to apply language changes dynamically
                requireActivity().recreate()
            }
        }

        // 4. Onboarding Navigation clicks
        binding.btnLoginWelcome.setOnClickListener {
            findNavController().navigate(R.id.action_welcomeFragment_to_loginFragment)
        }

        binding.btnRegisterWelcome.setOnClickListener {
            findNavController().navigate(R.id.action_welcomeFragment_to_registerFragment)
        }

        binding.btnGuest.setOnClickListener {
            // Set guest session details
            prefs.edit().apply {
                putBoolean("is_logged_in", true)
                putBoolean("is_guest", true)
                putString("farmer_name", "Farmer Guest")
                putString("farmer_username", "guest_farmer")
                apply()
            }
            findNavController().navigate(R.id.action_welcomeFragment_to_homeFragment)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
