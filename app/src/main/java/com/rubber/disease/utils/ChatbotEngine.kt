package com.rubber.disease.utils

import java.util.Locale

object ChatbotEngine {

    private val STOPWORDS = setOf(
        "how", "to", "for", "the", "is", "a", "in", "of", "and", "what",
        "why", "can", "you", "my", "do", "should", "i", "need", "wat",
        "evn", "much", "about", "give", "tell", "me", "which"
    )

    private fun levenshtein(s1: String, s2: String): Int {
        val dp = Array(s1.length + 1) { IntArray(s2.length + 1) }
        for (i in 0..s1.length) dp[i][0] = i
        for (j in 0..s2.length) dp[0][j] = j
        for (i in 1..s1.length) {
            for (j in 1..s2.length) {
                val cost = if (s1[i - 1] == s2[j - 1]) 0 else 1
                dp[i][j] = minOf(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost
                )
            }
        }
        return dp[s1.length][s2.length]
    }

    private fun similarity(s1: String, s2: String): Float {
        val maxLen = maxOf(s1.length, s2.length)
        if (maxLen == 0) return 1.0f
        return 1.0f - (levenshtein(s1, s2).toFloat() / maxLen)
    }

    private fun fuzzyTokenMatch(qt: String, at: String): Float {
        if (qt == at) return 1.0f
        if (qt.length >= 4 && at.length >= 4 && (qt.contains(at) || at.contains(qt))) return 0.95f
        val sim = similarity(qt, at)
        return if (sim >= 0.72f) sim else 0.0f
    }

    private fun matchScore(query: String, aliases: List<String>): Float {
        val qNorm = query.lowercase(Locale.getDefault()).trim()
        
        // 1. Direct phrase or exact alias match
        for (alias in aliases) {
            val aNorm = alias.lowercase(Locale.getDefault()).trim()
            if (qNorm.contains(aNorm)) {
                return 100.0f + aNorm.length
            }
        }

        // 2. Token-level fuzzy match
        val cleanQuery = qNorm.replace(Regex("[^\\p{L}\\p{Nd}\\s]"), " ")
        var qTokens = cleanQuery.split("\\s+".toRegex()).filter { it.length >= 2 && !STOPWORDS.contains(it) }
        if (qTokens.isEmpty()) {
            qTokens = cleanQuery.split("\\s+".toRegex()).filter { it.isNotEmpty() }
        }

        var bestScore = 0.0f
        for (alias in aliases) {
            val cleanAlias = alias.lowercase(Locale.getDefault()).replace(Regex("[^\\p{L}\\p{Nd}\\s]"), " ")
            val aTokens = cleanAlias.split("\\s+".toRegex()).filter { it.length >= 2 && !STOPWORDS.contains(it) }
            if (aTokens.isEmpty()) continue

            var matchedCount = 0
            var simSum = 0.0f

            for (at in aTokens) {
                var bestSim = 0.0f
                for (qt in qTokens) {
                    val sim = fuzzyTokenMatch(qt, at)
                    if (sim > bestSim) bestSim = sim
                }
                if (bestSim >= 0.72f) {
                    matchedCount++
                    simSum += bestSim
                }
            }

            if (matchedCount > 0) {
                val precision = matchedCount.toFloat() / aTokens.size
                val score = (matchedCount * 10.0f) + (simSum * 5.0f) + (precision * 2.0f)
                if (score > bestScore) {
                    bestScore = score
                }
            }
        }
        return bestScore
    }

    private val TOPIC_ALIASES = mapOf(
        "GREETING" to listOf("hello", "hi", "hey", "greetings", "good morning", "namaste", "ನಮಸ್ಕಾರ", "ಹಲೋ", "ಹಾಯ್", "ಶುಭೋದಯ"),
        "BORDEAUX" to listOf("bordeaux", "bordaux", "bordeax", "bordox", "copper sulfate", "bluestone", "lime mix", "copper knife test", "blue spray", "ಬೋರ್ಡೋ", "ಮೈಲುತುತ್ತು", "ಬೋರ್ಡೋ ದ್ರಾವಣ", "ಸುಣ್ಣ ಮೈಲುತುತ್ತು"),
        "TAPPING" to listOf("tap", "tapping", "tapin", "tapper", "latex", "bark cut", "rubber milk", "morning tapping", "tapping slope", "tapping angle", "girth", "ethrel", "ಟ್ಯಾಪಿಂಗ್", "ಹಾಲು ತೆಗೆ", "ಮರ ಕತ್ತರಿಸು", "ಇಳುವರಿ"),
        "FERTILIZER" to listOf("fertilizer", "fartilizer", "furtilizer", "fartiliser", "manure", "compost", "npk", "npkmg", "potash", "urea", "nitrogen", "tree nutrition", "magnesium deficiency", "ಗೊಬ್ಬರ", "ರಸಗೊಬ್ಬರ", "ಪೋಷಕಾಂಶ", "ಪೊಟ್ಯಾಶ್", "ಯೂರಿಯಾ"),
        "SPACING" to listOf("spacing", "spasin", "distance", "plant distance", "square planting", "contour planting", "pit size", "pit preparation", "planting season", "budded stumps", "ಅಂತರ", "ನಾಟಿ", "ಗುಂಡಿ", "ಗಿಡ ನೆಡುವುದು"),
        "CLONES" to listOf("clone", "clones", "clon", "variety", "varieties", "rrii", "rrii 105", "rrii 414", "rrii 430", "pb 260", "best clone", "high yield clone", "ಕ್ಲೋನ್", "ತಳಿಗಳು", "ಉತ್ತಮ ರಬ್ಬರ್ ತಳಿ"),
        "SOIL_CLIMATE" to listOf("soil", "soyl", "laterite", "soil ph", "rainfall", "rain requirement", "climate", "weather", "annual rainfall", "humidity", "temperature", "altitude", "ಮಣ್ಣು", "ಹವಾಮಾನ", "ಮಳೆ", "ಪಿಎಚ್", "ಉಷ್ಣಾಂಶ"),
        "IRRIGATION" to listOf("water", "irrigation", "drought", "summer care", "dry season", "moisture", "mulching", "tree basin mulch", "watering saplings", "watering", "ನೀರು", "ನೀರಾವರಿ", "ಬರಗಾಲ", "ಬೇಸಿಗೆ ನಿರ್ವಹಣೆ"),
        "RAIN_GUARD" to listOf("rain guard", "rain gard", "polythene apron", "monsoon panel", "tree banding compound", "panel rot", "bark rot", "black stripe", "phytophthora meadii", "ರೇನ್ ಗಾರ್ಡ್", "ಮಳೆ ರಕ್ಷಣೆ", "ಪ್ಯಾನಲ್ ಕೊಳೆತ"),
        "WINTERING" to listOf("wintering", "wintring", "natural leaf drop", "annual leaf fall", "yellow leaves shedding", "leaves turning red", "december leaf fall", "annual defoliation", "refoliation", "ಚಳಿಗಾಲದ ಎಲೆ ಉದುರುವಿಕೆ", "ಹಳದಿ ಎಲೆ ಉದುರುವುದು", "ಎಲೆ ಉದುರುವುದು"),
        "PINK_DISEASE" to listOf("pink disease", "corticium", "brown bast", "tapping panel dryness", "tpd", "no latex flow", "dry cut", "bark splitting", "stem rot", "branch rot", "ಪಿಂಕ್ ರೋಗ", "ತೊಗಟೆ", "ಹಾಲು ಬಾರದಿರುವುದು"),
        "COVER_CROPS" to listOf("weed", "weeding", "grass", "cover crop", "cover crops", "mucuna", "mucuna bracteata", "pueraria", "nitrogen fixation", "glyphosate", "herbicide", "ಕಳೆ", "ಕಳೆ ನಿಯಂತ್ರಣ", "ಹೊದಿಕೆ ಬೆಳೆ"),
        "RUBBER_BOARD" to listOf("rubber board", "board", "officer", "helpline", "phone", "contact", "subsidy", "financial assistance", "replanting subsidy", "1800", "ರಬ್ಬರ್ ಬೋರ್ಡ್", "ಸಹಾಯವಾಣಿ", "ಸಬ್ಸಿಡಿ", "ಕಚೇರಿ"),
        "DISEASES_LIST" to listOf("what disease", "which disease", "list disease", "can you detect", "supported", "classes", "types of disease", "ಯಾವ ರೋಗ", "ರೋಗಗಳ ಪಟ್ಟಿ", "ಪತ್ತೆಹಚ್ಚುವ ರೋಗಗಳು"),
        "APP_GUIDE" to listOf("help", "how to use", "features", "photo tips", "camera guide", "blur image", "clear photo", "scan leaf", "export pdf", "how app works", "ಸಹಾಯ", "ಆ್ಯಪ್ ಬಳಕೆ", "ಫೋಟೋ ಸಲಹೆ"),
        "ANTHRACNOSE" to listOf("anthracnose", "antracnos", "antracose", "colletotrichum", "shot hole", "ಆಂಥ್ರಾಕ್ನೋಸ್", "ಆಂಥ್ರ್ಯಾಕ್ನೋಸ್"),
        "POWDERY_MILDEW" to listOf("powdery mildew", "mildew", "mildw", "oidium", "white powder", "sulfur dust", "ಬೂದಿ ರೋಗ", "ಬಿಳಿ ಬೂದಿ"),
        "LEAF_BLIGHT" to listOf("leaf blight", "blight", "blite", "fusicladium", "ಕರಕಲು", "ಎಲೆ ಕರಕಲು"),
        "LEAF_SPOT" to listOf("leaf spot", "corynespora", "railway track", "ಎಲೆ ಚುಕ್ಕೆ"),
        "ABNORMAL_FALL" to listOf("abnormal", "phytophthora", "abnormal leaf fall", "leaf fall", "rot", "ಅಸಹಜ", "ಕೊಳೆರೋಗ"),
        "BLACK_SPOT" to listOf("black spot", "bird's eye", "birds eye", "helminthosporium", "ಕಪ್ಪು ಚುಕ್ಕೆ", "ಹಕ್ಕಿ ಕಣ್ಣು"),
        "DRY_LEAF" to listOf("dry leaf", "sunburn", "water deficit", "parchment", "scorch", "ಒಣಗಿದ ಎಲೆ", "ಬಿಸಿಲು ರೋಗ"),
        "HEALTHY_LEAF" to listOf("healthy", "vigorous", "normal leaf", "ಆರೋಗ್ಯಕರ", "ಉತ್ತಮ ಎಲೆ")
    )

    private val GENERIC_DOMAIN_WORDS = setOf(
        "leaf", "leaves", "rubber", "tree", "plant", "crop", "disease",
        "rubber tree", "rubber leaf", "leaf disease", "plant disease",
        "help", "guide", "info",
        "ಎಲೆ", "ರಬ್ಬರ್", "ಮರ", "ಗಿಡ", "ರೋಗ", "ರಬ್ಬರ್ ಮರ", "ರಬ್ಬರ್ ಎಲೆ"
    )

    private fun isGenericQuery(query: String): Boolean {
        val q = query.lowercase(Locale.getDefault()).trim()
        return GENERIC_DOMAIN_WORDS.contains(q)
    }

    fun getResponse(
        userMessage: String,
        lastScanDisease: String?,
        lastScanSeverity: String?,
        language: String
    ): String {
        val raw = getResponseInternal(userMessage, lastScanDisease, lastScanSeverity, language)
        return cleanFormatting(raw)
    }

    private fun cleanFormatting(text: String): String {
        return text.replace(Regex("\\*\\*(.+?)\\*\\*"), "$1")
            .replace(Regex("\\*(.+?)\\*"), "$1")
            .replace("*", "")
    }

    private fun getResponseInternal(
        userMessage: String,
        lastScanDisease: String?,
        lastScanSeverity: String?,
        language: String
    ): String {
        val isKannada = language.equals("kn", ignoreCase = true)
        val query = userMessage.trim()
        val cleanQuery = query.lowercase(Locale.getDefault()).replace(Regex("[^\\p{L}\\p{Nd}\\s]"), "").trim()

        // 0. Intercept generic single domain words
        if (isGenericQuery(cleanQuery)) {
            return if (isKannada) {
                "🌱 **ರಬ್ಬರ್ ಎಲೆ ಸಹಾಯಕ:**\n\n" +
                        "ರಬ್ಬರ್ ಎಲೆಯ ಬಗ್ಗೆ ನೀವು ಏನು ತಿಳಿಯಲು ಬಯಸುತ್ತೀರಿ?\n" +
                        "• **ಸ್ಕ್ಯಾನ್ ಮಾಡಿ:** ರೋಗ ಪತ್ತೆ ಮತ್ತು ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ಹೀಟ್‌ಮ್ಯಾಪ್ ತಪಾಸಣೆಗಾಗಿ **Scan** ಟ್ಯಾಬ್‌ನಲ್ಲಿ ಫೋಟೋ ತೆಗೆಯಿರಿ.\n" +
                        "• **ಸಾಮಾನ್ಯ ರೋಗಗಳು:** *ಬೂದಿ ರೋಗ, ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ, ಎಲೆ ಚುಕ್ಕೆ, ಆಂಥ್ರಾಕ್ನೋಸ್, ಅಥವಾ ಎಲೆ ಕರಕಲು* ಬಗ್ಗೆ ವಿವರ ಕೇಳಿ.\n" +
                        "• **ಚಳಿಗಾಲದ ಎಲೆ ಉದುರುವಿಕೆ:** *ವಿಂಟರಿಂಗ್ (Wintering)* ಬಗ್ಗೆ ಕೇಳಿ.\n" +
                        "• **ಪೋಷಕಾಂಶಗಳು:** *ರಸಗೊಬ್ಬರ (NPK/ಮೆಗ್ನೀಸಿಯಮ್) ಕೊರತೆ* ಬಗ್ಗೆ ಕೇಳಿ."
            } else {
                "🌱 **Rubber Leaf Assistant:**\n\n" +
                        "What would you like to know about rubber leaves?\n" +
                        "• **Scan & Identify:** Go to the **Scan** tab to capture a leaf photo for instant AI diagnosis and Grad-CAM visual heatmaps.\n" +
                        "• **Common Leaf Diseases:** Ask about *Powdery Mildew, Abnormal Leaf Fall, Leaf Spot (Corynespora), Anthracnose, or Leaf Blight*.\n" +
                        "• **Seasonal Shedding:** Ask about *Wintering (annual natural leaf drop)*.\n" +
                        "• **Nutrition:** Ask about *fertilizer (NPK/Magnesium) deficiency symptoms*."
            }
        }

        // 1. Find best matching topic via fuzzy NLP scoring
        var bestTopic: String? = null
        var bestScore = 0.0f
        for ((topic, aliases) in TOPIC_ALIASES) {
            val score = matchScore(query, aliases)
            if (score > bestScore) {
                bestScore = score
                bestTopic = topic
            }
        }

        // If the query didn't score high on domain topics, check if it's asking general treatment/cause/symptoms about the scanned disease
        if (bestScore < 8.0f && lastScanDisease != null) {
            val qLower = query.lowercase(Locale.getDefault())
            val isTreatment = qLower.contains("treat") || qLower.contains("cure") || qLower.contains("spray") || qLower.contains("medicine") || qLower.contains("ಚಿಕಿತ್ಸೆ") || qLower.contains("ಔಷಧ")
            val isSymptom = qLower.contains("symptom") || qLower.contains("cause") || qLower.contains("why") || qLower.contains("ಲಕ್ಷಣ") || qLower.contains("ಕಾರಣ")
            val isFertilizer = qLower.contains("fertilizer") || qLower.contains("npk") || qLower.contains("feed") || qLower.contains("ಗೊಬ್ಬರ")

            if (isTreatment || isSymptom || isFertilizer) {
                val rec = RecommendationSystem.getRecommendation(lastScanDisease, language)
                return if (isKannada) {
                    "**ಇತ್ತೀಚಿನ ಸ್ಕ್ಯಾನ್ (${lastScanDisease}):**\n\n" +
                            "🍀 **ಚಿಕಿತ್ಸೆ:** ${rec.chemicalTreatment}\n\n" +
                            "🌾 **ಗೊಬ್ಬರ:** ${rec.recommendedFertilizer}\n\n" +
                            "⏱️ **ಚೇತರಿಕೆ:** ${rec.recoveryTime}"
                } else {
                    "**Latest Scan Advice (${lastScanDisease}):**\n\n" +
                            "🍀 **Treatment:** ${rec.chemicalTreatment}\n\n" +
                            "🌾 **Fertilizer:** ${rec.recommendedFertilizer}\n\n" +
                            "⏱️ **Recovery:** ${rec.recoveryTime}"
                }
            }
        }

        // 2. Deliver comprehensive domain responses
        if (bestScore >= 8.0f && bestTopic != null) {
            return when (bestTopic) {
                "GREETING" -> if (isKannada) {
                    "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ರಬ್ಬರ್ ಗಾರ್ಡ್ ಕೃಷಿ ಚಾಟ್‌ಬಾಟ್. ರಬ್ಬರ್ ಮರದ ರೋಗಗಳು, ಬೋರ್ಡೋ ಮಿಶ್ರಣ, ಟ್ಯಾಪಿಂಗ್, ಗೊಬ್ಬರ, ಕ್ಲೋನ್, ಅಥವಾ ಮಣ್ಣಿನ ನಿರ್ವಹಣೆಯ ಬಗ್ಗೆ ಏನು ಬೇಕಾದರೂ ಕೇಳಿ."
                } else {
                    "Hello! I am your RubberGuard Agricultural Assistant. Ask me anything about rubber tree diseases, 1% Bordeaux mixture, tapping guidelines, NPK fertilizer schedules, clones, spacing, or soil care."
                }

                "BORDEAUX" -> if (isKannada) {
                    "**1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ (Bordeaux Mixture) ತಯಾರಿಸುವ ವಿಧಾನ:**\n\n" +
                            "• **ಸಾಮಗ್ರಿಗಳು:** 1 ಕೆಜಿ ತಾಮ್ರದ ಸಲ್ಫೇಟ್ (ಮೈಲುತುತ್ತು) + 1 ಕೆಜಿ ಸುಣ್ಣ (Quicklime) + 100 ಲೀಟರ್ ನೀರು.\n" +
                            "• **ತಯಾರಿಕೆ:** 1 ಕೆಜಿ ಮೈಲುತುತ್ತನ್ನು 50 ಲೀಟರ್ ನೀರಿನಲ್ಲಿ ಪ್ಲಾಸ್ಟಿಕ್ ಪಾತ್ರೆಯಲ್ಲಿ ಕರಗಿಸಿ. ಇನ್ನೊಂದು ಪಾತ್ರೆಯಲ್ಲಿ 1 ಕೆಜಿ ಸುಣ್ಣವನ್ನು 50 ಲೀಟರ್ ನೀರಿನಲ್ಲಿ ಕರಗಿಸಿ. ನಂತರ ಮೈಲುತುತ್ತಿನ ದ್ರಾವಣವನ್ನು ಸುಣ್ಣದ ದ್ರಾವಣಕ್ಕೆ ನಿಧಾನವಾಗಿ ಸುರಿದು ಕಲಕಿ.\n" +
                            "• **ಚಾಕು ಪರೀಕ್ಷೆ (Knife Test):** ಕ್ಲೀನ್ ಕಬ್ಬಿಣದ ಚಾಕುವನ್ನು 1 ನಿಮಿಷ ಅದ್ದಿ ತೆಗೆಯಿರಿ. ತಾಮ್ರದ ಕಂದು ಬಣ್ಣದ ಲೇಪನ ಬರಬಾರದು.\n" +
                            "• **ಬಳಕೆ:** ಮಳೆಗಾಲದ ಆರಂಭಕ್ಕೆ ಮುನ್ನ (ಮೇ ತಿಂಗಳಲ್ಲಿ) ಸಿಂಪಡಿಸಿದರೆ ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ ಮತ್ತು ಕೊಳೆ ರೋಗವನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ತಡೆಗಟ್ಟಬಹುದು."
                } else {
                    "**Preparation of 1% Bordeaux Mixture (Standard Rubber Prophylactic):**\n\n" +
                            "• **Ingredients:** 1 kg Copper Sulphate (Bluestone) + 1 kg Quicklime + 100 Litres of Water.\n" +
                            "• **Procedure:** Dissolve 1 kg Copper Sulphate in 50 L water in a plastic or wooden vessel. Slake 1 kg quicklime in another vessel and dilute with 50 L water. Slowly pour the copper sulphate solution into the lime suspension while stirring continuously.\n" +
                            "• **Knife Test:** Dip a polished iron knife blade for 1 minute; if it forms a reddish copper deposit, add more lime suspension until neutral.\n" +
                            "• **Timing:** Spray thoroughly over the foliage before monsoon (May) to prevent Abnormal Leaf Fall (*Phytophthora*)."
                }

                "TAPPING" -> if (isKannada) {
                    "**ರಬ್ಬರ್ ಟ್ಯಾಪಿಂಗ್ (Latex Harvesting) ಮಾರ್ಗಸೂಚಿಗಳು:**\n\n" +
                            "• **ಪ್ರಾರಂಭದ ಅಳತೆ:** ಮರದ ಕಾಂಡದ ಸುತ್ತಳತೆ 125 ಸೆಂ.ಮೀ ಎತ್ತರದಲ್ಲಿ ಕನಿಷ್ಠ 50 ಸೆಂ.ಮೀ ಇರಬೇಕು.\n" +
                            "• **ಸಮಯ:** ಮುಂಜಾನೆ 6:00 ರಿಂದ 8:00 ಗಂಟೆಯೊಳಗೆ ಟ್ಯಾಪಿಂಗ್ ಮಾಡುವುದು ಅತ್ಯುತ್ತಮ (ಹೆಚ್ಚಿನ ಹಾಲು ಮತ್ತು ಇಳುವರಿ).\n" +
                            "• **ಕೋನ ಮತ್ತು ಇಳಿಜಾರು:** ಎಡದಿಂದ ಬಲಕ್ಕೆ 30° ಇಳಿಜಾರಿನಲ್ಲಿ ಕತ್ತರಿಸಿ.\n" +
                            "• **ಆಳ:** ಮರದ ಕ್ಯಾಂಬಿಯಂ ಪದರದಿಂದ 1.0 ರಿಂದ 1.5 ಮಿ.ಮೀ ಅಂತರದಲ್ಲಿರಬೇಕು (ಕಾಂಡಕ್ಕೆ ಗಾಯವಾಗಬಾರದು).\n" +
                            "• **ವಿಧಾನ:** d/2 (ದಿನ ಬಿಟ್ಟು ದಿನ) ಅಥವಾ d/3 (ಮೂರು ದಿನಕ್ಕೊಮ್ಮೆ).\n" +
                            "• **ಇಳುವರಿ ಪ್ರಚೋದಕ:** ಎಥ್ರೆಲ್ (2.5% Ethrel) ಅನ್ನು ವರ್ಷಕ್ಕೆ 3-4 ಬಾರಿ ಕತ್ತರಿಸಿದ ಜಾಗಕ್ಕೆ ಸವರಬಹುದು."
                } else {
                    "**Rubber Tapping & Latex Harvesting Best Practices:**\n\n" +
                            "• **Opening Standards:** Trees are ready when girth reaches 50 cm at 125 cm height from bud union.\n" +
                            "• **Timing:** Early morning (6:00 AM – 8:00 AM) when latex turgor pressure is peak for highest yield.\n" +
                            "• **Slope & Angle:** 30° slope from high-left to low-right.\n" +
                            "• **Depth:** 1.0 to 1.5 mm distance from the cambium layer. Never gouge the underlying wood.\n" +
                            "• **Frequency:** Alternate daily (d/2) or third-daily (d/3) tapping systems.\n" +
                            "• **Yield Stimulant:** Apply 2.5% Ethrel brush formulation on the tapping cut 3–4 times annually to stimulate flow in mature trees."
                }

                "FERTILIZER" -> if (isKannada) {
                    "**ರಬ್ಬರ್ ಮರಗಳಿಗೆ ಶಿಫಾರಸು ಮಾಡಿದ ರಸಗೊಬ್ಬರ ವೇಳಾಪಟ್ಟಿ:**\n\n" +
                            "• **1ನೇ ವರ್ಷ (ಸಸಿಗಳು):** 10:10:4:1.5 NPKMg ಮಿಶ್ರಣವನ್ನು ಗಿಡಕ್ಕೆ 100 ಗ್ರಾಂ ನೀಡಿ.\n" +
                            "• **2 ರಿಂದ 4ನೇ ವರ್ಷ (ಬೆಳೆಯುವ ಮರಗಳು):** 10:10:4:1.5 NPKMg ಮಿಶ್ರಣವನ್ನು ವರ್ಷಕ್ಕೆ 400 ಗ್ರಾಂ ನೀಡಿ (ಮೇ ಮತ್ತು ಸೆಪ್ಟೆಂಬರ್ ತಿಂಗಳಲ್ಲಿ).\n" +
                            "• **ಟ್ಯಾಪಿಂಗ್ ಮರಗಳು (ಇಳುವರಿ ಹಂತ):** ಪ್ರತಿ ಮರಕ್ಕೆ 400-500 ಗ್ರಾಂ 10:10:10 ಅಥವಾ 12:12:12 NPK ಸಮತೋಲಿತ ಮಿಶ್ರಣವನ್ನು ಮೇ ಮತ್ತು ಸೆಪ್ಟೆಂಬರ್‌ನಲ್ಲಿ ಎರಡು ಕಂತುಗಳಲ್ಲಿ ನೀಡಿ.\n" +
                            "• **ಮೆಗ್ನೀಸಿಯಮ್ ಕೊರತೆ:** ಎಲೆಗಳ ನರಗಳ ನಡುವೆ ಹಳದಿ ಬಣ್ಣ ಕಂಡುಬಂದರೆ 1% ಮೆಗ್ನೀಸಿಯಮ್ ಸಲ್ಫೇಟ್ ಸಿಂಪಡಿಸಿ."
                } else {
                    "**Standard NPK Fertilizer Schedule for Rubber Plantations:**\n\n" +
                            "• **Year 1 (Saplings):** Apply 10:10:4:1.5 NPKMg mixture @ 100–120 g per plant.\n" +
                            "• **Years 2–4 (Immature Trees):** Apply 10:10:4:1.5 NPKMg mixture @ 400 g per tree in two split doses (May–June & Sept–Oct).\n" +
                            "• **Mature Tapping Trees:** Apply 400–500 g per tree of 10:10:10 or 12:12:12 NPK grade in split applications (pre-monsoon and post-monsoon).\n" +
                            "• **Potassium Importance:** Additional MOP builds thick leaf cuticles against fungal defoliation."
                }

                "SPACING" -> if (isKannada) {
                    "**ರಬ್ಬರ್ ನಾಟಿ ಮತ್ತು ಅಂತರದ ವಿವರಗಳು (Spacing & Planting):**\n\n" +
                            "• **ಸಮತಟ್ಟಾದ ಜಮೀನು:** 4.9 ಮೀ × 4.9 ಮೀ ಚೌಕ ಪದ್ಧತಿ (ಪ್ರತಿ ಎಕರೆಗೆ ಸುಮಾರು 180–200 ಮರಗಳು).\n" +
                            "• **ಗುಡ್ಡಗಾಡು / ಇಳಿಜಾರು ಜಮೀನು:** 6.7 ಮೀ × 3.4 ಮೀ ಕಾಂಟೂರ್ ಪದ್ಧತಿ (ಪ್ರತಿ ಎಕರೆಗೆ ಸುಮಾರು 180 ಮರಗಳು).\n" +
                            "• **ಗುಂಡಿಯ ಅಳತೆ:** 75 ಸೆಂ.ಮೀ × 75 ಸೆಂ.ಮೀ × 75 ಸೆಂ.ಮೀ.\n" +
                            "• **ಗುಂಡಿ ತುಂಬುವುದು:** ಮೇಲ್ಮಣ್ಣು + 12 ಕೆಜಿ ಕಳಿತ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ + 200 ಗ್ರಾಂ ರಾಕ್ ಫಾಸ್ಫೇಟ್.\n" +
                            "• **ಉತ್ತಮ ಕಾಲ:** ನೈಋತ್ಯ ಮಾನ್ಸೂನ್ ಪ್ರಾರಂಭವಾಗುವ ಮೇ–ಜುಲೈ ತಿಂಗಳು."
                } else {
                    "**Planting Spacing & Pit Preparation:**\n\n" +
                            "• **Flat / Level Land:** 4.9 m × 4.9 m square system (approx. 200 trees/acre or 500 trees/ha).\n" +
                            "• **Hilly / Contour Slopes:** 6.7 m × 3.4 m contour planting.\n" +
                            "• **Pit Dimensions:** 75 cm × 75 cm × 75 cm.\n" +
                            "• **Pit Filling:** Topsoil mixed with 10–12 kg well-rotted farmyard manure and 200 g rock phosphate.\n" +
                            "• **Planting Window:** May to July with the onset of the South-West monsoon for optimal root establishment."
                }

                "CLONES" -> if (isKannada) {
                    "**ಕರ್ನಾಟಕ ಮತ್ತು ಕೇರಳಕ್ಕೆ ಶಿಫಾರಸು ಮಾಡಿದ ರಬ್ಬರ್ ತಳಿಗಳು (Clones):**\n\n" +
                            "• **RRII 105:** ಅತ್ಯಂತ ಜನಪ್ರಿಯ ಹಾಗೂ ಗರಿಷ್ಠ ಇಳುವರಿ ನೀಡುವ ತಳಿ (ಕರ್ನಾಟಕದ ಕರಾವಳಿ ಮತ್ತು ಮಲೆನಾಡಿಗೆ ಸೂಕ್ತ).\n" +
                            "• **RRII 414 / RRII 430:** ಗಾಳಿಗೆ ಮುರಿಯದ ಗಟ್ಟಿ ಮರ ಮತ್ತು ಶಿಲೀಂಧ್ರ ರೋಗಗಳಿಗೆ ಉತ್ತಮ ನಿರೋಧಕತೆ ಹೊಂದಿರುವ ಆಧುನಿಕ ತಳಿಗಳು.\n" +
                            "• **PB 260:** ಬೇಗನೆ ಟ್ಯಾಪಿಂಗ್ ಹಂತಕ್ಕೆ ಬರುವ ತಳಿ, ಆದರೆ ಬಿರುಗಾಳಿಗೆ ಕೊಂಚ ಸಂವೇದನಶೀಲ.\n" +
                            "• **RRIM 600:** ಉತ್ತಮ ಬೆಳವಣಿಗೆ ಮತ್ತು ಇಳುವರಿ ಹೊಂದಿರುವ ತಳಿ."
                } else {
                    "**Recommended High-Yielding Rubber Clones for South India:**\n\n" +
                            "• **RRII 105:** The benchmark high-yield clone in Karnataka and Kerala; produces peak latex yield under good management.\n" +
                            "• **RRII 414 & RRII 430:** Modern fast-growing clones featuring strong wind resistance and superior tolerance to Corynespora and Powdery Mildew.\n" +
                            "• **PB 260:** Early maturing with high initial yields; requires wind-protected valley planting.\n" +
                            "• **RRIM 600:** Hardy clone with consistent latex yield across various soil conditions."
                }

                "SOIL_CLIMATE" -> if (isKannada) {
                    "**ರಬ್ಬರ್ ಕೃಷಿಗೆ ಸೂಕ್ತ ಮಣ್ಣು ಮತ್ತು ಹವಾಮಾನ:**\n\n" +
                            "• **ಮಣ್ಣು:** ಕನಿಷ್ಠ 1 ಮೀಟರ್ ಆಳವಿರುವ ಉತ್ತಮ ಬಸಿದುಹೋಗುವ ಜಂಬಿಟ್ಟಿಗೆ (Laterite) ಅಥವಾ ಕೆಂಪು ಗೋಡು ಮಣ್ಣು.\n" +
                            "• **ಮಣ್ಣಿನ ಪಿಎಚ್ (pH):** 4.5 ರಿಂದ 6.0 (ಸ್ವಲ್ಪ ಆಮ್ಲೀಯ ಮಣ್ಣು ರಬ್ಬರ್‌ಗೆ ಅತ್ಯುತ್ತಮ).\n" +
                            "• **ಮಳೆ ಪ್ರಮಾಣ:** ವಾರ್ಷಿಕ 2000 ರಿಂದ 3000 ಮಿ.ಮೀ ಮಳೆ ಸಮನಾಗಿ ಹಂಚಿಕೆಯಾಗಿರಬೇಕು.\n" +
                            "• **ಉಷ್ಣಾಂಶ:** 20°C ನಿಂದ 34°C ಹಾಗೂ ಹೆಚ್ಚಿನ ಆರ್ದ್ರತೆ (80% ಗಿಂತ ಹೆಚ್ಚು).\n" +
                            "• **ಸಮುದ್ರ ಮಟ್ಟ:** 500 ಮೀಟರ್ ಒಳಗಿನ ಪ್ರದೇಶಗಳು ಅತ್ಯಂತ ಪ್ರಶಸ್ತ."
                } else {
                    "**Soil, Climate & Environmental Requirements:**\n\n" +
                            "• **Soil Type:** Deep, well-drained acidic laterite or red loam (minimum effective depth $\\ge 1.0$ meter).\n" +
                            "• **Soil pH:** 4.5 to 6.0 is optimal for rubber root uptake.\n" +
                            "• **Rainfall:** 2,000 to 3,000 mm annually distributed over 100+ rainy days.\n" +
                            "• **Temperature:** 20°C to 34°C with relative humidity $>80\\%$.\n" +
                            "• **Elevation:** Below 500 meters above sea level for best vegetative growth and latex production."
                }

                "IRRIGATION" -> if (isKannada) {
                    "**ಬೇಸಿಗೆ ನಿರ್ವಹಣೆ ಮತ್ತು ನೀರಾವರಿ (Drought Management):**\n\n" +
                            "• **ಮರದ ಬುಡಕ್ಕೆ ಹೊದಿಕೆ (Mulching):** ಬೇಸಿಗೆಯಲ್ಲಿ ಮರದ ಬುಡದ 1 ಮೀಟರ್ ಸುತ್ತಳತೆಯಲ್ಲಿ ಒಣ ಎಲೆಗಳು ಅಥವಾ ತೆಂಗಿನ ತ್ಯಾಜ್ಯದಿಂದ ಹೊದಿಕೆ ಹಾಕಿ ತೇವಾಂಶ ಕಾಪಾಡಿ.\n" +
                            "• **ಸಸಿಗಳಿಗೆ ನೀರುಣಿಸುವುದು:** ಸಣ್ಣ ಸಸಿಗಳಿಗೆ ಬೇಸಿಗೆಯಲ್ಲಿ ವಾರಕ್ಕೆ ಒಮ್ಮೆ 10 ಲೀಟರ್ ನೀರು ನೀಡುವುದು ಉತ್ತಮ.\n" +
                            "• **ಬಿಸಿಲಿನ ರಕ್ಷಣೆ:** ಸಣ್ಣ ಗಿಡಗಳ ಕಾಂಡಕ್ಕೆ ಸುಣ್ಣ (Lime wash) ಹಚ್ಚಿ ಬಿಸಿಲ ಬೇಗೆಯಿಂದ ಬಿರುಕು ಬಿಡುವುದನ್ನು ತಪ್ಪಿಸಿ."
                } else {
                    "**Water Stress, Drought & Irrigation Management:**\n\n" +
                            "• **Basin Mulching:** Mulch tree basins up to 1-meter radius with dry leaves or coir pith before summer to conserve soil moisture.\n" +
                            "• **Sapling Watering:** Young plants benefit from 10 L water weekly during severe summer dry spells.\n" +
                            "• **Sun Scorch Protection:** Whitewash the trunks of young trees with dilute lime suspension to prevent sun cracking.\n" +
                            "• **Water Stress Relief:** Foliar spray of 1% Potassium Chloride (KCl) helps foliage maintain water turgidity."
                }

                "RAIN_GUARD" -> if (isKannada) {
                    "**ಮಳೆ ರಕ್ಷಣೆ (Rain Guarding) ಮತ್ತು ಪ್ಯಾನಲ್ ನಿರ್ವಹಣೆ:**\n\n" +
                            "• **ರೇನ್ ಗಾರ್ಡ್ ಹಾಕುವುದು:** ಮಾನ್ಸೂನ್ ಮಳೆ ಆರಂಭವಾಗುವ ಮುನ್ನ (ಮೇ ತಿಂಗಳಲ್ಲಿ) ಟ್ಯಾಪಿಂಗ್ ಕಟ್‌ಗಿಂತ 8 ಸೆಂ.ಮೀ ಎತ್ತರದಲ್ಲಿ ಪಾಲಿಥಿನ್ ಶೀಟ್ ಅನ್ನು ರಬ್ಬರ್ ಬ್ಯಾಂಡಿಂಗ್ ಪೇಸ್ಟ್ ಬಳಸಿ ಅಂಟಿಸಿ.\n" +
                            "• **ಲಾಭ:** ಮಳೆಗಾಲದಲ್ಲೂ ಹಾಲಿನ ನಷ್ಟವಿಲ್ಲದೆ ನಿರಂತರವಾಗಿ ಟ್ಯಾಪಿಂಗ್ ಮಾಡಬಹುದು.\n" +
                            "• **ಪ್ಯಾನಲ್ ಕೊಳೆತ ತಡೆ:** ಮಳೆಗಾಲದಲ್ಲಿ ಟ್ಯಾಪಿಂಗ್ ಪ್ಯಾನಲ್‌ಗೆ 0.2% ಮ್ಯಾಂಕೋಜೆಬ್ ಅಥವಾ ಕಾಪರ್ ಪೇಸ್ಟ್ ಹಚ್ಚಿ ರಕ್ಷಿಸಿ."
                } else {
                    "**Rain Guarding & Monsoon Panel Protection:**\n\n" +
                            "• **Application:** Fix polythene aprons around the tree trunk 8 cm above the tapping cut using tree-banding compound before monsoon rains start.\n" +
                            "• **Benefits:** Prevents latex wash-out, allowing 30–40 additional tapping days during monsoon months.\n" +
                            "• **Bark Rot Prevention:** Apply Copper Oxychloride (0.2%) or Mancozeb paste weekly to the tapping cut to prevent Black Stripe (*Phytophthora meadii*) bark decay."
                }

                "WINTERING" -> if (isKannada) {
                    "**ಚಳಿಗಾಲದ ಎಲೆ ಉದುರುವಿಕೆ (Wintering Phenomenon):**\n\n" +
                            "• **ನೈಸರ್ಗಿಕ ಪ್ರಕ್ರಿಯೆ:** ಡಿಸೆಂಬರ್‌ನಿಂದ ಫೆಬ್ರವರಿ ತಿಂಗಳಲ್ಲಿ ರಬ್ಬರ್ ಎಲೆಗಳು ಹಳದಿ ಮತ್ತು ಕಂದು ಬಣ್ಣಕ್ಕೆ ತಿರುಗಿ ಉದುರುವುದು ನೈಸರ್ಗಿಕ ಲಕ್ಷಣ (ವಿಂಟರಿಂಗ್).\n" +
                            "• **ಹೊಸ ಚಿಗುರು:** ಫೆಬ್ರವರಿ-ಮಾರ್ಚ್‌ನಲ್ಲಿ ಬರುವ ಹೊಸ ಎಲೆಗಳಿಗೆ ಬೂದಿ ರೋಗ (Powdery Mildew) ತಗುಲುವ ಸಾಧ್ಯತೆ ಹೆಚ್ಚು.\n" +
                            "• **ಮುನ್ನೆಚ್ಚರಿಕೆ:** ಹೊಸ ಚಿಗುರು ಬಂದ ತಕ್ಷಣ ಗಂಧಕದ ಪುಡಿ (Sulphur dust) ಧೂಳೀಕರಣ ಮಾಡಿ."
                } else {
                    "**Wintering (Annual Defoliation & Refoliation):**\n\n" +
                            "• **Natural Physiological Cycle:** Rubber trees naturally drop their leaves from December to February. Leaves turn yellow or copper-red before shedding.\n" +
                            "• **Refoliation Season:** Tender new copper-green foliage emerges in February–March.\n" +
                            "• **Critical Advisory:** Young tender flush is highly vulnerable to **Powdery Mildew** (*Oidium heveae*). Dust fine elemental sulphur (12–15 kg/ha) early in the morning during refoliation."
                }

                "PINK_DISEASE" -> if (isKannada) {
                    "**ಪಿಂಕ್ ರೋಗ (Pink Disease) ಮತ್ತು ಬ್ರೌನ್ ಬಾಸ್ಟ್ (TPD):**\n\n" +
                            "• **ಪಿಂಕ್ ರೋಗ ಲಕ್ಷಣ:** ಮರದ ಕವಲುಗಳಲ್ಲಿ ಬಿಳಿ ಅಥವಾ ಗುಲಾಬಿ ಬಣ್ಣದ ಶಿಲೀಂಧ್ರ ಜಾಲ ಮತ್ತು ತೊಗಟೆ ಸೀಳುವುದು.\n" +
                            "• **ಪಿಂಕ್ ರೋಗ ಚಿಕಿತ್ಸೆ:** ಸೋಂಕಿತ ಜಾಗವನ್ನು ಕೆರೆದು ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಅಥವಾ ಥೈರಮ್ (0.5%) ಹಚ್ಚಿ.\n" +
                            "• **ಬ್ರೌನ್ ಬಾಸ್ಟ್ (ಹಾಲು ಬಾರದಿರುವುದು):** ಅತಿಯಾಗಿ ಟ್ಯಾಪಿಂಗ್ ಮಾಡುವುದರಿಂದ ಉಂಟಾಗುತ್ತದೆ; ಮರಕ್ಕೆ 3-6 ತಿಂಗಳು ವಿಶ್ರಾಂತಿ ನೀಡಿ ಟ್ಯಾಪಿಂಗ್ ನಿಲ್ಲಿಸಿ."
                } else {
                    "**Pink Disease (*Corticium*) & Tapping Panel Dryness (TPD):**\n\n" +
                            "• **Pink Disease:** Attacks tree fork crotches, showing white/pink cobweb fungus followed by bark splitting and latex bleeding. Scrape the lesion and apply Bordeaux Paste (1 kg copper sulphate + 2 kg lime in 10 L water).\n" +
                            "• **Tapping Panel Dryness (Brown Bast):** Total cessation of latex flow caused by over-tapping or excessive stimulant use. Rest the tree for 3–6 months, reduce tapping intensity to d/3, and cease Ethrel usage."
                }

                "COVER_CROPS" -> if (isKannada) {
                    "**ಹೊದಿಕೆ ಬೆಳೆಗಳು ಮತ್ತು ಕಳೆ ನಿಯಂತ್ರಣ (Cover Crops & Weeding):**\n\n" +
                            "• **ಉತ್ತಮ ಹೊದಿಕೆ ಬೆಳೆ:** *ಮುಕುನಾ ಬ್ರ್ಯಾಕ್ಟಿಯೇಟಾ (Mucuna bracteata)* - ಇದು ಕಳೆಗಳನ್ನು ಹತ್ತಿಕ್ಕುತ್ತದೆ, ಮಣ್ಣಿಗೆ ಸಾರಜನಕ ಒದಗಿಸುತ್ತದೆ ಮತ್ತು ತೇವಾಂಶ ಕಾಪಾಡುತ್ತದೆ.\n" +
                            "• **ರಾಸಾಯನಿಕ ಕಳೆನಾಶಕ:** ಸಾಲುಗಳ ನಡುವಿನ ಕಳೆಗಳಿಗೆ 1% ಗ್ಲೈಫೋಸೇಟ್ (Glyphosate 41% SL) ಸಿಂಪಡಿಸಿ."
                } else {
                    "**Cover Crops & Weed Control:**\n\n" +
                            "• **Recommended Cover Crop:** *Mucuna bracteata* or *Pueraria phaseoloides*. Smothers aggressive weeds, fixes over 100 kg Nitrogen/ha, and adds organic leaf mulch.\n" +
                            "• **Chemical Weeding:** Spray Glyphosate 41% SL (1 to 1.5 L/ha) for perennial grasses in inter-rows, ensuring spray does not drift onto green rubber bark."
                }

                "RUBBER_BOARD" -> if (isKannada) {
                    "**ರಬ್ಬರ್ ಬೋರ್ಡ್ ಸಂಪರ್ಕ ಮತ್ತು ಸಬ್ಸಿಡಿ ಮಾಹಿತಿ:**\n\n" +
                            "• **ಟೋಲ್-ಫ್ರೀ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್:** 1800-425-5522 (ಸೋಮವಾರದಿಂದ ಶುಕ್ರವಾರ ಬೆಳಿಗ್ಗೆ 9:30 ರಿಂದ ಸಂಜೆ 5:30).\n" +
                            "• **ಕರ್ನಾಟಕ ಪ್ರಾದೇಶಿಕ ಕಚೇರಿಗಳು:** ಮಂಗಳೂರು, ಪುತ್ತೂರು, ಬೆಳ್ತಂಗಡಿ, ಸುಳ್ಯ, ಶಿವಮೊಗ್ಗ.\n" +
                            "• **ಸಬ್ಸಿಡಿಗಳು:** ಹೊಸ ತೋಟ ನಾಟಿ ಸಹಾಯಧನ, ರೇನ್ ಗಾರ್ಡ್ ಸಬ್ಸಿಡಿ ಮತ್ತು ಯಂತ್ರೋಪಕರಣ ನೆರವು ಲಭ್ಯವಿದೆ.\n" +
                            "• **ವೆಬ್‌ಸೈಟ್:** rubberboard.gov.in"
                } else {
                    "**Rubber Board of India Advisory & Helpline:**\n\n" +
                            "• **Kisan Call Center Toll-Free:** 1800-425-5522 (Mon–Fri, 9:30 AM to 5:30 PM).\n" +
                            "• **Regional Offices (Karnataka):** Mangaluru, Puttur, Belthangady, Sullia, and Shivamogga.\n" +
                            "• **Subsidies & Schemes:** Financial replanting assistance per hectare, rain guarding subsidy, and mechanized tapper training programs.\n" +
                            "• **Official Portal:** rubberboard.gov.in"
                }

                "DISEASES_LIST" -> if (isKannada) {
                    "ನಮ್ಮ ಆ್ಯಪ್ ಈ ಕೆಳಗಿನ 8 ರೋಗ ಸ್ಥಿತಿಗಳನ್ನು ನಿಖರವಾಗಿ ಪತ್ತೆಹಚ್ಚಬಲ್ಲದು:\n" +
                            "1. **ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ** (Abnormal Leaf Fall - *Phytophthora*)\n" +
                            "2. **ಆಂಥ್ರಾಕ್ನೋಸ್** (Anthracnose - *Colletotrichum*)\n" +
                            "3. **ಕಪ್ಪು ಚುಕ್ಕೆ / ಹಕ್ಕಿ ಕಣ್ಣು** (Black Spot / Bird's Eye)\n" +
                            "4. **ಎಲೆ ಕರಕಲು ರೋಗ** (Leaf Blight - *Fusicladium*)\n" +
                            "5. **ಎಲೆ ಚುಕ್ಕೆ ರೋಗ** (Leaf Spot - *Corynespora*)\n" +
                            "6. **ಬೂದಿ ರೋಗ** (Powdery Mildew - *Oidium*)\n" +
                            "7. **ಒಣಗಿದ ಎಲೆ** (Dry Leaf / Sun Scorch)\n" +
                            "8. **ಆರೋಗ್ಯಕರ ಎಲೆ** (Healthy Leaf)"
                } else {
                    "Our AI model diagnoses the following 8 rubber leaf conditions:\n" +
                            "1. **Abnormal Leaf Fall** (*Phytophthora spp.*)\n" +
                            "2. **Anthracnose** (*Colletotrichum gloeosporioides*)\n" +
                            "3. **Black Spot / Bird's Eye** (*Helminthosporium heveae*)\n" +
                            "4. **Leaf Blight** (*Fusicladium macrosporum*)\n" +
                            "5. **Leaf Spot** (*Corynespora cassiicola*)\n" +
                            "6. **Powdery Mildew** (*Oidium heveae*)\n" +
                            "7. **Dry Leaf** (Abiotic / Drought Stress)\n" +
                            "8. **Healthy Leaf** (No fungal pathogen)"
                }

                "APP_GUIDE" -> if (isKannada) {
                    "**ರಬ್ಬರ್ ಗಾರ್ಡ್ ಆ್ಯಪ್ ಬಳಕೆ ಮತ್ತು ಫೋಟೋ ಸಲಹೆ:**\n\n" +
                            "• **ಫೋಟೋ ತೆಗೆಯುವುದು:** ಒಂದೇ ಎಲೆಯನ್ನು ಹತ್ತಿರದಿಂದ ಹಿಡಿದು ನೈಸರ್ಗಿಕ ಬೆಳಕಿನಲ್ಲಿ ಸ್ಪಷ್ಟವಾಗಿ ಫೋಟೋ ತೆಗೆಯಿರಿ.\n" +
                            "• **Grad-CAM ನಕ್ಷೆ:** ಪತ್ತೆಯಾದ ರೋಗದ ಕೆಂಪು/ಹಳದಿ ಬಣ್ಣದ ತಪಾಸಣಾ ನಕ್ಷೆಯನ್ನು ಗಮನಿಸಿ.\n" +
                            "• **ಪಿಡಿಎಫ್ ವರದಿ:** 'Export PDF' ಬಟನ್ ಒತ್ತಿ ಕೃಷಿ ಅಧಿಕಾರಿಗಳಿಗೆ ಅಥವಾ ರಬ್ಬರ್ ಬೋರ್ಡ್‌ಗೆ ವರದಿ ಶೇರ್ ಮಾಡಿ."
                } else {
                    "**How to Use RubberGuard for Best Results:**\n\n" +
                            "• **Framing:** Place a single rubber leaf centrally against a neutral background in natural daylight.\n" +
                            "• **Clarity:** Keep distance 15–25 cm to avoid motion blur.\n" +
                            "• **Grad-CAM Saliency:** Switch to the Heatmap tab to verify exactly where the AI detected lesion triggers.\n" +
                            "• **PDF Report:** Tap 'Export PDF Report' to generate an A4 summary with severity percentage and agronomic advice."
                }

                // Individual disease inquiries
                "ANTHRACNOSE", "POWDERY_MILDEW", "LEAF_BLIGHT", "LEAF_SPOT", "ABNORMAL_FALL", "BLACK_SPOT", "DRY_LEAF", "HEALTHY_LEAF" -> {
                    val diseaseName = when (bestTopic) {
                        "ANTHRACNOSE" -> "Anthracnose"
                        "POWDERY_MILDEW" -> "Powdery Mildew"
                        "LEAF_BLIGHT" -> "Leaf Blight"
                        "LEAF_SPOT" -> "Leaf Spot"
                        "ABNORMAL_FALL" -> "Abnormal Leaf Fall"
                        "BLACK_SPOT" -> "Black Spot / Bird's Eye"
                        "DRY_LEAF" -> "Dry Leaf"
                        else -> "Healthy"
                    }
                    val rec = RecommendationSystem.getRecommendation(diseaseName, language)
                    if (isKannada) {
                        "**${rec.description}**\n\n" +
                                "🔍 **ಪ್ರಮುಖ ಲಕ್ಷಣಗಳು:** ${rec.symptoms}\n\n" +
                                "🍀 **ಸಾವಯವ ಚಿಕಿತ್ಸೆ:** ${rec.organicTreatment}\n\n" +
                                "🧪 **ಶಿಲೀಂಧ್ರನಾಶಕ:** ${rec.chemicalTreatment}\n\n" +
                                "🌾 **ಗೊಬ್ಬರ:** ${rec.recommendedFertilizer}\n\n" +
                                "⏱️ **ಚೇತರಿಕೆ ಅವಧಿ:** ${rec.recoveryTime}"
                    } else {
                        "**${rec.description}**\n\n" +
                                "🔍 **Symptoms:** ${rec.symptoms}\n\n" +
                                "🍀 **Organic Control:** ${rec.organicTreatment}\n\n" +
                                "🧪 **Chemical Spray:** ${rec.chemicalTreatment}\n\n" +
                                "🌾 **Fertilizer:** ${rec.recommendedFertilizer}\n\n" +
                                "⏱️ **Expected Recovery:** ${rec.recoveryTime}"
                    }
                }

                else -> defaultFallback(isKannada)
            }
        }

        return defaultFallback(isKannada)
    }

    private fun defaultFallback(isKannada: Boolean): String {
        return if (isKannada) {
            "ನನಗೆ ಪ್ರಶ್ನೆ ಸ್ಪಷ್ಟವಾಗಲಿಲ್ಲ. ನೀವು ಈ ಕೆಳಗಿನವುಗಳ ಬಗ್ಗೆ ಕೇಳಬಹುದು:\n" +
                    "• ರೋಗಗಳ ಚಿಕಿತ್ಸೆ (ಉದಾ: 'ಆಂಥ್ರಾಕ್ನೋಸ್ ಚಿಕಿತ್ಸೆ' ಅಥವಾ 'ಬೂದಿ ರೋಗ')\n" +
                    "• 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ತಯಾರಿಸುವ ವಿಧಾನ\n" +
                    "• ರಬ್ಬರ್ ಟ್ಯಾಪಿಂಗ್ ಸಮಯ ಮತ್ತು ನಿಯಮಗಳು\n" +
                    "• ರಸಗೊಬ್ಬರ (NPK) ವೇಳಾಪಟ್ಟಿ\n" +
                    "• ನಾಟಿ ಅಂತರ ಮತ್ತು ಉತ್ತಮ ಕ್ಲೋನ್‌ಗಳು (RRII 105)\n" +
                    "• ಮಳೆ ರಕ್ಷಣೆ (ರೇನ್ ಗಾರ್ಡ್) ಮತ್ತು ಚಳಿಗಾಲದ ಎಲೆ ಉದುರುವಿಕೆ"
        } else {
            "I couldn't quite identify your question. You can ask me about:\n" +
                    "• Any leaf disease (e.g. 'How to treat Anthracnose', 'Powdery Mildew', 'Leaf Blight')\n" +
                    "• 1% Bordeaux mixture preparation steps\n" +
                    "• Rubber tapping timing, angle, depth & rain-guards\n" +
                    "• Recommended NPK fertilizer schedules\n" +
                    "• Recommended high-yielding clones (RRII 105) & tree spacing\n" +
                    "• Soil, rainfall requirements & wintering defoliation\n" +
                    "• Rubber Board helpline: 1800-425-5522"
        }
    }
}
