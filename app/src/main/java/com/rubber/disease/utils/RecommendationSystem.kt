package com.rubber.disease.utils

data class DiseaseRecommendation(
    val description: String,
    val symptoms: String,
    val causes: String,
    val organicTreatment: String,
    val chemicalTreatment: String,
    val recommendedFertilizer: String,
    val preventiveMeasures: String,
    val recoveryTime: String,
    val precautions: String
)

object RecommendationSystem {

    fun getRecommendation(diseaseName: String, language: String): DiseaseRecommendation {
        val isKannada = language.equals("kn", ignoreCase = true)
        return when (diseaseName) {
            "Abnormal Leaf Fall" -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ ರೋಗವು ಫೈಟೊಫ್ಥೊರಾ ಶಿಲೀಂಧ್ರದಿಂದ ಉಂಟಾಗುತ್ತದೆ. ಇದು ಮಳೆಗಾಲದಲ್ಲಿ ರಬ್ಬರ್ ಮರಗಳಿಗೆ ತೀವ್ರ ಹಾನಿ ಮಾಡುತ್ತದೆ.",
                    symptoms = "ಎಲೆಗಳ ತೊಟ್ಟಿನ ಮೇಲೆ ಕಪ್ಪು ಚುಕ್ಕೆಗಳು ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ ಮತ್ತು ಕಾಯಿಗಳು ಕೊಳೆತು ಉದುರುತ್ತವೆ.",
                    causes = "ಅತಿ ಹೆಚ್ಚು ಆರ್ದ್ರತೆ, ನಿರಂತರ ಮಳೆ ಮತ್ತು ಕಡಿಮೆ ತಾಪಮಾನ.",
                    organicTreatment = "ಪೀಡಿತ ಎಲೆಗಳು ಮತ್ತು ಕೊಂಬೆಗಳನ್ನು ಕತ್ತರಿಸಿ ಸುಟ್ಟು ಹಾಕುವುದು.",
                    chemicalTreatment = "ಮಳೆಗಾಲ ಪ್ರಾರಂಭವಾಗುವ ಮೊದಲು 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣವನ್ನು ಎಲೆಗಳಿಗೆ ಸಿಂಪಡಿಸಿ.",
                    recommendedFertilizer = "ಹೆಚ್ಚುವರಿ ಪೊಟ್ಯಾಸಿಯಮ್ ಗೊಬ್ಬರಗಳನ್ನು ಹಾಕಿ ಮರಗಳ ರೋಗನಿರೋಧಕ ಶಕ್ತಿಯನ್ನು ಹೆಚ್ಚಿಸಿ.",
                    preventiveMeasures = "ಮರಗಳ ನಡುವೆ ಗಾಳಿಯಾಡಲು ಅತಿಯಾದ ಕೊಂಬೆಗಳನ್ನು ಕತ್ತರಿಸಿ.",
                    recoveryTime = "30-45 ದಿನಗಳು ಸೂಕ್ತ ಕಾಳಜಿಯೊಂದಿಗೆ.",
                    precautions = "ಮಳೆಗಾಲದಲ್ಲಿ ಮರದ ಕಾಂಡಕ್ಕೆ ಶಿಲೀಂಧ್ರನಾಶಕ ಪೇಸ್ಟ್ ಹಚ್ಚಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "Abnormal Leaf Fall is caused by Phytophthora species. It is a major disease affecting rubber trees during the monsoon season in India.",
                    symptoms = "Water-soaked lesions on petioles, leaf fall while still green, and rotting of pods.",
                    causes = "Continuous heavy rainfall, high humidity, and cool temperatures.",
                    organicTreatment = "Prune and destroy infected branches; clear fallen leaves and pods around the tree base.",
                    chemicalTreatment = "Spray 1% Bordeaux mixture or copper oxychloride before the onset of the monsoon.",
                    recommendedFertilizer = "Apply balanced NPK fertilizer with additional Potassium to build tree vigor.",
                    preventiveMeasures = "Proper spacing and canopy thinning to allow light penetration and air circulation.",
                    recoveryTime = "30-45 days under proper management.",
                    precautions = "Avoid tapping during heavy rain and protect tapping panels with fungicide paste."
                )
            }

            "Anthracnose" -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ಆಂಥ್ರಾಕ್ನೋಸ್ ರೋಗವು ಕೊಲೆಟೊಟ್ರಿಕಮ್ ಶಿಲೀಂಧ್ರದಿಂದ ಉಂಟಾಗುತ್ತದೆ, ಇದು ಎಳೆಯ ಚಿಗುರುಗಳು ಮತ್ತು ಎಲೆಗಳನ್ನು ಹಾನಿಗೊಳಿಸುತ್ತದೆ.",
                    symptoms = "ಎಲೆಗಳ ಅಂಚುಗಳಲ್ಲಿ ಮತ್ತು ತುದಿಯಲ್ಲಿ ಕಂದು ಬಣ್ಣದ ವೃತ್ತಾಕಾರದ ಚುಕ್ಕೆಗಳು ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ.",
                    causes = "ಚಿಕ್ಕ ವಯಸ್ಸಿನ ಸಸ್ಯಗಳಲ್ಲಿ ಬಿಸಿಲು ಮತ್ತು ಅತಿಯಾದ ಆರ್ದ್ರತೆ.",
                    organicTreatment = "ಕಲಬೆರಕೆ ತಡೆಗಟ್ಟಲು ಬೇವಿನ ಎಣ್ಣೆ (2%) ಸಿಂಪಡಿಸಿ.",
                    chemicalTreatment = "0.2% ಮ್ಯಾಂಕೋಜೆಬ್ ಅಥವಾ ಕಾರ್ಬೆಂಡಾಜಿಮ್ ಶಿಲೀಂಧ್ರನಾಶಕವನ್ನು ಸಿಂಪಡಿಸಿ.",
                    recommendedFertilizer = "ಸಾರಜನಕ ಬಳಕೆಯನ್ನು ಕಡಿಮೆ ಮಾಡಿ, ಫಾಸ್ಫೇಟ್ ಬಳಕೆಯನ್ನು ಹೆಚ್ಚಿಸಿ.",
                    preventiveMeasures = "ನರ್ಸರಿಗಳಲ್ಲಿ ನೆರಳು ಒದಗಿಸುವುದು ಮತ್ತು ಸ್ವಚ್ಛತೆಯನ್ನು ಕಾಪಾಡುವುದು.",
                    recoveryTime = "15-20 ದಿನಗಳು.",
                    precautions = "ಸಸ್ಯಗಳಿಗೆ ಗಾಯವಾಗದಂತೆ ಎಚ್ಚರವಹಿಸಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "Anthracnose is caused by Colletotrichum gloeosporioides, which attacks tender leaves, shoots, and twigs.",
                    symptoms = "Circular brown spots on leaves, drying and dieback of young shoots, and leaf distortion.",
                    causes = "High rainfall combined with warm temp, poor soil drainage, and physical plant injuries.",
                    organicTreatment = "Apply Neem seed kernel extract (5%) or copper hydroxide sprays.",
                    chemicalTreatment = "Spray Carbendazim (0.05%) or Mancozeb (0.2%) at fortnightly intervals on young leaves.",
                    recommendedFertilizer = "Apply standard NPK mix; avoid excessive Nitrogen which promotes soft susceptible tissue.",
                    preventiveMeasures = "Construct overhead shade in nurseries and ensure good soil drainage.",
                    recoveryTime = "15-20 days.",
                    precautions = "Prune dead twigs before the new leaf flush emerges to reduce inoculum sources."
                )
            }

            "Black Spot / Bird's Eye" -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ಪಕ್ಷಿ ಕಣ್ಣಿನ ಚುಕ್ಕೆ ರೋಗವು ಹೆಲ್ಮಿಂಥೋಸ್ಪೋರಿಯಮ್ ಶಿಲೀಂಧ್ರದಿಂದ ಉಂಟಾಗುತ್ತದೆ. ಇದು ಎಲೆಗಳ ಮೇಲೆ ಸಣ್ಣ ಚುಕ್ಕೆಗಳನ್ನು ಉಂಟುಮಾಡುತ್ತದೆ.",
                    symptoms = "ಎಲೆಗಳ ಮೇಲೆ ಕಪ್ಪು ಅಂಚು ಮತ್ತು ಬಿಳಿ ಕೇಂದ್ರಭಾಗ ಹೊಂದಿರುವ ಪಕ್ಷಿ ಕಣ್ಣಿನಂತಹ ಚುಕ್ಕೆಗಳು ಕಾಣಿಸುತ್ತವೆ.",
                    causes = "ದೀರ್ಘಾವಧಿಯವರೆಗೆ ಎಲೆಗಳು ಒದ್ದೆಯಾಗಿರುವುದು ಮತ್ತು ಮಂಜು ಕವಿದ ವಾತಾವರಣ.",
                    organicTreatment = "ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ಸಂಗ್ರಹಿಸಿ ಸುಟ್ಟು ಹಾಕಿ.",
                    chemicalTreatment = "ಕ್ಲೋರೋಥಲೋನಿಲ್ ಅಥವಾ ಜಿನೆಬ್ ಶಿಲೀಂಧ್ರನಾಶಕವನ್ನು ಸಿಂಪಡಿಸಿ.",
                    recommendedFertilizer = "ಸೂಕ್ಷ್ಮ ಪೋಷಕಾಂಶಗಳಾದ ಜಿಂಕ್ ಮತ್ತು ಬೋರಾನ್ ಒದಗಿಸಿ.",
                    preventiveMeasures = "ಸಸ್ಯಗಳ ಸುತ್ತ ಕಳೆಗಳನ್ನು ನಿಯಮಿತವಾಗಿ ತೆಗೆದುಹಾಕಿ.",
                    recoveryTime = "20-30 ದಿನಗಳು.",
                    precautions = "ಸ್ಪಿನರ್ ನೀರಾವರಿ ಪದ್ಧತಿಯನ್ನು ಸಂಜೆ ಬಳಸಬೇಡಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "Bird's Eye Spot (caused by Drechslera heveae) is common in nurseries and young plantations.",
                    symptoms = "Small circular spots with a grey/white center and dark brown border resembling a bird's eye.",
                    causes = "Dew formation, prolonged leaf wetness, and high humidity in dense nurseries.",
                    organicTreatment = "Destroy affected leaves; clean weeds around nurseries to lower micro-humidity.",
                    chemicalTreatment = "Spray Zineb (0.2%) or Chlorothalonil (0.2%) periodically during new leaf flush.",
                    recommendedFertilizer = "Provide balanced NPK and ensure micronutrients (Zinc, Magnesium) are supplied.",
                    preventiveMeasures = "Increase spacing in nursery beds and avoid overhead sprinkler watering in late afternoons.",
                    recoveryTime = "20-30 days.",
                    precautions = "Monitor young grafts closely during dry spells with heavy morning dews."
                )
            }

            "Dry Leaf" -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ಒಣ ಎಲೆ ಪರಿಸ್ಥಿತಿಯು ನೀರಾವರಿ ಕೊರತೆ ಅಥವಾ ತೀವ್ರ ಸೂರ್ಯನ ತಾಪದಿಂದ ಸಂಭವಿಸುತ್ತದೆ.",
                    symptoms = "ಎಲೆಗಳ ಅಂಚು ಒಣಗುವುದು, ಹಳದಿಯಾಗುವುದು ಮತ್ತು ಅಂತಿಮವಾಗಿ ಎಲೆ ಉದುರುವುದು.",
                    causes = "ನೀರಿನ ಕೊರತೆ, ಮಣ್ಣಿನಲ್ಲಿ ಕಡಿಮೆ ತೇವಾಂಶ ಮತ್ತು ಅತಿಯಾದ ಶಾಖ.",
                    organicTreatment = "ಬುಡಕ್ಕೆ ಒಣ ಎಲೆಗಳ ಹೊದಿಕೆ (ಮಲ್ಚಿಂಗ್) ಹಾಕಿ ತೇವಾಂಶ ಕಾಪಾಡಿ.",
                    chemicalTreatment = "ಯಾವುದೇ ರಾಸಾಯನಿಕ ಶಿಲೀಂಧ್ರನಾಶಕ ಬೇಕಾಗಿಲ್ಲ. ಲಘುವಾಗಿ ನೀರುಣಿಸಿ.",
                    recommendedFertilizer = "ಸಾವಯವ ಗೊಬ್ಬರ ಮತ್ತು ಕಾಂಪೋಸ್ಟ್ ಹಾಕಿ ಮಣ್ಣಿನ ತೇವಾಂಶ ಹಿಡಿದಿಡುವ ಶಕ್ತಿ ಹೆಚ್ಚಿಸಿ.",
                    preventiveMeasures = "ಬೇಸಿಗೆಯಲ್ಲಿ ಹನಿ ನೀರಾವರಿ ವ್ಯವಸ್ಥೆ ಅಳವಡಿಸಿ.",
                    recoveryTime = "10-15 ದಿನಗಳು ಸಮರ್ಪಕ ನೀರುಣಿಸಿದ ನಂತರ.",
                    precautions = "ಮರಗಳಿಗೆ ಬಿಸಿಲು ತಾಗದಂತೆ ತಡೆಗೋಡೆಗಳನ್ನು ಬಳಸಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "Dry Leaf condition is primarily due to abiotic stress like drought or sun scorch, not a fungal infection.",
                    symptoms = "Marginal leaf drying, yellowing, crispy brown leaf margins, and premature defoliation.",
                    causes = "Inadequate watering, sandy soils with poor moisture retention, and high solar radiation.",
                    organicTreatment = "Apply organic mulch around the tree base to retain soil moisture.",
                    chemicalTreatment = "No chemical fungicides are required; spray anti-transpirants if necessary.",
                    recommendedFertilizer = "Apply well-rotted organic compost to improve soil texture and water-holding capacity.",
                    preventiveMeasures = "Ensure regular irrigation during dry dry summer months via drip systems.",
                    recoveryTime = "10-15 days after restoring moisture.",
                    precautions = "Avoid heavy fertilizer application when the soil is completely dry."
                )
            }

            "Healthy" -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ನಿಮ್ಮ ರಬ್ಬರ್ ಮರವು ಸಂಪೂರ್ಣ ಆರೋಗ್ಯಕರವಾಗಿದೆ. ಯಾವುದೇ ರೋಗದ ಲಕ್ಷಣಗಳಿಲ್ಲ.",
                    symptoms = "ಹಸಿರು, ಹೊಳೆಯುವ ಮತ್ತು ಕಲೆಗಳಿಲ್ಲದ ಎಲೆಗಳು.",
                    causes = "ಉತ್ತಮ ನಿರ್ವಹಣೆ, ಸೂಕ್ತ ಪೋಷಣೆ ಮತ್ತು ಅನುಕೂಲಕರ ವಾತಾವರಣ.",
                    organicTreatment = "ನಿಯಮಿತವಾಗಿ ಸಾವಯವ ಕಾಂಪೋಸ್ಟ್ ಹಾಕಿ.",
                    chemicalTreatment = "ಯಾವುದೇ ರಾಸಾಯನಿಕ ಸಿಂಪಡಣೆ ಅಗತ್ಯವಿಲ್ಲ.",
                    recommendedFertilizer = "ವಾರ್ಷಿಕವಾಗಿ ಶಿಫಾರಸು ಮಾಡಿದ ಎನ್.ಪಿ.ಕೆ. ಗೊಬ್ಬರವನ್ನು ಹಾಕಿ.",
                    preventiveMeasures = "ಸ್ವಚ್ಛತೆ ಮತ್ತು ನೀರಾವರಿ ಕ್ರಮಗಳನ್ನು ಮುಂದುವರಿಸಿ.",
                    recoveryTime = "ಅನ್ವಯಿಸುವುದಿಲ್ಲ (ಆರೋಗ್ಯಕರ).",
                    precautions = "ರೋಗ ತಡೆಗಟ್ಟಲು ನಿಯಮಿತವಾಗಿ ಕಣ್ಣಿಡಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "The rubber leaf is perfectly healthy with no signs of fungal or bacterial infection.",
                    symptoms = "Lush green coloration, glossy texture, and clean surface without spots.",
                    causes = "Optimal agricultural practices, balanced nutrient profile, and disease-free environment.",
                    organicTreatment = "None needed. Maintain organic compost applications.",
                    chemicalTreatment = "No chemical sprays required.",
                    recommendedFertilizer = "Apply recommended annual NPK dose to maintain tree vigor.",
                    preventiveMeasures = "Maintain regular surveillance and weeding protocols.",
                    recoveryTime = "Not applicable (Healthy).",
                    precautions = "Keep sanitary conditions in the farm to prevent future outbreaks."
                )
            }

            "Leaf Blight" -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ಎಲೆ ಮಾರಿ ರೋಗವು ಫ್ಯುಸೇರಿಯಮ್ ಅಥವಾ ಕೊಲೆಟೊಟ್ರಿಕಮ್ ಶಿಲೀಂಧ್ರಗಳಿಂದ ಉಂಟಾಗುತ್ತದೆ.",
                    symptoms = "ಎಲೆಗಳ ಮೇಲೆ ದೊಡ್ಡದಾದ, ಅನಿಯಮಿತ ಒಣ ಕಂದು ಬಣ್ಣದ ಕಲೆಗಳು ಉಂಟಾಗುತ್ತವೆ.",
                    causes = "ಅತಿ ಹೆಚ್ಚು ತೇವಾಂಶ ಮತ್ತು ಎಲೆಗಳ ಮೇಲೆ ನೀರು ನಿಲ್ಲುವುದು.",
                    organicTreatment = "ಬೇವಿನ ಕಷಾಯವನ್ನು 10 ದಿನಗಳಿಗೊಮ್ಮೆ ಸಿಂಪಡಿಸಿ.",
                    chemicalTreatment = "ಕಾರ್ಬನ್ಡಾಜಿಮ್ 0.1% ಅಥವಾ ಪ್ರೊಪಿಕೊನಜೋಲ್ ಸಿಂಪಡಿಸಿ.",
                    recommendedFertilizer = "ಪೊಟ್ಯಾಶ್ ಮತ್ತು ಸೂಪರ್ ಫಾಸ್ಫೇಟ್ ಬಳಕೆಯನ್ನು ಹೆಚ್ಚಿಸಿ.",
                    preventiveMeasures = "ನೀರು ಸರಾಗವಾಗಿ ಹರಿದು ಹೋಗಲು ಕಾಲುವೆಗಳನ್ನು ನಿರ್ಮಿಸಿ.",
                    recoveryTime = "25-30 ದಿನಗಳು.",
                    precautions = "ಸೋಂಕಿತ ಮರದ ಎಲೆಗಳನ್ನು ಮುಟ್ಟಿದ ನಂತರ ಕೈಗಳನ್ನು ತೊಳೆದುಕೊಳ್ಳಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "Leaf Blight is a fungal infection causing extensive necrotic areas on mature leaves.",
                    symptoms = "Large, irregular scorched-brown dry patches covering significant portions of the leaf blade.",
                    causes = "Persistent leaf wetness, overhead shading, and poor air circulation.",
                    organicTreatment = "Spray Pseudomonas fluorescens (0.5%) liquid formulation on foliage.",
                    chemicalTreatment = "Spray Propiconazole (0.1%) or Hexaconazole (0.1%) to arrest spread.",
                    recommendedFertilizer = "Apply balanced NPK, with attention to Potassium to improve cell wall strength.",
                    preventiveMeasures = "Prune overlapping branches to ensure sunlight reaches the lower canopy.",
                    recoveryTime = "25-30 days.",
                    precautions = "Burn infected crop residues to prevent spore dispersal by wind."
                )
            }

            "Leaf Spot" -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ಎಲೆ ಚುಕ್ಕೆ ರೋಗವು ಸರ್ಕೋಸ್ಪೋರಾ ಶಿಲೀಂಧ್ರದಿಂದ ಬರುತ್ತದೆ.",
                    symptoms = "ಎಲೆಗಳ ಮೇಲೆ ಸಣ್ಣ, ದುಂಡಗಿನ ಕಂದು ಬಣ್ಣದ ಚುಕ್ಕೆಗಳು ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ.",
                    causes = "ಉಷ್ಣ ವಾತಾವರಣ ಮತ್ತು ಮಣ್ಣಿನಲ್ಲಿ ಪೋಷಕಾಂಶಗಳ ಕೊರತೆ.",
                    organicTreatment = "ಬೇವಿನ ಬೀಜದ ಹಿಂಡಿ ದ್ರಾವಣ ಸಿಂಪಡಿಸಿ.",
                    chemicalTreatment = "ಕ್ಲೋರೋಥಲೋನಿಲ್ ಅಥವಾ ಕಾರ್ಬೆಂಡಾಜಿಮ್ ಸಿಂಪಡಿಸಿ.",
                    recommendedFertilizer = "ಸಾರಜನಕ, ರಂಜಕ ಮತ್ತು ಪೊಟ್ಯಾಶಿಯಂ ಸಮತೋಲನ ಕಾಯ್ದುಕೊಳ್ಳಿ.",
                    preventiveMeasures = "ಸಸಿ ನೆಡುವಾಗ ಶಿಫಾರಸು ಮಾಡಿದ ಅಂತರ ಪಾಲಿಸಿ.",
                    recoveryTime = "15-20 ದಿನಗಳು.",
                    precautions = "ರೋಗಪೀಡಿತ ಸಸ್ಯಗಳಿಂದ ಕಸಿ ಮಾಡಬೇಡಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "Leaf Spot is caused by Cercospora or similar opportunistic fungal pathogens.",
                    symptoms = "Numerous small, circular brown spots scattered across the leaf blade, sometimes merging.",
                    causes = "Warm temperatures, humid microclimates, and nutrient-depleted soils.",
                    organicTreatment = "Spray fresh compost tea or diluted neem oil (1-2%) to suppress fungal spores.",
                    chemicalTreatment = "Apply Carbendazim (0.1%) or Mancozeb (0.2%) at the first sign of spotting.",
                    recommendedFertilizer = "Apply balanced fertilizer rich in Magnesium and Calcium to bolster immunity.",
                    preventiveMeasures = "Avoid water logging and plant rubber clones known for disease resistance.",
                    recoveryTime = "15-20 days.",
                    precautions = "Remove weeds which act as secondary hosts for the fungus."
                )
            }

            "Powdery Mildew" -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ಬೂದಿ ರೋಗವು ಓಡಿಯಮ್ ಹೆವಿಯೇ ಶಿಲೀಂಧ್ರದಿಂದ ಉಂಟಾಗುವ ರಬ್ಬರ್‌ನ ಪ್ರಮುಖ ಎಲೆ ರೋಗವಾಗಿದೆ.",
                    symptoms = "ಎಲೆಗಳ ಕೆಳಭಾಗದಲ್ಲಿ ಬಿಳಿ ಬೂದಿಯಂತಹ ಪದರ ಮೂಡುತ್ತದೆ ಮತ್ತು ಎಲೆಗಳು ಸುರುಳಿಯಾಗುತ್ತವೆ.",
                    causes = "ಚಿಲಿಂ ಚಿಲಿಂ ಚಳಿ ಮತ್ತು ಮುಂಜಾನೆ ಮಂಜಿನೊಂದಿಗೆ ಒಣ ಹವೆ.",
                    organicTreatment = "ಹಾಲಿನ ದ್ರಾವಣ (1 ಪಾಲು ಹಾಲು, 9 ಪಾಲು ನೀರು) ಸಿಂಪಡಿಸಿ.",
                    chemicalTreatment = "ಗಂಧಕದ ಪುಡಿಯನ್ನು (ಸಲ್ಫರ್ ಡಸ್ಟ್) ಹೆಕ್ಟೇರ್‌ಗೆ 15 ಕೆಜಿಯಂತೆ ಧೂಳೀಕರಿಸಿ ಅಥವಾ ನೀರಿನಲ್ಲಿ ಕರಗುವ ಗಂಧಕ 0.2% ಸಿಂಪಡಿಸಿ.",
                    recommendedFertilizer = "ಸೂಕ್ತ ಪ್ರಮಾಣದ ಸಾರಜನಕ ಮತ್ತು ಪೊಟ್ಯಾಸಿಯಮ್ ಒದಗಿಸಿ.",
                    preventiveMeasures = "ರೋಗ ನಿರೋಧಕ ತಳಿಗಳನ್ನು ಬೆಳೆಸಿ.",
                    recoveryTime = "20-25 ದಿನಗಳು.",
                    precautions = "ಬೂದಿ ದೂಳೀಕರಣವನ್ನು ಮುಂಜಾನೆ ಗಾಳಿ ಇಲ್ಲದ ಸಮಯದಲ್ಲಿ ಮಾಡಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "Powdery Mildew is caused by Oidium heveae, primarily attacking the new leaves during refoliation.",
                    symptoms = "White powdery patches on the underside of leaves, causing young leaves to shrivel, curl, and fall.",
                    causes = "Cool nights, misty mornings, and dry warm days during February-March.",
                    organicTreatment = "Spray diluted milk formulation (1:9 ratio with water) which acts as a natural fungicide.",
                    chemicalTreatment = "Dust sulphur powder (325 mesh) at 15 kg/ha or spray wettable sulphur (0.2%).",
                    recommendedFertilizer = "Ensure adequate Potassium supply to support rapid cuticle hardening.",
                    preventiveMeasures = "Defoliation control and scheduling clonal selections that refoliate early.",
                    recoveryTime = "20-25 days.",
                    precautions = "Conduct sulphur dusting in the early morning when the wind speed is minimal to prevent drift."
                )
            }

            else -> if (isKannada) {
                DiseaseRecommendation(
                    description = "ಅಜ್ಞಾತ ರೋಗ ಲಕ್ಷಣಗಳು. ಹೆಚ್ಚಿನ ತಪಾಸಣೆಗಾಗಿ ತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
                    symptoms = "ತಿಳಿದಿಲ್ಲ.",
                    causes = "ತಿಳಿದಿಲ್ಲ.",
                    organicTreatment = "ಸಾಮಾನ್ಯ ಸ್ವಚ್ಛತೆ ಕಾಪಾಡಿ.",
                    chemicalTreatment = "ಸಾರ್ವತ್ರಿಕ ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ.",
                    recommendedFertilizer = "ಸಮತೋಲಿತ ಎನ್.ಪಿ.ಕೆ. ಬಳಸಿ.",
                    preventiveMeasures = "ಮರಗಳ ಉತ್ತಮ ನಿರ್ವಹಣೆ.",
                    recoveryTime = "ತಿಳಿದಿಲ್ಲ.",
                    precautions = "ತಜ್ಞರ ಸಲಹೆ ಪಡೆಯಿರಿ."
                )
            } else {
                DiseaseRecommendation(
                    description = "Unknown disease class detected. Please verify with physical inspection.",
                    symptoms = "Unclassified visual patterns.",
                    causes = "Unidentified pathogen or stress.",
                    organicTreatment = "Maintain basic farm hygiene.",
                    chemicalTreatment = "Apply broad-spectrum copper fungicides as a general protective measure.",
                    recommendedFertilizer = "Apply standard balanced organic manure.",
                    preventiveMeasures = "Ensure optimal soil health and ventilation.",
                    recoveryTime = "Requires assessment.",
                    precautions = "Consult a local Rubber Board officer for precise identification."
                )
            }
        }
    }
}
