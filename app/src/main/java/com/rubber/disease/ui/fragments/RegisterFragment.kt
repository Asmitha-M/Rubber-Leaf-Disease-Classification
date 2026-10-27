package com.rubber.disease.ui.fragments

import android.os.Bundle
import android.util.Patterns
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.fragment.findNavController
import com.rubber.disease.R
import com.rubber.disease.databinding.FragmentRegisterBinding
import com.rubber.disease.viewmodels.MainViewModel

class RegisterFragment : Fragment() {

    private var _binding: FragmentRegisterBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: MainViewModel

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentRegisterBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel = ViewModelProvider(this)[MainViewModel::class.java]

        binding.btnRegisterSubmit.setOnClickListener {
            val fullName = binding.etRegFullname.text.toString().trim()
            val email = binding.etRegEmail.text.toString().trim()
            val username = binding.etRegUsername.text.toString().trim()
            val phone = binding.etRegPhone.text.toString().trim()
            val location = binding.etRegLocation.text.toString().trim()
            val password = binding.etRegPassword.text.toString().trim()
            val confirmPassword = binding.etRegConfirmPassword.text.toString().trim()

            // Validations
            if (fullName.isEmpty()) {
                binding.tilRegFullname.error = "Please enter your name"
                return@setOnClickListener
            } else binding.tilRegFullname.error = null

            if (email.isEmpty() || !Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
                binding.tilRegEmail.error = "Please enter a valid email address"
                return@setOnClickListener
            } else binding.tilRegEmail.error = null

            if (username.length < 4) {
                binding.tilRegUsername.error = "Username must be at least 4 characters"
                return@setOnClickListener
            } else binding.tilRegUsername.error = null

            if (phone.isEmpty()) {
                binding.tilRegPhone.error = "Please enter your phone number"
                return@setOnClickListener
            } else binding.tilRegPhone.error = null

            if (location.isEmpty()) {
                binding.tilRegLocation.error = "Please enter your location/district"
                return@setOnClickListener
            } else binding.tilRegLocation.error = null

            if (password.length < 6) {
                binding.tilRegPassword.error = "Password must be at least 6 characters"
                return@setOnClickListener
            } else binding.tilRegPassword.error = null

            if (password != confirmPassword) {
                binding.tilRegConfirmPassword.error = "Passwords do not match"
                return@setOnClickListener
            } else binding.tilRegConfirmPassword.error = null

            viewModel.register(username, email, password, fullName, phone, location) { success ->
                if (success) {
                    Toast.makeText(context, "Registration Successful! Please login.", Toast.LENGTH_LONG).show()
                    findNavController().navigate(R.id.action_registerFragment_to_loginFragment)
                } else {
                    Toast.makeText(context, "Username or Email already registered", Toast.LENGTH_LONG).show()
                }
            }
        }

        binding.tvLoginLink.setOnClickListener {
            findNavController().navigate(R.id.action_registerFragment_to_loginFragment)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
