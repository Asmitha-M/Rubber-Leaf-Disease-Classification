package com.rubber.disease.ui.fragments

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.rubber.disease.databinding.FragmentContactExpertBinding

class ContactExpertFragment : Fragment() {

    private var _binding: FragmentContactExpertBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentContactExpertBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.toolbarExpert.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        binding.cardExpertMangaluru.setOnClickListener {
            dialNumber("+918242422000")
        }

        binding.cardExpertKadaba.setOnClickListener {
            dialNumber("+918251260200")
        }

        binding.cardExpertUdupi.setOnClickListener {
            dialNumber("+918202521100")
        }
    }

    private fun dialNumber(phoneNumber: String) {
        try {
            val intent = Intent(Intent.ACTION_DIAL).apply {
                data = Uri.parse("tel:$phoneNumber")
            }
            startActivity(intent)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
