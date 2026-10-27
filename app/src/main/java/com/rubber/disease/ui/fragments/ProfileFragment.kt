package com.rubber.disease.ui.fragments

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.fragment.findNavController
import com.rubber.disease.databinding.FragmentProfileBinding
import com.rubber.disease.viewmodels.MainViewModel

class ProfileFragment : Fragment() {

    private var _binding: FragmentProfileBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: MainViewModel
    
    private var userId: Int = -1
    private var isGuest: Boolean = false

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentProfileBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel = ViewModelProvider(requireActivity())[MainViewModel::class.java]

        binding.toolbarProfile.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        // Check if guest
        val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
        isGuest = prefs.getBoolean("is_guest", false)
        userId = prefs.getInt("farmer_id", -1)

        if (isGuest) {
            setupGuestProfile()
        } else {
            setupUserProfile()
        }
    }

    private fun setupGuestProfile() {
        binding.etProfileName.setText("Farmer Guest")
        binding.etProfileEmail.setText("guest@rubberguard.com")
        binding.etProfilePhone.setText("+91 XXXXXXXXXX")
        binding.etProfileLocation.setText("Karnataka, India")
        binding.tvAvatarInitials.text = "G"

        // Disable input editing
        binding.etProfileName.isEnabled = false
        binding.etProfileEmail.isEnabled = false
        binding.etProfilePhone.isEnabled = false
        binding.etProfileLocation.isEnabled = false
        binding.btnUpdateProfile.isEnabled = false
        
        binding.btnUpdateProfile.text = "Profile Editing Disabled (Guest)"
    }

    private fun setupUserProfile() {
        if (userId == -1) return

        // Query profile from database
        viewModel.getUserProfile(userId)
        
        viewModel.currentUser.observe(viewLifecycleOwner) { user ->
            if (user != null) {
                binding.etProfileName.setText(user.fullName)
                binding.etProfileEmail.setText(user.email)
                binding.etProfilePhone.setText(user.phone)
                binding.etProfileLocation.setText(user.location)
                
                if (user.fullName.isNotEmpty()) {
                    binding.tvAvatarInitials.text = user.fullName.take(1).uppercase()
                }
            }
        }

        binding.btnUpdateProfile.setOnClickListener {
            val name = binding.etProfileName.text.toString().trim()
            val email = binding.etProfileEmail.text.toString().trim()
            val phone = binding.etProfilePhone.text.toString().trim()
            val location = binding.etProfileLocation.text.toString().trim()

            if (name.isEmpty() || email.isEmpty() || phone.isEmpty() || location.isEmpty()) {
                Toast.makeText(context, "All profile fields are required", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val currentUserVal = viewModel.currentUser.value
            if (currentUserVal != null) {
                val updatedUser = currentUserVal.copy(
                    fullName = name,
                    email = email,
                    phone = phone,
                    location = location
                )
                
                viewModel.updateUserProfile(updatedUser)
                
                // Cache name update in preferences
                val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
                prefs.edit().putString("farmer_name", name).apply()
                
                Toast.makeText(context, "Profile updated successfully!", Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
