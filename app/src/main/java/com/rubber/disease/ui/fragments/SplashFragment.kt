package com.rubber.disease.ui.fragments

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.rubber.disease.R
import com.rubber.disease.databinding.FragmentSplashBinding
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class SplashFragment : Fragment() {

    private var _binding: FragmentSplashBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSplashBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Wait 2500ms and navigate to Welcome Screen
        viewLifecycleOwner.lifecycleScope.launch {
            delay(2500)
            if (isAdded) {
                // If user is already logged in, navigate straight to Home dashboard!
                val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
                val isLoggedIn = prefs.getBoolean("is_logged_in", false)
                
                if (isLoggedIn) {
                    findNavController().navigate(R.id.action_splashFragment_to_welcomeFragment)
                    // The welcome fragment will check state and route accordingly,
                    // or we can route directly to Home if needed.
                    // Routing to Welcome first lets it do localized checks, or we can handle it here.
                } else {
                    findNavController().navigate(R.id.action_splashFragment_to_welcomeFragment)
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
