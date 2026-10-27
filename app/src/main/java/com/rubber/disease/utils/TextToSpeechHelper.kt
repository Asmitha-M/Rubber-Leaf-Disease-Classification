package com.rubber.disease.utils

import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale

class TextToSpeechHelper(
    context: Context,
    initialLanguage: String = "en",
    private val onInitSuccess: () -> Unit = {}
) : TextToSpeech.OnInitListener {

    private var tts: TextToSpeech? = TextToSpeech(context.applicationContext, this)
    private var isReady = false
    private var currentLanguage = initialLanguage

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            setLanguage(currentLanguage)
            isReady = true
            onInitSuccess()
        }
    }

    fun setLanguage(langCode: String) {
        currentLanguage = langCode
        val locale = if (langCode.equals("kn", ignoreCase = true)) {
            Locale("kn", "IN") // Kannada (India)
        } else {
            Locale.ENGLISH
        }
        
        val result = tts?.setLanguage(locale)
        if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
            // Fallback to default if language is not installed
            tts?.setLanguage(Locale.ENGLISH)
        }
    }

    fun speak(text: String) {
        if (isReady && tts != null) {
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "RubberGuardTTS")
        }
    }

    fun stop() {
        tts?.stop()
    }

    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
        tts = null
        isReady = false
    }
}
