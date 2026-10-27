package com.rubber.disease.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.rubber.disease.data.AppDatabase
import com.rubber.disease.databinding.FragmentForgotPasswordBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.security.MessageDigest

class ForgotPasswordFragment : Fragment() {

    private var _binding: FragmentForgotPasswordBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentForgotPasswordBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.btnForgotSubmit.setOnClickListener {
            val input = binding.etForgotInput.text.toString().trim()
            if (input.isEmpty()) {
                binding.tilForgotInput.error = "Please enter your username or email"
                return@setOnClickListener
            } else {
                binding.tilForgotInput.error = null
            }

            // Database operation
            lifecycleScope.launch {
                val db = AppDatabase.getDatabase(requireContext())
                val user = withContext(Dispatchers.IO) {
                    db.userDao().getUserByUsername(input) ?: db.userDao().getUserByEmail(input)
                }

                if (user != null) {
                    // Update user password to "rubber123" offline
                    val newPasswordPlain = "rubber123"
                    val bytes = MessageDigest.getInstance("SHA-256").digest(newPasswordPlain.toByteArray())
                    val newHash = bytes.joinToString("") { "%02x".format(it) }
                    
                    val updatedUser = user.copy(passwordHash = newHash)
                    withContext(Dispatchers.IO) {
                        db.userDao().updateUser(updatedUser)
                    }

                    binding.tvRetrievedInfo.text = "Account found for: ${user.fullName}. For security, your password has been reset offline."
                    binding.tvRetrievedPassword.text = "New Password: '$newPasswordPlain'"
                    binding.cardForgotResult.visibility = View.VISIBLE
                } else {
                    binding.cardForgotResult.visibility = View.GONE
                    Toast.makeText(context, "No profile found with that email/username", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
