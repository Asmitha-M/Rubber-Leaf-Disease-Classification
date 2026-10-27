package com.rubber.disease.utils

import android.content.Context
import android.content.SharedPreferences
import android.content.res.Configuration
import java.util.Locale

object LanguageHelper {

    private const val PREFS_NAME = "rubber_guard_prefs"
    private const val KEY_LANG = "app_language"

    fun setLanguage(context: Context, language: String) {
        val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_LANG, language).apply()
        applyLocale(context, language)
    }

    fun getLanguage(context: Context): String {
        val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_LANG, "en") ?: "en"
    }

    fun applyLocale(context: Context, language: String): Context {
        val locale = if (language.equals("kn", ignoreCase = true)) {
            Locale("kn", "IN")
        } else {
            Locale("en")
        }
        
        Locale.setDefault(locale)
        val resources = context.resources
        val configuration = Configuration(resources.configuration)
        configuration.setLocale(locale)
        
        // On API 17+ createConfigurationContext is preferred
        return context.createConfigurationContext(configuration)
    }

    /**
     * Toggles the application language between English ("en") and Kannada ("kn").
     * @return The newly set language code.
     */
    fun toggleLanguage(context: Context): String {
        val current = getLanguage(context)
        val newLang = if (current == "en") "kn" else "en"
        setLanguage(context, newLang)
        return newLang
    }
}
