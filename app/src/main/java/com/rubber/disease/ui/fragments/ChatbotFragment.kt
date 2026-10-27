package com.rubber.disease.ui.fragments

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.rubber.disease.adapters.ChatAdapter
import com.rubber.disease.adapters.ChatMessage
import com.rubber.disease.databinding.FragmentChatbotBinding
import com.rubber.disease.utils.ChatbotEngine
import com.rubber.disease.utils.LanguageHelper
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class ChatbotFragment : Fragment() {

    private var _binding: FragmentChatbotBinding? = null
    private val binding get() = _binding!!
    
    private lateinit var adapter: ChatAdapter
    private var lastScanDisease: String? = null
    private var lastScanSeverity: String? = null
    private var lang = "en"

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentChatbotBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.toolbarChatbot.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        // 1. Fetch preferences context
        val prefs = requireActivity().getSharedPreferences("rubber_guard_prefs", Context.MODE_PRIVATE)
        lastScanDisease = prefs.getString("last_scan_disease", null)
        lastScanSeverity = prefs.getString("last_scan_severity", null)
        lang = LanguageHelper.getLanguage(requireContext())

        // 2. Initialize chat adapter with a welcome greeting message
        val isKannada = lang == "kn"
        val welcomeMsg = if (isKannada) {
            "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ರಬ್ಬರ್ ಗಾರ್ಡ್ ಸಹಾಯ ಚಾಟ್‌ಬಾಟ್. ನಿಮ್ಮ ಇತ್ತೀಚಿನ ಸ್ಕ್ಯಾನ್ ಅಥವಾ ಚಿಕಿತ್ಸೆಗಳ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ."
        } else {
            "Hello! I am your RubberGuard Agricultural Assistant. Ask me questions about leaf diseases, organic/chemical treatments, fertilizers, or prevention."
        }
        
        adapter = ChatAdapter(mutableListOf(ChatMessage(welcomeMsg, false)))
        binding.rvChatMessages.layoutManager = LinearLayoutManager(context).apply {
            stackFromEnd = true
        }
        binding.rvChatMessages.adapter = adapter

        // 3. Send action listener
        binding.btnChatSend.setOnClickListener {
            sendMessage()
        }
    }

    private fun sendMessage() {
        val text = binding.etChatInput.text.toString().trim()
        if (text.isEmpty()) return

        // Add user message
        adapter.addMessage(ChatMessage(text, true))
        binding.etChatInput.text.clear()
        binding.rvChatMessages.scrollToPosition(adapter.itemCount - 1)

        // Simulate typing delay & retrieve response offline
        viewLifecycleOwner.lifecycleScope.launch {
            binding.btnChatSend.isEnabled = false
            delay(600) // Simulating response generation delay
            
            val response = ChatbotEngine.getResponse(
                text,
                lastScanDisease,
                lastScanSeverity,
                lang
            )
            
            adapter.addMessage(ChatMessage(response, false))
            binding.rvChatMessages.scrollToPosition(adapter.itemCount - 1)
            binding.btnChatSend.isEnabled = true
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
