package com.rubber.disease.ui.fragments

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.rubber.disease.databinding.FragmentRecommendationBinding
import com.rubber.disease.utils.LanguageHelper
import com.rubber.disease.utils.RecommendationSystem
import com.rubber.disease.utils.TextToSpeechHelper

class RecommendationFragment : Fragment() {

    private var _binding: FragmentRecommendationBinding? = null
    private val binding get() = _binding!!
    
    private var ttsHelper: ttsHelperHolder? = null

    // Helper interface class to safely keep TTS
    private class ttsHelperHolder(context: Context, lang: String) {
        val helper = TextToSpeechHelper(context, lang)
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentRecommendationBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.toolbarRecommendation.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        val diseaseName = arguments?.getString("diseaseName") ?: "Healthy"
        val lang = LanguageHelper.getLanguage(requireContext())

        // Fetch Recommendations
        val recs = RecommendationSystem.getRecommendation(diseaseName, lang)

        // Populate Views
        binding.tvRecDiseaseTitle.text = diseaseName
        binding.tvRecDesc.text = recs.description
        binding.tvRecSymptoms.text = recs.symptoms
        binding.tvRecCauses.text = recs.causes
        binding.tvRecOrganic.text = recs.organicTreatment
        binding.tvRecChemical.text = recs.chemicalTreatment
        binding.tvRecFertilizer.text = recs.recommendedFertilizer
        binding.tvRecPreventive.text = recs.preventiveMeasures
        binding.tvRecRecovery.text = "${recs.recoveryTime} days"
        binding.tvRecPrecautions.text = recs.precautions

        // Text-to-Speech read out
        binding.fabSpeakRecommendation.setOnClickListener {
            if (ttsHelper == null) {
                ttsHelper = ttsHelperHolder(requireContext(), lang)
            }
            
            val textToSpeak = "${recs.description}. Organic treatment is: ${recs.organicTreatment}. Chemical treatment is: ${recs.chemicalTreatment}."
            ttsHelper?.helper?.speak(textToSpeak)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
        ttsHelper?.helper?.shutdown()
    }
}
