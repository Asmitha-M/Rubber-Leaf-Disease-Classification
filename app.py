import os
import io
import time
import re
import difflib
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import streamlit as st
import tensorflow as tf

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------------------------------------------------
# Page Configuration & Constants
# ---------------------------------------------------------
st.set_page_config(
    page_title="RubberGuard - Mobile AI Disease Diagnosis",
    page_icon="🍃",
    layout="centered",
    initial_sidebar_state="collapsed"
)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "app", "src", "main", "assets")
MODEL_PATH = os.path.join(ASSETS_DIR, "model.tflite")
if not os.path.exists(MODEL_PATH) and os.path.exists("model.tflite"):
    MODEL_PATH = "model.tflite"

WEIGHTS_PATH = os.path.join(ASSETS_DIR, "dense_weights.bin")
if not os.path.exists(WEIGHTS_PATH) and os.path.exists("dense_weights.bin"):
    WEIGHTS_PATH = "dense_weights.bin"

CLASSES = [
    "Abnormal Leaf Fall",            # 0: Abnormal
    "Anthracnose",                   # 1: Anthracnose
    "Background / Non-Rubber Leaf",  # 2: Background
    "Black Spot / Bird's Eye",       # 3: Black_Spot
    "Dry Leaf",                      # 4: Dry_Leaf
    "Healthy",                       # 5: Healthy
    "Leaf Blight",                   # 6: Leaf_Blight
    "Leaf Spot",                     # 7: Leaf_Spot
    "Powdery Mildew"                 # 8: Powdery_Mildew
]

# ---------------------------------------------------------
# Knowledge Base & Recommendations (Bilingual: EN & KN)
# ---------------------------------------------------------
RECOMMENDATIONS = {
    "Abnormal Leaf Fall": {
        "en": {
            "name": "Abnormal Leaf Fall",
            "pathogen": "Phytophthora botryosa / Phytophthora meadii",
            "description": "Abnormal Leaf Fall is one of the most destructive diseases affecting rubber plantations in South India during the southwest monsoon season (June to August).",
            "symptoms": "Water-soaked lesions on leaf petioles; green leaves fall prematurely forming a dense carpet on the ground; rotting of fruits/pods.",
            "causes": "High humidity (>90%), continuous monsoon rainfall, cool overcast weather, and water stagnation.",
            "organic": "Collect and burn fallen leaves and rotted pods. Prune inter-canopy branches to improve light and air circulation.",
            "chemical": "Prophylactic aerial/ground spray of 1% Bordeaux mixture before monsoon onset (May/June), followed by copper oxychloride oil dispersion.",
            "fertilizer": "Apply balanced NPK with additional Potassium (MOP) to harden petiole cuticles and strengthen tree immunity.",
            "prevention": "Ensure good drainage; avoid tapping on rain-soaked wet bark; paint tapping panels with antimicrobial paste.",
            "recovery": "30 – 45 days under optimal post-monsoon sunshine."
        },
        "kn": {
            "name": "ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ (Abnormal Leaf Fall)",
            "pathogen": "ಫೈಟೊಫ್ಥೊರಾ ಶಿಲೀಂಧ್ರ (Phytophthora spp.)",
            "description": "ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ ರೋಗವು ಮಳೆಗಾಲದಲ್ಲಿ ಕರ್ನಾಟಕದ ಕರಾವಳಿ ಮತ್ತು ಮಲೆನಾಡು ಭಾಗಗಳಲ್ಲಿ ರಬ್ಬರ್ ಮರಗಳಿಗೆ ತೀವ್ರ ಹಾನಿ ಉಂಟುಮಾಡುತ್ತದೆ.",
            "symptoms": "ಎಲೆಯ ತೊಟ್ಟಿನ ಮೇಲೆ ಕಪ್ಪು ಚುಕ್ಕೆಗಳು, ಎಲೆಗಳು ಹಸಿರಾಗಿರುವಾಗಲೇ ಉದುರುವುದು ಮತ್ತು ಕಾಯಿಗಳು ಕೊಳೆತು ಉದುರುವುದು.",
            "causes": "ಅತಿಯಾದ ಮಳೆ, ನಿರಂತರ ತಂಪು ಹವಾಮಾನ, ಹೆಚ್ಚು ತೇವಾಂಶ ಮತ್ತು ಗಾಳಿಯಾಡದ ದಟ್ಟವಾದ ತೋಪುಗಳು.",
            "organic": "ಉದುರಿದ ಎಲೆಗಳನ್ನು ಒಟ್ಟುಗೂಡಿಸಿ ಸುಡುವುದು. ಮರಗಳ ನಡುವೆ ಗಾಳಿಯಾಡಲು ಹೆಚ್ಚುವರಿ ಕೊಂಬೆಗಳನ್ನು ಕತ್ತರಿಸಿ.",
            "chemical": "ಮಳೆಗಾಲ ಪ್ರಾರಂಭವಾಗುವ ಮೊದಲು (ಮೇ/ಜೂನ್) 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಅಥವಾ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ ಸಿಂಪಡಿಸಿ.",
            "fertilizer": "ಪೊಟ್ಯಾಶ್ (Potassium) ಗೊಬ್ಬರವನ್ನು ಹೆಚ್ಚುವರಿಯಾಗಿ ನೀಡಿ ಮರಗಳ ರೋಗನಿರೋಧಕ ಶಕ್ತಿಯನ್ನು ಹೆಚ್ಚಿಸಿ.",
            "prevention": "ತೋಟದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ಕಾಲುವೆ ಮಾಡಿ; ಮಳೆಗಾಲದಲ್ಲಿ ಟ್ಯಾಪಿಂಗ್ ಪ್ಯಾನಲ್‌ಗೆ ಶಿಲೀಂಧ್ರನಾಶಕ ಪೇಸ್ಟ್ ಹಚ್ಚಿ.",
            "recovery": "30 – 45 ದಿನಗಳು ಸೂಕ್ತ ಕಾಳಜಿಯೊಂದಿಗೆ."
        }
    },
    "Anthracnose": {
        "en": {
            "name": "Anthracnose",
            "pathogen": "Colletotrichum gloeosporioides",
            "description": "Anthracnose attacks tender shoots and young flush leaves, causing dieback in immature rubber plants and nurseries.",
            "symptoms": "Circular brown lesions with concentric rings along leaf margins and tips; curled or shot-holed leaves; twig dieback.",
            "causes": "High atmospheric humidity, warm temperatures with intermittent drizzles, and overcrowding in nurseries.",
            "organic": "Spray 2% Neem Seed Kernel Extract (NSKE) or neem oil emulsion. Prune and destroy blighted twigs.",
            "chemical": "Foliar spray with Carbendazim (0.1%) or Mancozeb (0.2%) at 10-14 day intervals during new leaf flushes.",
            "fertilizer": "Reduce excessive chemical Nitrogen; apply Rock Phosphate and organic compost to promote balanced tissue growth.",
            "prevention": "Avoid overhead sprinkler irrigation in nurseries; maintain adequate nursery shading.",
            "recovery": "15 – 20 days with timely fungicide application."
        },
        "kn": {
            "name": "ಆಂಥ್ರಾಕ್ನೋಸ್ (Anthracnose)",
            "pathogen": "ಕೊಲೆಟೊಟ್ರಿಕಮ್ ಶಿಲೀಂಧ್ರ (Colletotrichum gloeosporioides)",
            "description": "ಆಂಥ್ರಾಕ್ನೋಸ್ ರೋಗವು ಎಳೆಯ ಚಿಗುರುಗಳು, ನರ್ಸರಿ ಸಸಿಗಳು ಮತ್ತು ಎಲೆಗಳನ್ನು ಬಾಧಿಸುವ ಪ್ರಮುಖ ರೋಗವಾಗಿದೆ.",
            "symptoms": "ಎಲೆಗಳ ಅಂಚಿನಲ್ಲಿ ಮತ್ತು ತುದಿಯಲ್ಲಿ ಕಂದು ಬಣ್ಣದ ವೃತ್ತಾಕಾರದ ಚುಕ್ಕೆಗಳು; ಎಲೆಗಳು ಸುರುಟಿಕೊಳ್ಳುವುದು.",
            "causes": "ಹೆಚ್ಚು ತೇವಾಂಶ ಮತ್ತು ಮೋಡ ಕವಿದ ಬಿಸಿ ವಾತಾವರಣ.",
            "organic": "ಬೇವಿನ ಎಣ್ಣೆ (2%) ಸಿಂಪಡಿಸಿ. ಪೀಡಿತ ಸಣ್ಣ ಕೊಂಬೆಗಳನ್ನು ಕತ್ತರಿಸಿ ಸ್ವಚ್ಛಗೊಳಿಸಿ.",
            "chemical": "0.1% ಕಾರ್ಬೆಂಡಾಜಿಮ್ ಅಥವಾ 0.2% ಮ್ಯಾಂಕೋಜೆಬ್ ಶಿಲೀಂಧ್ರನಾಶಕವನ್ನು ಸಿಂಪಡಿಸಿ.",
            "fertilizer": "ಸಾರಜನಕ ಗೊಬ್ಬರ ಕಡಿಮೆ ಮಾಡಿ, ರಂಜಕ ಮತ್ತು ಸಾವಯವ ಗೊಬ್ಬರವನ್ನು ಹೆಚ್ಚಿಸಿ.",
            "prevention": "ನರ್ಸರಿಗಳಲ್ಲಿ ಸಸಿಗಳ ನಡುವೆ ಅಂತರ ಕಾಪಾಡಿ ಮತ್ತು ಸ್ವಚ್ಛತೆಯನ್ನು ಕಾಪಾಡಿ.",
            "recovery": "15 – 20 ದಿನಗಳು."
        }
    },
    "Black Spot / Bird's Eye": {
        "en": {
            "name": "Black Spot / Bird's Eye",
            "pathogen": "Helminthosporium heveae",
            "description": "Bird's Eye Spot affects young rubber nursery plants and tender flushes, producing distinctive circular spots with pale centers.",
            "symptoms": "Small circular spots with white or pale straw-colored centers surrounded by dark reddish-brown margins, resembling a bird's eye.",
            "causes": "Prolonged leaf wetness, poor soil fertility, and excessive sun exposure in nursery beds.",
            "organic": "Ensure good nursery shading with coir mats or agrinets. Spray fermented cow dung slurry filtrate (10%).",
            "chemical": "Spray Chlorothalonil (0.2%) or Dithane M-45 (Mancozeb 0.25%) twice at weekly intervals on young flushes.",
            "fertilizer": "Apply balanced micronutrient mixture containing Zinc and Boron along with regular NPK.",
            "prevention": "Provide regulated shade; water plants at soil level without wetting foliage directly.",
            "recovery": "20 – 30 days."
        },
        "kn": {
            "name": "ಕಪ್ಪು ಚುಕ್ಕೆ / ಹಕ್ಕಿ ಕಣ್ಣು (Black Spot / Bird's Eye)",
            "pathogen": "ಹೆಲ್ಮಿಂಥೊಸ್ಪೊರಿಯಮ್ ಶಿಲೀಂಧ್ರ (Helminthosporium heveae)",
            "description": "ಈ ರೋಗವು ಮುಖ್ಯವಾಗಿ ನರ್ಸರಿ ಸಸಿಗಳು ಮತ್ತು ಎಳೆಯ ಎಲೆಗಳ ಮೇಲೆ ಹಕ್ಕಿಯ ಕಣ್ಣಿನಂತಹ ಚುಕ್ಕೆಗಳನ್ನು ಉಂಟುಮಾಡುತ್ತದೆ.",
            "symptoms": "ಮಧ್ಯದಲ್ಲಿ ಬಿಳಿ ಅಥವಾ ತಿಳಿ ಬಣ್ಣ ಹಾಗೂ ಅಂಚಿನಲ್ಲಿ ಗಾಢ ಕಂದು ಬಣ್ಣದ ಸಣ್ಣ ವೃತ್ತಾಕಾರದ ಚುಕ್ಕೆಗಳು.",
            "causes": "ಸಸಿಗಳಿಗೆ ಅತಿಯಾದ ಬಿಸಿಲು ಮತ್ತು ಮಣ್ಣಿನಲ್ಲಿ ಪೋಷಕಾಂಶಗಳ ಕೊರತೆ.",
            "organic": "ನರ್ಸರಿಯಲ್ಲಿ ಹಸಿರು ಬಲೆಗಳನ್ನು ಬಳಸಿ ಸೂಕ್ತ ನೆರಳು ಒದಗಿಸಿ. ಸಗಣಿ ತಿಳಿ ನೀರು ಸಿಂಪಡಿಸಿ.",
            "chemical": "0.2% ಕ್ಲೋರೋಥಲೋನಿಲ್ ಅಥವಾ 0.25% ಮ್ಯಾಂಕೋಜೆಬ್ ಸಿಂಪಡಿಸಿ.",
            "fertilizer": "ಲಘು ಪೋಷಕಾಂಶಗಳಾದ ಸತು (Zinc) ಮತ್ತು ಬೋರಾನ್ ಒಳಗೊಂಡ ಗೊಬ್ಬರ ನೀಡಿ.",
            "prevention": "ಎಲೆಗಳ ಮೇಲೆ ನೀರು ಬೀಳದಂತೆ ಬುಡಕ್ಕೆ ಮಾತ್ರ ನೀರುಣಿಸಿ; ನಿಯಮಿತವಾಗಿ ಕಳೆ ತೆಗೆಯಿರಿ.",
            "recovery": "20 – 30 ದಿನಗಳು."
        }
    },
    "Leaf Blight": {
        "en": {
            "name": "Leaf Blight",
            "pathogen": "Fusicladium macrosporum / Colletotrichum spp.",
            "description": "Leaf Blight causes rapid scorching and desiccation of mature and semi-mature rubber leaves, reducing canopy photosynthetic area.",
            "symptoms": "Large, irregular, water-soaked necrotic patches that turn dark brown to black and dry out brittle; leaf edge burning.",
            "causes": "Continuous mist, prolonged leaf wetness, and wind-borne fungal spores.",
            "organic": "Collect dried blighted leaves from the base and compost them deeply with Trichoderma viride.",
            "chemical": "Foliar application of Copper Hydroxide (0.2%) or Tebuconazole + Trifloxystrobin formulation.",
            "fertilizer": "Apply soil amendments with Magnesium Sulphate to support chlorophyll restoration.",
            "prevention": "Maintain windbreaks around plantation edges; clear undergrowth weeds.",
            "recovery": "25 – 35 days."
        },
        "kn": {
            "name": "ಎಲೆ ಕರಕಲು ರೋಗ (Leaf Blight)",
            "pathogen": "ಫ್ಯುಸಿಕ್ಲಾಡಿಯಮ್ ಶಿಲೀಂಧ್ರ (Fusicladium macrosporum)",
            "description": "ಎಲೆ ಕರಕಲು ರೋಗವು ಎಲೆಗಳು ಸುಟ್ಟಂತೆ ಒಣಗಿ ಕಪ್ಪಾಗುವಂತೆ ಮಾಡಿ ಮರಗಳ ದ್ಯುತಿಸಂಶ್ಲೇಷಣೆಯನ್ನು ಕುಂಠಿತಗೊಳಿಸುತ್ತದೆ.",
            "symptoms": "ಎಲೆಗಳ ಮೇಲೆ ಅನಿಯಮಿತ ಗಾಢ ಕಂದು ಅಥವಾ ಕಪ್ಪು ಬಣ್ಣದ ದೊಡ್ಡ ಕರಕಲು ಕಲೆಗಳು; ಎಲೆಗಳು ಸುಲಭವಾಗಿ ಮುರಿಯುವುದು.",
            "causes": "ನಿರಂತರ ಮಂಜು, ತೇವಾಂಶ ಮತ್ತು ಗಾಳಿಯ ಮೂಲಕ ಹರಡುವ ಶಿಲೀಂಧ್ರ ಬೀಜಕಗಳು.",
            "organic": "ಒಣಗಿದ ಎಲೆಗಳನ್ನು ತೆಗೆದು ಟ್ರೈಕೋಡರ್ಮಾ ಜೈವಿಕ ಶಿಲೀಂಧ್ರನಾಶಕ ಬಳಸಿ ವಿಲೇವಾರಿ ಮಾಡಿ.",
            "chemical": "0.2% ಕಾಪರ್ ಹೈಡ್ರಾಕ್ಸೈಡ್ ಅಥವಾ ಟೆಬುಕೊನಜೋಲ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಸಿಂಪಡಿಸಿ.",
            "fertilizer": "ಮೆಗ್ನೀಷಿಯಂ ಸಲ್ಫೇಟ್ ನೀಡಿ ಎಲೆಗಳಲ್ಲಿ ಹಸಿರು ಕಣಗಳನ್ನು ಪುನರುಜ್ಜೀವನಗೊಳಿಸಿ.",
            "prevention": "ತೋಟದ ಸುತ್ತ ಗಾಳಿತಡೆ ಗಿಡಗಳನ್ನು ಬೆಳೆಸಿ ಮತ್ತು ಕಳೆ ಸ್ವಚ್ಛಗೊಳಿಸಿ.",
            "recovery": "25 – 35 ದಿನಗಳು."
        }
    },
    "Leaf Spot": {
        "en": {
            "name": "Leaf Spot",
            "pathogen": "Corynespora cassiicola",
            "description": "Corynespora Leaf Spot causes premature defoliation and severe yield loss in mature rubber plantations, characterized by 'railway-track' lesions.",
            "symptoms": "Dark brown circular spots with vein-limited black borders resembling miniature railway tracks; yellow halo around spots; leaf drop.",
            "causes": "High rainfall followed by sunny humid weather; susceptible clones (e.g., RRII 105 in certain microclimates).",
            "organic": "Spray bio-fungicides like Pseudomonas fluorescens (20g/L) during early spot formation.",
            "chemical": "Spray Hexaconazole (0.1%) or Propiconazole (0.1%) or Mancozeb (0.25%) immediately upon noticing first lesions.",
            "fertilizer": "Top-dress with additional Muriate of Potash (MOP) to accelerate leaf cuticle thickening.",
            "prevention": "Avoid overly dense planting; monitor susceptible clones regularly after showers.",
            "recovery": "25 – 30 days."
        },
        "kn": {
            "name": "ಎಲೆ ಚುಕ್ಕೆ ರೋಗ (Leaf Spot)",
            "pathogen": "ಕೊರಿನಿಸ್ಪೊರಾ ಶಿಲೀಂಧ್ರ (Corynespora cassiicola)",
            "description": "ಕೊರಿನಿಸ್ಪೊರಾ ಎಲೆ ಚುಕ್ಕೆ ರೋಗವು ಎಲೆ ನರಗಳ ಮೇಲೆ ಹರಡಿ ಮರಗಳ ಇಳುವರಿಯನ್ನು ಗಣನೀಯವಾಗಿ ತಗ್ಗಿಸುತ್ತದೆ.",
            "symptoms": "ಎಲೆಯ ನರಗಳ ಉದ್ದಕ್ಕೂ ರೈಲ್ವೆ ಹಳಿಯಂತೆ ಕಾಣುವ ಕಂದು ಕಲೆಗಳು; ಕಲೆಗಳ ಸುತ್ತ ಹಳದಿ ಬಳೆ ಮತ್ತು ಅಕಾಲಿಕ ಎಲೆ ಉದುರುವಿಕೆ.",
            "causes": "ಮಳೆ ನಂತರದ ಸೆಕೆ ಮತ್ತು ಬಿಸಿಲಿನ ವಾತಾವರಣ.",
            "organic": "ಸ್ಯೂಡೋಮೊನಾಸ್ ಫ್ಲೋರೊಸೆನ್ಸ್ (Pseudomonas) ಜೈವಿಕ ನಿಯಂತ್ರಕ ಸಿಂಪಡಿಸಿ.",
            "chemical": "0.1% ಹೆಕ್ಸಾಕೊನಜೋಲ್ ಅಥವಾ 0.1% ಪ್ರೊಪಿಕೊನಜೋಲ್ ಶಿಲೀಂಧ್ರನಾಶಕವನ್ನು ಸಿಂಪಡಿಸಿ.",
            "fertilizer": "ಪೊಟ್ಯಾಶ್ ಗೊಬ್ಬರ ನೀಡಿ ಎಲೆಗಳ ಹೊರಪದರ ಗಟ್ಟಿಯಾಗುವಂತೆ ಮಾಡಿ.",
            "prevention": "ಮಳೆಗಾಲದ ನಂತರ ನಿಯಮಿತವಾಗಿ ತಪಾಸಣೆ ಮಾಡಿ ಮತ್ತು ಸೋಂಕು ಕಂಡುಬಂದ ತಕ್ಷಣ ಸಿಂಪಡಿಸಿ.",
            "recovery": "25 – 30 ದಿನಗಳು."
        }
    },
    "Powdery Mildew": {
        "en": {
            "name": "Powdery Mildew",
            "pathogen": "Oidium heveae",
            "description": "Powdery Mildew attacks fresh rubber foliage during the annual refoliation season (January to March), causing young leaf curling and drop.",
            "symptoms": "White powdery patches on both leaf surfaces; crinkling, curling, and distortion of young tender leaves; secondary leaf fall.",
            "causes": "Cool dry nights with morning dew followed by warm sunny dry days during refoliation season.",
            "organic": "Dust with fine elemental sulfur or spray wettable sulfur (0.2%) early in the morning when leaves are dewy.",
            "chemical": "Sulphur dusting at 12–15 kg/ha (3–4 rounds at 7–10 day intervals) or spray Carbendazim (0.05%) / Dinocap (0.1%).",
            "fertilizer": "Ensure sufficient Potash in the pre-monsoon fertilizer application.",
            "prevention": "Plan defoliation schedules; dust early in the morning when wind velocity is low to prevent drift.",
            "recovery": "20 – 25 days."
        },
        "kn": {
            "name": "ಬೂದಿ ರೋಗ (Powdery Mildew)",
            "pathogen": "ಒಯಿಡಿಯಮ್ ಶಿಲೀಂಧ್ರ (Oidium heveae)",
            "description": "ಬೂದಿ ರೋಗವು ವಾರ್ಷಿಕ ಚಿಗುರುವಿಕೆಯ ಸಮಯದಲ್ಲಿ (ಜನವರಿಯಿಂದ ಮಾರ್ಚ್) ಹೊಸ ಎಲೆಗಳ ಮೇಲೆ ಬಿಳಿ ಬೂದಿಯಂತೆ ಹರಡುತ್ತದೆ.",
            "symptoms": "ಎಲೆಯ ಮೇಲ್ಮೈಯಲ್ಲಿ ಬಿಳಿ ಬಣ್ಣದ ಬೂದಿ ಹಿಟ್ಟಿನಂತಹ ಕಲೆಗಳು; ಎಲೆಗಳು ಸುರುಟಿಕೊಳ್ಳುವುದು ಮತ್ತು ಉದುರುವುದು.",
            "causes": "ರಾತ್ರಿ ತಂಪು ಮತ್ತು ಹಗಲು ಬಿಸಿಲಿನ ಶುಷ್ಕ ಹವಾಮಾನ ಹಾಗೂ ಮುಂಜಾನೆಯ ಇಬ್ಬನಿ.",
            "organic": "ಮುಂಜಾನೆಯ ಇಬ್ಬನಿ ಇರುವಾಗ ಗಂಧಕದ ಪುಡಿ (Sulfur dust) ಅಥವಾ ನೀರಿನಲ್ಲಿ ಕರಗುವ ಗಂಧಕ ಸಿಂಪಡಿಸಿ.",
            "chemical": "ಹೆಕ್ಟೇರಿಗೆ 12-15 ಕೆಜಿ ಗಂಧಕದ ಪುಡಿ ಧೂಳೀಕರಣ (Dusting) ಅಥವಾ 0.05% ಕಾರ್ಬೆಂಡಾಜಿಮ್ ಸಿಂಪಡಿಸಿ.",
            "fertilizer": "ಪೊಟ್ಯಾಶ್ ಪೋಷಕಾಂಶ ನೀಡಿ ಚಿಗುರೆಲೆಗಳು ವೇಗವಾಗಿ ಬಲಿತುಕೊಳ್ಳಲು ಉತ್ತೇಜಿಸಿ.",
            "prevention": "ಗಾಳಿಯ ವೇಗ ಕಡಿಮೆಯಿರುವ ಮುಂಜಾನೆಯ ವೇಳೆ ಗಂಧಕ ಧೂಳೀಕರಣ ಮಾಡಿ.",
            "recovery": "20 – 25 ದಿನಗಳು."
        }
    },
    "Dry Leaf": {
        "en": {
            "name": "Dry Leaf / Environmental Stress",
            "pathogen": "Abiotic (Moisture Stress / Sun Scorch)",
            "description": "Dry Leaf is caused by extreme heat, drought, soil moisture deficits, or severe root damage rather than an active infectious pathogen.",
            "symptoms": "Brown, parchment-like brittle leaf margins; upward leaf curling; premature shedding of older leaves.",
            "causes": "Extended summer drought, direct scorching sunlight, shallow soil depth, or root disturbance.",
            "organic": "Mulch the tree basins with dry organic matter or green leaf cuttings to retain soil moisture.",
            "chemical": "No chemical fungicide required. Spray 1% Potassium chloride solution to alleviate water stress.",
            "fertilizer": "Incorporate well-rotted farmyard manure (FYM) and vermicompost to enhance soil water holding capacity.",
            "prevention": "Provide irrigation in young plantations; establish shade covers for saplings during peak summer.",
            "recovery": "10 – 15 days following irrigation or rain."
        },
        "kn": {
            "name": "ಒಣಗಿದ ಎಲೆ / ನೀರಿನ ಕೊರತೆ (Dry Leaf)",
            "pathogen": "ಅಜೈವಿಕ ಕಾರಣ (ಬಿಸಿಲು ಮತ್ತು ನೀರಿನ ಕೊರತೆ)",
            "description": "ಇದು ಯಾವುದೇ ಶಿಲೀಂಧ್ರದಿಂದಲ್ಲದೆ ಬೇಸಿಗೆಯ ತೀವ್ರ ಬಿಸಿಲು ಮತ್ತು ಮಣ್ಣಿನಲ್ಲಿ ನೀರಿನ ಕೊರತೆಯಿಂದ ಉಂಟಾಗುತ್ತದೆ.",
            "symptoms": "ಎಲೆಯ ಅಂಚುಗಳು ಕಂದು ಬಣ್ಣಕ್ಕೆ ತಿರುಗಿ ಒಣಗುವುದು; ಎಲೆಗಳು ಸುರುಟಿಕೊಳ್ಳುವುದು.",
            "causes": "ತೀವ್ರ ಬೇಸಿಗೆ, ಬಿಸಿಲು, ಮಣ್ಣಿನ ತೇವಾಂಶ ಕೊರತೆ.",
            "organic": "ಮರದ ಬುಡಕ್ಕೆ ಒಣ ಎಲೆಗಳು ಅಥವಾ ತೆಂಗಿನ ತ್ಯಾಜ್ಯದಿಂದ ಹೊದಿಕೆ (Mulching) ಹಾಕಿ ತೇವಾಂಶ ಕಾಪಾಡಿ.",
            "chemical": "ಯಾವುದೇ ಶಿಲೀಂಧ್ರನಾಶಕದ ಅಗತ್ಯವಿಲ್ಲ.",
            "fertilizer": "ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ ಮತ್ತು ಎರೆಹುಳು ಗೊಬ್ಬರ ನೀಡಿ ಮಣ್ಣಿನ ನೀರು ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳುವ ಸಾಮರ್ಥ್ಯ ಹೆಚ್ಚಿಸಿ.",
            "prevention": "ಬೇಸಿಗೆಯಲ್ಲಿ ಸಾಧ್ಯವಾದರೆ ಹನಿ ನೀರಾವರಿ ಒದಗಿಸಿ; ಸಸಿಗಳಿಗೆ ನೆರಳು ಕಲ್ಪಿಸಿ.",
            "recovery": "ನೀರುಣಿಸಿದ 10 – 15 ದಿನಗಳಲ್ಲಿ ಸುಧಾರಣೆ."
        }
    },
    "Healthy": {
        "en": {
            "name": "Healthy Rubber Leaf",
            "pathogen": "None (Plant in optimal health)",
            "description": "The leaf shows vigorous green coloration, intact lamina, clean veins, and no necrotic fungal or bacterial symptoms.",
            "symptoms": "Rich uniform green color; pliable lamina; no spots, chlorosis, or powdery mildew.",
            "causes": "Balanced soil nutrition, timely canopy maintenance, and clean agricultural practices.",
            "organic": "Continue periodic foliar sprays with Jeevamrutha or Panchagavya (3%) to sustain beneficial phyllosphere microbes.",
            "chemical": "No chemical intervention needed.",
            "fertilizer": "Maintain regular seasonal NPK application schedule (10:10:10 or 12:12:12 NPK) as recommended by Rubber Board.",
            "prevention": "Maintain clean plantation sanitation; inspect leaves periodically before and after monsoons.",
            "recovery": "N/A"
        },
        "kn": {
            "name": "ಆರೋಗ್ಯಕರ ಎಲೆ (Healthy Leaf)",
            "pathogen": "ಯಾವುದೂ ಇಲ್ಲ (ಉತ್ತಮ ಆರೋಗ್ಯ)",
            "description": "ಎಲೆಯು ಸಂಪೂರ್ಣ ಹಸಿರಾಗಿದ್ದು, ಯಾವುದೇ ಶಿಲೀಂಧ್ರ ಅಥವಾ ಬ್ಯಾಕ್ಟೀರಿಯಾ ಸೋಂಕಿನ ಲಕ್ಷಣಗಳಿಲ್ಲದೆ ಉತ್ತಮ ಆರೋಗ್ಯದಲ್ಲಿದೆ.",
            "symptoms": "ಏಕರೂಪದ ಹಸಿರು ಬಣ್ಣ; ನಯವಾದ ಮೇಲ್ಮೈ; ಯಾವುದೇ ಚುಕ್ಕೆಗಳಿಲ್ಲ.",
            "causes": "ಉತ್ತಮ ಮಣ್ಣಿನ ಫಲವತ್ತತೆ ಮತ್ತು ಸಮಯೋಚಿತ ಕೃಷಿ ನಿರ್ವಹಣೆ.",
            "organic": "ಜೀವಾಮೃತ ಅಥವಾ ಪಂಚಗವ್ಯ (3%) ಸಿಂಪಡಿಸಿ ಗಿಡಗಳ ನೈಸರ್ಗಿಕ ರೋಗನಿರೋಧಕತೆಯನ್ನು ಕಾಪಾಡಿ.",
            "chemical": "ಯಾವುದೇ ರಾಸಾಯನಿಕ ಅಗತ್ಯವಿಲ್ಲ.",
            "fertilizer": "ರಬ್ಬರ್ ಬೋರ್ಡ್ ಶಿಫಾರಸಿನಂತೆ ವಾರ್ಷಿಕ ಸಮತೋಲಿತ NPK ಗೊಬ್ಬರ ನೀಡುವುದನ್ನು ಮುಂದುವರಿಸಿ.",
            "prevention": "ತೋಟದಲ್ಲಿ ನಿಯಮಿತ ಕಳೆ ನಿರ್ವಹಣೆ ಮತ್ತು ವೀಕ್ಷಣೆ ಮುಂದುವರಿಸಿ.",
            "recovery": "ಅನ್ವಯಿಸುವುದಿಲ್ಲ"
        }
    }
}

# ---------------------------------------------------------
# Caching Model & TFLite Interpreter
# ---------------------------------------------------------
@st.cache_resource
def load_tflite_model():
    if not os.path.exists(MODEL_PATH):
        st.error(f"TFLite model file not found at: {MODEL_PATH}")
        return None, None
    
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    
    # Load Grad-CAM weights
    weights = None
    if os.path.exists(WEIGHTS_PATH):
        weights = np.fromfile(WEIGHTS_PATH, dtype=np.float32)
        # Reshape to (1280, 9)
        if weights.size == 1280 * len(CLASSES):
            weights = weights.reshape((1280, len(CLASSES)))
        else:
            weights = None
            
    return interpreter, weights

# ---------------------------------------------------------
# OpenCV Preprocessing & Validation Pipeline
# ---------------------------------------------------------
def preprocess_and_validate(image_rgb):
    """
    Applies the full OpenCV preprocessor pipeline:
    1. HSV color-space organic tissue segmentation
    2. Largest contour leaf detection & background removal
    3. Illumination & Shadow Correction (Lab CLAHE)
    4. Bilateral noise reduction
    5. Gaussian unsharp mask sharpening
    6. Quality validation checks (leaf coverage, blurriness, exposure)
    """
    h, w, _ = image_rgb.shape
    total_pixels = h * w
    
    # Convert to HSV
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    
    # Masks for healthy green, senescent yellow-brown, dark spots, and mildew white
    green_mask = cv2.inRange(hsv, (35, 30, 30), (85, 255, 255))
    yellow_brown_mask = cv2.inRange(hsv, (10, 30, 30), (35, 255, 255))
    dark_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, 60))
    white_mask = cv2.inRange(hsv, (0, 0, 150), (180, 50, 255))
    
    diseased_mask = cv2.bitwise_or(cv2.bitwise_or(yellow_brown_mask, dark_mask), white_mask)
    leaf_mask = cv2.bitwise_or(green_mask, diseased_mask)
    
    # Find external contours
    contours, _ = cv2.findContours(leaf_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, None, {
            "passed": False,
            "error": "No leaf detected. Please upload a clear image of a rubber leaf.",
            "details": "No leaf contours found via HSV color segmentation."
        }
        
    # Filter small noise contours
    significant_contours = [c for c in contours if cv2.contourArea(c) > 100]
    if not significant_contours:
        return None, None, {
            "passed": False,
            "error": "No leaf detected. Please upload a clear image of a rubber leaf.",
            "details": "Contour surface area is too small."
        }
        
    largest_contour = max(significant_contours, key=cv2.contourArea)
    max_area = cv2.contourArea(largest_contour)
    leaf_ratio = max_area / float(total_pixels)
    
    # Quality Check: Multiple leaves
    large_contours = [c for c in significant_contours if cv2.contourArea(c) > (total_pixels * 0.05)]
    multi_leaf = len(large_contours) > 1
    
    # Quality Check: Leaf size (leaf occupies >= 5% of the image)
    too_small = leaf_ratio < 0.05
    
    # Quality Check: Exposure (Luminance in Lab)
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2Lab)
    l_channel, a_channel, b_channel = cv2.split(lab)
    mean_luminance = float(np.mean(l_channel))
    is_bad_exposure = mean_luminance < 30.0 or mean_luminance > 240.0
    
    # Quality Check: Focus blur (Laplacian variance - only reject severe unusable blur)
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_blurry = laplacian_var < 6.0
    
    validation_passed = not (multi_leaf or too_small or is_bad_exposure or is_blurry)
    
    validation_metrics = {
        "passed": validation_passed,
        "leaf_ratio": leaf_ratio * 100,
        "multi_leaf": multi_leaf,
        "too_small": too_small,
        "mean_luminance": mean_luminance,
        "is_bad_exposure": is_bad_exposure,
        "laplacian_var": laplacian_var,
        "is_blurry": is_blurry,
        "error": None if validation_passed else "Please upload a clear image containing a single rubber leaf."
    }
    
    # Crop to Bounding Box
    bx, by, bw, bh = cv2.boundingRect(largest_contour)
    validation_metrics["bbox"] = (bx, by, bw, bh)
    cropped = image_rgb[by:by+bh, bx:bx+bw]
    
    # Mask out background clutter (pure black)
    mask = np.zeros((bh, bw), dtype=np.uint8)
    translated_contour = largest_contour - np.array([bx, by])
    cv2.drawContours(mask, [translated_contour], -1, 255, -1)
    segmented = cv2.bitwise_and(cropped, cropped, mask=mask)
    
    # CLAHE shadow & illumination normalization on L channel
    seg_lab = cv2.cvtColor(segmented, cv2.COLOR_RGB2Lab)
    sl, sa, sb = cv2.split(seg_lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    sl_eq = clahe.apply(sl)
    enhanced = cv2.cvtColor(cv2.merge([sl_eq, sa, sb]), cv2.COLOR_Lab2RGB)
    
    # Adaptive enhancement: If image is soft or slightly blurry, apply unsharp masking
    # to restore fine lesion boundaries, fungal mycelium, and concentric spot edges!
    if laplacian_var < 75.0:
        boost = min(1.7, max(0.7, (75.0 - laplacian_var) / 35.0))
        blurred = cv2.GaussianBlur(enhanced, (0, 0), 2.5)
        sharpened = cv2.addWeighted(enhanced, 1.0 + boost, blurred, -boost, 0)
    else:
        denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=30.0, sigmaSpace=30.0)
        blurred = cv2.GaussianBlur(denoised, (5, 5), 0)
        sharpened = cv2.addWeighted(denoised, 1.3, blurred, -0.3, 0)
    
    # Resize to exact 224x224
    preprocessed_224 = cv2.resize(sharpened, (224, 224))
    
    return preprocessed_224, segmented, validation_metrics

# ---------------------------------------------------------
# Severity Calculation Function
# ---------------------------------------------------------
def estimate_severity(image_rgb, is_healthy=False):
    if is_healthy:
        return 0.0, "Healthy / Trace", "#2E7D32"
        
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    green_mask = cv2.inRange(hsv, (35, 30, 30), (85, 255, 255))
    yellow_brown_mask = cv2.inRange(hsv, (10, 30, 30), (35, 255, 255))
    dark_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, 60))
    white_mask = cv2.inRange(hsv, (0, 0, 150), (180, 50, 255))
    
    diseased_mask = cv2.bitwise_or(cv2.bitwise_or(yellow_brown_mask, dark_mask), white_mask)
    
    green_pixels = cv2.countNonZero(green_mask)
    diseased_pixels = cv2.countNonZero(diseased_mask)
    total_leaf = green_pixels + diseased_pixels
    
    if total_leaf == 0:
        return 0.0, "Healthy / Trace", "#2E7D32"
        
    severity_pct = (diseased_pixels / float(total_leaf)) * 100.0
    
    if severity_pct < 5.0:
        return severity_pct, "Healthy / Trace", "#2E7D32"
    elif severity_pct <= 20.0:
        return severity_pct, "Mild Infection", "#F59E0B"
    elif severity_pct <= 50.0:
        return severity_pct, "Moderate Infection", "#EF4444"
    else:
        return severity_pct, "Severe Defoliation", "#B91C1C"

# ---------------------------------------------------------
# Grad-CAM Heatmap Generator
# ---------------------------------------------------------
def generate_gradcam_overlay(feature_map, weights, predicted_idx, target_image_rgb, bbox=None):
    """
    Computes class-activation map (CAM) from 7x7x1280 features and 1280x9 weights.
    Uses bicubic interpolation, Gaussian smoothing, and adaptive alpha-masking so healthy tissue
    remains 100% natural and only diseased lesions glow vibrantly in yellow/orange/red.
    If bbox is provided, maps the activations to the leaf bounding box on the full capture.
    """
    if weights is None or feature_map is None:
        return None
        
    # feature_map shape: (1, 7, 7, 1280)
    feat = feature_map[0] # (7, 7, 1280)
    class_weights = weights[:, predicted_idx] # (1280,)
    
    # Linear combination
    cam = np.dot(feat, class_weights) # (7, 7)
    
    # ReLU
    cam = np.maximum(cam, 0)
    
    # Normalize to [0, 1]
    if np.max(cam) > 0:
        cam = cam / np.max(cam)
        
    h, w, _ = target_image_rgb.shape
    
    if bbox is not None:
        bx, by, bw, bh = bbox
        cam_leaf = cv2.resize(cam, (bw, bh), interpolation=cv2.INTER_CUBIC)
        full_cam = np.zeros((h, w), dtype=np.float32)
        full_cam[by:by+bh, bx:bx+bw] = cam_leaf
        cam_target = full_cam
    else:
        cam_target = cv2.resize(cam, (w, h), interpolation=cv2.INTER_CUBIC)
        
    # 1. High-resolution CAM smoothing
    cam_smooth = cv2.GaussianBlur(cam_target, (21, 21), 0)
    
    # 2. Precise Leaf Segmentation (rejection of paper, paper shadows, void, and hand)
    r = target_image_rgb[:, :, 0].astype(np.float32)
    g = target_image_rgb[:, :, 1].astype(np.float32)
    b = target_image_rgb[:, :, 2].astype(np.float32)
    
    hsv = cv2.cvtColor(target_image_rgb, cv2.COLOR_RGB2HSV)
    H = hsv[:, :, 0].astype(np.float32)
    S = hsv[:, :, 1].astype(np.float32)
    V = hsv[:, :, 2].astype(np.float32)
    
    # Paper (white, gray shadow, warm shadow): Saturation < 38
    is_paper_or_shadow = (S < 38.0)
    is_bright_white = (r > 175.0) & (g > 175.0) & (b > 175.0)
    is_cool_shadow = (b > g + 3.0) & (b > r + 8.0)
    is_dark_void = (V < 25.0)
    is_hand = (r > 115.0) & (r > g + 16.0) & (b < 120.0)
    
    is_bg = is_paper_or_shadow | is_bright_white | is_cool_shadow | is_dark_void | is_hand
    raw_leaf = (~is_bg).astype(np.uint8) * 255
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    leaf_closed = cv2.morphologyEx(raw_leaf, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(leaf_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    leaf_mask = np.zeros((h, w), dtype=np.uint8)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 200:
            cv2.drawContours(leaf_mask, [largest], -1, 255, -1)
        else:
            leaf_mask = leaf_closed
    else:
        leaf_mask = leaf_closed
        
    leaf_mask_float = leaf_mask.astype(np.float32) / 255.0
    leaf_mask_smooth = cv2.GaussianBlur(leaf_mask_float, (7, 7), 0)
    
    # 3. Determine existing dominant leaf color: Is leaf predominantly GREEN or BROWN?
    leaf_pixels_h = H[leaf_mask == 255]
    leaf_pixels_s = S[leaf_mask == 255]
    leaf_pixels_v = V[leaf_mask == 255]
    
    if len(leaf_pixels_h) > 0:
        green_count = np.sum((leaf_pixels_h >= 35) & (leaf_pixels_h <= 95) & (leaf_pixels_s > 30))
        is_green_leaf = (green_count / float(len(leaf_pixels_h))) > 0.40
        med_v = float(np.median(leaf_pixels_v))
    else:
        is_green_leaf = True
        med_v = 80.0
        
    # 4. Damage Detection: Where color is DIFFERENT from existing leaf tissue
    has_chroma = (S > 35.0).astype(np.float32)
    
    if is_green_leaf:
        # EXISTING LEAF IS GREEN. Damage is where color differs from green:
        # A. Brown / bronze / necrotic lesions:
        brown_chroma = np.clip((r - b - 20.0) / 25.0, 0.0, 1.0)
        red_vs_green = np.clip((r - (g - 5.0)) / 20.0, 0.0, 1.0)
        brown_lesion = brown_chroma * red_vs_green * has_chroma
        
        # B. Yellow chlorotic halos:
        min_rg = np.minimum(r, g)
        yellow_diff = np.clip(((min_rg - b) - 20.0) / 25.0, 0.0, 1.0)
        is_yellow_hue = ((H >= 12.0) & (H <= 38.0)).astype(np.float32)
        yellow_halo = yellow_diff * is_yellow_hue * has_chroma
        
        # C. Pale / dry / powdery spots / translucent shot-holes:
        pale_val = np.clip((V - 130.0) / 35.0, 0.0, 1.0)
        pale_red_bias = np.clip((r - b - 15.0) / 15.0, 0.0, 1.0)
        pale_spot = pale_val * pale_red_bias
        
        # D. Dark necrotic centers:
        dark_diff = np.clip(((med_v - 18.0) - V) / 20.0, 0.0, 1.0)
        not_green = (g - r < 8.0).astype(np.float32)
        dark_spot = dark_diff * not_green * has_chroma
        
        raw_damage = np.maximum(brown_lesion, yellow_halo)
        raw_damage = np.maximum(raw_damage, pale_spot)
        raw_damage = np.maximum(raw_damage, dark_spot) * leaf_mask_float
    else:
        # EXISTING LEAF IS BROWN / DRY / TRANSITIONING. Damage differs from brown:
        dark_necrosis = np.clip(((med_v - 15.0) - V) / 22.0, 0.0, 1.0) * has_chroma
        pale_blight = np.clip((V - (med_v + 20.0)) / 22.0, 0.0, 1.0) * has_chroma
        raw_damage = np.maximum(dark_necrosis, pale_blight) * leaf_mask_float
        
    damage_glow = cv2.GaussianBlur(raw_damage, (7, 7), 0)
    damage_glow = np.clip(damage_glow * 1.8, 0.0, 1.0)
    
    # 5. Spot-Grounded Heatmap Fusion
    # Neural CAM modulates physical spots: primary AI focus zone glows fiery crimson (0.8 - 1.0)
    # Confirmed spots across leaf glow warm orange/yellow; healthy lamina stays 0.0 (natural photo!)
    final_heat = damage_glow * (0.50 + 0.50 * cam_smooth) * leaf_mask_smooth
    f_max = np.max(final_heat)
    if f_max > 0:
        final_heat = final_heat / f_max
        
    # 6. Colormap and Smooth Alpha Blending
    threshold = 0.12
    norm_act = np.clip((final_heat - threshold) / (1.0 - threshold), 0.0, 1.0)
    alpha = (norm_act ** 1.3) * 0.85
    
    heatmap_u8 = np.uint8(255 * final_heat)
    heatmap_color = cv2.applyColorMap(heatmap_u8, cv2.COLORMAP_JET)
    heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
    
    alpha_3d = np.expand_dims(alpha, axis=-1)
    overlay = target_image_rgb.astype(np.float32) * (1.0 - alpha_3d) + heatmap_color.astype(np.float32) * alpha_3d
    return np.clip(overlay, 0, 255).astype(np.uint8)



# ---------------------------------------------------------
# ReportLab PDF Generation
# ---------------------------------------------------------
def generate_pdf_report(farmer_name, disease_name, confidence, severity_label, severity_pct, rec, original_pil, heatmap_pil, lang="en"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1B5E20')
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2E7D32')
    )
    normal_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1F2937')
    )
    bold_style = ParagraphStyle(
        'BoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#111827')
    )
    
    # Header Banner
    story.append(Paragraph("RubberGuard: Leaf Disease Diagnostic Report", title_style))
    story.append(Paragraph(f"Autonomous On-Device MobileNetV2 Analysis • Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}", normal_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2E7D32'), spaceAfter=15))
    
    # Summary Table
    meta_data = [
        [Paragraph("<b>Farmer / Field:</b>", bold_style), Paragraph(farmer_name, normal_style),
         Paragraph("<b>Diagnosis Status:</b>", bold_style), Paragraph(disease_name, bold_style)],
        [Paragraph("<b>Confidence Level:</b>", bold_style), Paragraph(f"{confidence:.1f}%", normal_style),
         Paragraph("<b>Severity Assessment:</b>", bold_style), Paragraph(f"{severity_label} ({severity_pct:.1f}%)", normal_style)],
        [Paragraph("<b>Causal Pathogen:</b>", bold_style), Paragraph(rec.get("pathogen", "N/A"), normal_style),
         Paragraph("<b>Recovery Time:</b>", bold_style), Paragraph(rec.get("recovery", "N/A"), normal_style)]
    ]
    t = Table(meta_data, colWidths=[120, 140, 130, 130])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4FBF5')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#A3D9A5')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1E7D3')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # Images (Original vs Heatmap)
    img_data = []
    orig_buf = io.BytesIO()
    original_pil.resize((220, 220)).save(orig_buf, format="JPEG")
    orig_buf.seek(0)
    
    heat_buf = io.BytesIO()
    heatmap_pil.resize((220, 220)).save(heat_buf, format="JPEG")
    heat_buf.seek(0)
    
    img_table = Table([
        [Paragraph("<b>Original Leaf Capture</b>", bold_style), Paragraph("<b>Grad-CAM Explainable AI Saliency</b>", bold_style)],
        [RLImage(orig_buf, width=220, height=180), RLImage(heat_buf, width=220, height=180)]
    ], colWidths=[260, 260])
    img_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
    ]))
    story.append(img_table)
    story.append(Spacer(1, 15))
    
    # Recommendations
    story.append(Paragraph("1. Symptoms & Visual Identification", heading_style))
    story.append(Paragraph(rec.get("symptoms", "N/A"), normal_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("2. Organic & Cultural Control Measures", heading_style))
    story.append(Paragraph(rec.get("organic", "N/A"), normal_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("3. Recommended Chemical Fungicides", heading_style))
    story.append(Paragraph(rec.get("chemical", "N/A"), normal_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("4. Fertilizer & Tree Nutrition Schedule", heading_style))
    story.append(Paragraph(rec.get("fertilizer", "N/A"), normal_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("5. Preventive Agronomic Protocol", heading_style))
    story.append(Paragraph(rec.get("prevention", "N/A"), normal_style))
    story.append(Spacer(1, 15))
    
    # Footer Notice
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray, spaceAfter=8))
    story.append(Paragraph("Notice: Generated automatically by RubberGuard MobileNetV2 Diagnostic Pipeline. For official advisory contact the Rubber Board of India helpline at 1800-425-5522.", ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.dimgray)))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# Chatbot Engine (Bilingual, Typo-Tolerant, Fuzzy NLP)
# ---------------------------------------------------------
CHATBOT_STOPWORDS = {
    'how', 'to', 'for', 'the', 'is', 'a', 'in', 'of', 'and', 'what',
    'why', 'can', 'you', 'my', 'do', 'should', 'i', 'need', 'wat',
    'evn', 'much', 'about', 'give', 'tell', 'me', 'which'
}

def _fuzzy_token_match(token: str, target: str) -> bool:
    if token == target:
        return True
    if len(token) >= 4 and len(target) >= 4:
        if token in target or target in token:
            return True
    return difflib.SequenceMatcher(None, token, target).ratio() >= 0.72

def _calc_match_score(query: str, aliases: list) -> float:
    q_norm = query.lower().strip()
    for alias in aliases:
        a_norm = alias.lower().strip()
        if a_norm in q_norm:
            return 100.0 + len(a_norm)
            
    q_tokens = [w for w in re.sub(r'[^\w\s]', ' ', q_norm).split() if len(w) >= 2 and w not in CHATBOT_STOPWORDS]
    if not q_tokens:
        q_tokens = [w for w in q_norm.split() if w]
        
    best_score = 0.0
    for alias in aliases:
        a_tokens = [w for w in re.sub(r'[^\w\s]', ' ', alias.lower()).split() if len(w) >= 2 and w not in CHATBOT_STOPWORDS]
        if not a_tokens:
            continue
            
        matched_count = 0
        similarity_sum = 0.0
        for at in a_tokens:
            best_token_sim = 0.0
            for qt in q_tokens:
                if qt == at:
                    sim = 1.0
                elif len(qt) >= 4 and len(at) >= 4 and (qt in at or at in qt):
                    sim = 0.95
                else:
                    sim = difflib.SequenceMatcher(None, qt, at).ratio()
                if sim > best_token_sim:
                    best_token_sim = sim
            if best_token_sim >= 0.72:
                matched_count += 1
                similarity_sum += best_token_sim
                
        if matched_count > 0:
            precision = matched_count / float(len(a_tokens))
            score = (matched_count * 10.0) + (similarity_sum * 5.0) + (precision * 2.0)
            if score > best_score:
                best_score = score
                
    return best_score

CHATBOT_TOPIC_ALIASES = [
    ("GREETING", ["hello", "hi", "hey", "greetings", "good morning", "namaste", "ನಮಸ್ಕಾರ", "ಹಲೋ", "ಹಾಯ್", "ಶುಭೋದಯ"]),
    ("BORDEAUX", ["bordeaux", "bordaux", "bordeax", "bordox", "copper sulfate", "bluestone", "lime mix", "copper knife test", "blue spray", "ಬೋರ್ಡೋ", "ಮೈಲುತುತ್ತು", "ಬೋರ್ಡೋ ದ್ರಾವಣ", "ಸುಣ್ಣ ಮೈಲುತುತ್ತು"]),
    ("TAPPING", ["tap", "tapping", "tapin", "tapper", "latex", "bark cut", "rubber milk", "morning tapping", "tapping slope", "tapping angle", "girth", "ethrel", "ಟ್ಯಾಪಿಂಗ್", "ಹಾಲು ತೆಗೆ", "ಮರ ಕತ್ತರಿಸು", "ಇಳುವರಿ"]),
    ("FERTILIZER", ["fertilizer", "fartilizer", "furtilizer", "fartiliser", "manure", "compost", "npk", "npkmg", "potash", "urea", "nitrogen", "tree nutrition", "magnesium deficiency", "ಗೊಬ್ಬರ", "ರಸಗೊಬ್ಬರ", "ಪೋಷಕಾಂಶ", "ಪೊಟ್ಯಾಶ್", "ಯೂರಿಯಾ"]),
    ("SPACING", ["spacing", "spasin", "distance", "plant distance", "square planting", "contour planting", "pit size", "pit preparation", "planting season", "budded stumps", "ಅಂತರ", "ನಾಟಿ", "ಗುಂಡಿ", "ಗಿಡ ನೆಡುವುದು"]),
    ("CLONES", ["clone", "clones", "clon", "variety", "varieties", "rrii", "rrii 105", "rrii 414", "rrii 430", "pb 260", "best clone", "high yield clone", "ಕ್ಲೋನ್", "ತಳಿಗಳು", "ಉತ್ತಮ ರಬ್ಬರ್ ತಳಿ"]),
    ("SOIL_CLIMATE", ["soil", "soyl", "laterite", "soil ph", "rainfall", "rain requirement", "climate", "weather", "annual rainfall", "humidity", "temperature", "altitude", "ಮಣ್ಣು", "ಹವಾಮಾನ", "ಮಳೆ", "ಪಿಎಚ್", "ಉಷ್ಣಾಂಶ"]),
    ("IRRIGATION", ["water", "irrigation", "drought", "summer care", "dry season", "moisture", "mulching", "tree basin mulch", "watering saplings", "watering", "ನೀರು", "ನೀರಾವರಿ", "ಬರಗಾಲ", "ಬೇಸಿಗೆ ನಿರ್ವಹಣೆ"]),
    ("RAIN_GUARD", ["rain guard", "rain gard", "polythene apron", "monsoon panel", "tree banding compound", "panel rot", "bark rot", "black stripe", "phytophthora meadii", "ರೇನ್ ಗಾರ್ಡ್", "ಮಳೆ ರಕ್ಷಣೆ", "ಪ್ಯಾನಲ್ ಕೊಳೆತ"]),
    ("WINTERING", ["wintering", "wintring", "natural leaf drop", "annual leaf fall", "yellow leaves shedding", "leaves turning red", "december leaf fall", "annual defoliation", "refoliation", "ಚಳಿಗಾಲದ ಎಲೆ ಉದುರುವಿಕೆ", "ಹಳದಿ ಎಲೆ ಉದುರುವುದು", "ಎಲೆ ಉದುರುವುದು"]),
    ("PINK_DISEASE", ["pink disease", "corticium", "brown bast", "tapping panel dryness", "tpd", "no latex flow", "dry cut", "bark splitting", "stem rot", "branch rot", "ಪಿಂಕ್ ರೋಗ", "ತೊಗಟೆ", "ಹಾಲು ಬಾರದಿರುವುದು"]),
    ("COVER_CROPS", ["weed", "weeding", "grass", "cover crop", "cover crops", "mucuna", "mucuna bracteata", "pueraria", "nitrogen fixation", "glyphosate", "herbicide", "ಕಳೆ", "ಕಳೆ ನಿಯಂತ್ರಣ", "ಹೊದಿಕೆ ಬೆಳೆ"]),
    ("RUBBER_BOARD", ["rubber board", "board", "officer", "helpline", "phone", "contact", "subsidy", "financial assistance", "replanting subsidy", "1800", "ರಬ್ಬರ್ ಬೋರ್ಡ್", "ಸಹಾಯವಾಣಿ", "ಸಬ್ಸಿಡಿ", "ಕಚೇರಿ"]),
    ("DISEASES_LIST", ["what disease", "which disease", "list disease", "can you detect", "supported", "classes", "types of disease", "ಯಾವ ರೋಗ", "ರೋಗಗಳ ಪಟ್ಟಿ", "ಪತ್ತೆಹಚ್ಚುವ ರೋಗಗಳು"]),
    ("APP_GUIDE", ["help", "how to use", "features", "photo tips", "camera guide", "blur image", "clear photo", "scan leaf", "export pdf", "how app works", "ಸಹಾಯ", "ಆ್ಯಪ್ ಬಳಕೆ", "ಫೋಟೋ ಸಲಹೆ"]),
    ("ANTHRACNOSE", ["anthracnose", "antracnos", "antracose", "colletotrichum", "shot hole", "ಆಂಥ್ರಾಕ್ನೋಸ್", "ಆಂಥ್ರ್ಯಾಕ್ನೋಸ್"]),
    ("POWDERY_MILDEW", ["powdery mildew", "mildew", "mildw", "oidium", "white powder", "sulfur dust", "ಬೂದಿ ರೋಗ", "ಬಿಳಿ ಬೂದಿ"]),
    ("LEAF_BLIGHT", ["leaf blight", "blight", "blite", "fusicladium", "ಕರಕಲು", "ಎಲೆ ಕರಕಲು"]),
    ("LEAF_SPOT", ["leaf spot", "corynespora", "railway track", "ಎಲೆ ಚುಕ್ಕೆ"]),
    ("ABNORMAL_FALL", ["abnormal", "phytophthora", "abnormal leaf fall", "leaf fall", "rot", "ಅಸಹಜ", "ಕೊಳೆರೋಗ"]),
    ("BLACK_SPOT", ["black spot", "bird's eye", "birds eye", "helminthosporium", "ಕಪ್ಪು ಚುಕ್ಕೆ", "ಹಕ್ಕಿ ಕಣ್ಣು"]),
    ("DRY_LEAF", ["dry leaf", "sunburn", "water deficit", "parchment", "scorch", "ಒಣಗಿದ ಎಲೆ", "ಬಿಸಿಲು ರೋಗ"]),
    ("HEALTHY_LEAF", ["healthy", "vigorous", "normal leaf", "ಆರೋಗ್ಯಕರ", "ಉತ್ತಮ ಎಲೆ"])
]

GENERIC_DOMAIN_WORDS = {
    "leaf", "leaves", "rubber", "tree", "plant", "crop", "disease",
    "rubber tree", "rubber leaf", "leaf disease", "plant disease",
    "help", "guide", "info",
    "ಎಲೆ", "ರಬ್ಬರ್", "ಮರ", "ಗಿಡ", "ರೋಗ", "ರಬ್ಬರ್ ಮರ", "ರಬ್ಬರ್ ಎಲೆ"
}

def get_chatbot_reply(user_msg, last_scan_disease, last_scan_severity, is_kannada):
    query = user_msg.strip()
    clean_query = re.sub(r'[^\w\s]', '', query.lower()).strip()
    
    # 0. Intercept generic single domain words
    if clean_query in GENERIC_DOMAIN_WORDS:
        if is_kannada:
            return ("🌱 **ರಬ್ಬರ್ ಎಲೆ ಸಹಾಯಕ:**\n\n"
                    "ರಬ್ಬರ್ ಎಲೆಯ ಬಗ್ಗೆ ನೀವು ಏನು ತಿಳಿಯಲು ಬಯಸುತ್ತೀರಿ?\n"
                    "• **ಸ್ಕ್ಯಾನ್ ಮಾಡಿ:** ರೋಗ ಪತ್ತೆ ಮತ್ತು ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ಹೀಟ್‌ಮ್ಯಾಪ್ ತಪಾಸಣೆಗಾಗಿ ಮೇಲಿನ **Scan** ಆಯ್ಕೆ ಬಳಸಿ.\n"
                    "• **ಸಾಮಾನ್ಯ ರೋಗಗಳು:** *ಬೂದಿ ರೋಗ, ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ, ಎಲೆ ಚುಕ್ಕೆ, ಆಂಥ್ರಾಕ್ನೋಸ್, ಅಥವಾ ಎಲೆ ಕರಕಲು* ಬಗ್ಗೆ ವಿವರ ಕೇಳಿ.\n"
                    "• **ಚಳಿಗಾಲದ ಎಲೆ ಉದುರುವಿಕೆ:** *ವಿಂಟರಿಂಗ್ (Wintering)* ಬಗ್ಗೆ ಕೇಳಿ.\n"
                    "• **ಪೋಷಕಾಂಶಗಳು:** *ರಸಗೊಬ್ಬರ (NPK/ಮೆಗ್ನೀಸಿಯಮ್) ಕೊರತೆ* ಬಗ್ಗೆ ಕೇಳಿ.")
        else:
            return ("🌱 **Rubber Leaf Assistant:**\n\n"
                    "What would you like to know about rubber leaves?\n"
                    "• **Scan & Identify:** Upload or capture a leaf photo above for instant AI diagnosis and Grad-CAM visual heatmaps.\n"
                    "• **Common Leaf Diseases:** Ask about *Powdery Mildew, Abnormal Leaf Fall, Leaf Spot (Corynespora), Anthracnose, or Leaf Blight*.\n"
                    "• **Seasonal Shedding:** Ask about *Wintering (annual natural leaf drop)*.\n"
                    "• **Nutrition:** Ask about *fertilizer (NPK/Magnesium) deficiency symptoms*.")
    
    # Best matching topic via fuzzy NLP scoring
    best_topic = None
    best_score = 0.0
    for topic, aliases in CHATBOT_TOPIC_ALIASES:
        score = _calc_match_score(query, aliases)
        if score > best_score:
            best_score = score
            best_topic = topic
            
    # Context fallback: check if asking about latest scan
    if best_score < 8.0 and last_scan_disease:
        q_low = query.lower()
        is_treat = any(w in q_low for w in ["treat", "cure", "spray", "medicine", "fungicide", "ಚಿಕಿತ್ಸೆ", "ಔಷಧ"])
        is_sym = any(w in q_low for w in ["symptom", "cause", "why", "detail", "ಲಕ್ಷಣ", "ಕಾರಣ"])
        is_fert = any(w in q_low for w in ["fertilizer", "npk", "feed", "ಗೊಬ್ಬರ"])
        
        if is_treat or is_sym or is_fert:
            lang_key = "kn" if is_kannada else "en"
            rec = RECOMMENDATIONS.get(last_scan_disease, {}).get(lang_key, None)
            if rec:
                if is_kannada:
                    return (f"**ಇತ್ತೀಚಿನ ಸ್ಕ್ಯಾನ್ ({rec['name']}):**\n\n"
                            f"🍀 **ಚಿಕಿತ್ಸೆ:** {rec['chemical']}\n\n"
                            f"🌾 **ಗೊಬ್ಬರ:** {rec['fertilizer']}\n\n"
                            f"⏱️ **ಚೇತರಿಕೆ:** {rec['recovery']}")
                else:
                    return (f"**Latest Scan Advice ({rec['name']}):**\n\n"
                            f"🍀 **Chemical Treatment:** {rec['chemical']}\n\n"
                            f"🌾 **Fertilizer:** {rec['fertilizer']}\n\n"
                            f"⏱️ **Recovery Period:** {rec['recovery']}")
                            
    if best_score >= 8.0 and best_topic:
        if best_topic == "GREETING":
            return ("ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ರಬ್ಬರ್ ಗಾರ್ಡ್ ಕೃಷಿ ಚಾಟ್‌ಬಾಟ್. ರಬ್ಬರ್ ಮರದ ರೋಗಗಳು, ಬೋರ್ಡೋ ಮಿಶ್ರಣ, ಟ್ಯಾಪಿಂಗ್, ಗೊಬ್ಬರ, ಕ್ಲೋನ್, ಅಥವಾ ಮಣ್ಣಿನ ನಿರ್ವಹಣೆಯ ಬಗ್ಗೆ ಏನು ಬೇಕಾದರೂ ಕೇಳಿ."
                    if is_kannada else
                    "Hello! I am your RubberGuard Agricultural Assistant. Ask me anything about rubber tree diseases, 1% Bordeaux mixture, tapping guidelines, NPK fertilizer schedules, clones, spacing, or soil care.")
                    
        elif best_topic == "BORDEAUX":
            return ("**1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ (Bordeaux Mixture) ತಯಾರಿಸುವ ವಿಧಾನ:**\n\n"
                    "• **ಸಾಮಗ್ರಿಗಳು:** 1 ಕೆಜಿ ತಾಮ್ರದ ಸಲ್ಫೇಟ್ (ಮೈಲುತುತ್ತು) + 1 ಕೆಜಿ ಸುಣ್ಣ (Quicklime) + 100 ಲೀಟರ್ ನೀರು.\n"
                    "• **ತಯಾರಿಕೆ:** 1 ಕೆಜಿ ಮೈಲುತುತ್ತನ್ನು 50 ಲೀಟರ್ ನೀರಿನಲ್ಲಿ ಪ್ಲಾಸ್ಟಿಕ್ ಪಾತ್ರೆಯಲ್ಲಿ ಕರಗಿಸಿ. ಇನ್ನೊಂದು ಪಾತ್ರೆಯಲ್ಲಿ 1 ಕೆಜಿ ಸುಣ್ಣವನ್ನು 50 ಲೀಟರ್ ನೀರಿನಲ್ಲಿ ಕರಗಿಸಿ. ನಂತರ ಮೈಲುತುತ್ತಿನ ದ್ರಾವಣವನ್ನು ಸುಣ್ಣದ ದ್ರಾವಣಕ್ಕೆ ನಿಧಾನವಾಗಿ ಸುರಿದು ಕಲಕಿ.\n"
                    "• **ಚಾಕು ಪರೀಕ್ಷೆ (Knife Test):** ಕ್ಲೀನ್ ಕಬ್ಬಿಣದ ಚಾಕುವನ್ನು 1 ನಿಮಿಷ ಅದ್ದಿ ತೆಗೆಯಿರಿ. ತಾಮ್ರದ ಕಂದು ಬಣ್ಣದ ಲೇಪನ ಬರಬಾರದು.\n"
                    "• **ಬಳಕೆ:** ಮಳೆಗಾಲದ ಆರಂಭಕ್ಕೆ ಮುನ್ನ (ಮೇ ತಿಂಗಳಲ್ಲಿ) ಸಿಂಪಡಿಸಿದರೆ ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ ಮತ್ತು ಕೊಳೆ ರೋಗವನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ತಡೆಗಟ್ಟಬಹುದು."
                    if is_kannada else
                    "**Preparation of 1% Bordeaux Mixture (Standard Rubber Prophylactic):**\n\n"
                    "• **Ingredients:** 1 kg Copper Sulphate (Bluestone) + 1 kg Quicklime + 100 Litres of Water.\n"
                    "• **Procedure:** Dissolve 1 kg Copper Sulphate in 50 L water in a plastic or wooden vessel. Slake 1 kg quicklime in another vessel and dilute with 50 L water. Slowly pour the copper sulphate solution into the lime suspension while stirring continuously.\n"
                    "• **Knife Test:** Dip a polished iron knife blade for 1 minute; if it forms a reddish copper deposit, add more lime suspension until neutral.\n"
                    "• **Timing:** Spray thoroughly over the foliage before monsoon (May) to prevent Abnormal Leaf Fall (*Phytophthora*).")
                    
        elif best_topic == "TAPPING":
            return ("**ರಬ್ಬರ್ ಟ್ಯಾಪಿಂಗ್ (Latex Harvesting) ಮಾರ್ಗಸೂಚಿಗಳು:**\n\n"
                    "• **ಪ್ರಾರಂಭದ ಅಳತೆ:** ಮರದ ಕಾಂಡದ ಸುತ್ತಳತೆ 125 ಸೆಂ.ಮೀ ಎತ್ತರದಲ್ಲಿ ಕನಿಷ್ಠ 50 ಸೆಂ.ಮೀ ಇರಬೇಕು.\n"
                    "• **ಸಮಯ:** ಮುಂಜಾನೆ 6:00 ರಿಂದ 8:00 ಗಂಟೆಯೊಳಗೆ ಟ್ಯಾಪಿಂಗ್ ಮಾಡುವುದು ಅತ್ಯುತ್ತಮ (ಹೆಚ್ಚಿನ ಹಾಲು ಮತ್ತು ಇಳುವರಿ).\n"
                    "• **ಕೋನ ಮತ್ತು ಇಳಿಜಾರು:** ಎಡದಿಂದ ಬಲಕ್ಕೆ 30° ಇಳಿಜಾರಿನಲ್ಲಿ ಕತ್ತರಿಸಿ.\n"
                    "• **ಆಳ:** ಮರದ ಕ್ಯಾಂಬಿಯಂ ಪದರದಿಂದ 1.0 ರಿಂದ 1.5 ಮಿ.ಮೀ ಅಂತರದಲ್ಲಿರಬೇಕು (ಕಾಂಡಕ್ಕೆ ಗಾಯವಾಗಬಾರದು).\n"
                    "• **ವಿಧಾನ:** d/2 (ದಿನ ಬಿಟ್ಟು ದಿನ) ಅಥವಾ d/3 (ಮೂರು ದಿನಕ್ಕೊಮ್ಮೆ).\n"
                    "• **ಇಳುವರಿ ಪ್ರಚೋದಕ:** ಎಥ್ರೆಲ್ (2.5% Ethrel) ಅನ್ನು ವರ್ಷಕ್ಕೆ 3-4 ಬಾರಿ ಕತ್ತರಿಸಿದ ಜಾಗಕ್ಕೆ ಸವರಬಹುದು."
                    if is_kannada else
                    "**Rubber Tapping & Latex Harvesting Best Practices:**\n\n"
                    "• **Opening Standards:** Trees are ready when girth reaches 50 cm at 125 cm height from bud union.\n"
                    "• **Timing:** Early morning (6:00 AM – 8:00 AM) when latex turgor pressure is peak for highest yield.\n"
                    "• **Slope & Angle:** 30° slope from high-left to low-right.\n"
                    "• **Depth:** 1.0 to 1.5 mm distance from the cambium layer. Never gouge the underlying wood.\n"
                    "• **Frequency:** Alternate daily (d/2) or third-daily (d/3) tapping systems.\n"
                    "• **Yield Stimulant:** Apply 2.5% Ethrel brush formulation on the tapping cut 3–4 times annually to stimulate flow in mature trees.")
                    
        elif best_topic == "FERTILIZER":
            return ("**ರಬ್ಬರ್ ಮರಗಳಿಗೆ ಶಿಫಾರಸು ಮಾಡಿದ ರಸಗೊಬ್ಬರ ವೇಳಾಪಟ್ಟಿ:**\n\n"
                    "• **1ನೇ ವರ್ಷ (ಸಸಿಗಳು):** 10:10:4:1.5 NPKMg ಮಿಶ್ರಣವನ್ನು ಗಿಡಕ್ಕೆ 100 ಗ್ರಾಂ ನೀಡಿ.\n"
                    "• **2 ರಿಂದ 4ನೇ ವರ್ಷ (ಬೆಳೆಯುವ ಮರಗಳು):** 10:10:4:1.5 NPKMg ಮಿಶ್ರಣವನ್ನು ವರ್ಷಕ್ಕೆ 400 ಗ್ರಾಂ ನೀಡಿ (ಮೇ ಮತ್ತು ಸೆಪ್ಟೆಂಬರ್ ತಿಂಗಳಲ್ಲಿ).\n"
                    "• **ಟ್ಯಾಪಿಂಗ್ ಮರಗಳು (ಇಳುವರಿ ಹಂತ):** ಪ್ರತಿ ಮರಕ್ಕೆ 400-500 ಗ್ರಾಂ 10:10:10 ಅಥವಾ 12:12:12 NPK ಸಮತೋಲಿತ ಮಿಶ್ರಣವನ್ನು ಮೇ ಮತ್ತು ಸೆಪ್ಟೆಂಬರ್‌ನಲ್ಲಿ ಎರಡು ಕಂತುಗಳಲ್ಲಿ ನೀಡಿ.\n"
                    "• **ಮೆಗ್ನೀಸಿಯಮ್ ಕೊರತೆ:** ಎಲೆಗಳ ನರಗಳ ನಡುವೆ ಹಳದಿ ಬಣ್ಣ ಕಂಡುಬಂದರೆ 1% ಮೆಗ್ನೀಸಿಯಮ್ ಸಲ್ಫೇಟ್ ಸಿಂಪಡಿಸಿ."
                    if is_kannada else
                    "**Standard NPK Fertilizer Schedule for Rubber Plantations:**\n\n"
                    "• **Year 1 (Saplings):** Apply 10:10:4:1.5 NPKMg mixture @ 100–120 g per plant.\n"
                    "• **Years 2–4 (Immature Trees):** Apply 10:10:4:1.5 NPKMg mixture @ 400 g per tree in two split doses (May–June & Sept–Oct).\n"
                    "• **Mature Tapping Trees:** Apply 400–500 g per tree of 10:10:10 or 12:12:12 NPK grade in split applications (pre-monsoon and post-monsoon).\n"
                    "• **Potassium Importance:** Additional MOP builds thick leaf cuticles against fungal defoliation.")
                    
        elif best_topic == "SPACING":
            return ("**ರಬ್ಬರ್ ನಾಟಿ ಮತ್ತು ಅಂತರದ ವಿವರಗಳು (Spacing & Planting):**\n\n"
                    "• **ಸಮತಟ್ಟಾದ ಜಮೀನು:** 4.9 ಮೀ × 4.9 ಮೀ ಚೌಕ ಪದ್ಧತಿ (ಪ್ರತಿ ಎಕರೆಗೆ ಸುಮಾರು 180–200 ಮರಗಳು).\n"
                    "• **ಗುಡ್ಡಗಾಡು / ಇಳಿಜಾರು ಜಮೀನು:** 6.7 ಮೀ × 3.4 ಮೀ ಕಾಂಟೂರ್ ಪದ್ಧತಿ (ಪ್ರತಿ ಎಕರೆಗೆ ಸುಮಾರು 180 ಮರಗಳು).\n"
                    "• **ಗುಂಡಿಯ ಅಳತೆ:** 75 ಸೆಂ.ಮೀ × 75 ಸೆಂ.ಮೀ × 75 ಸೆಂ.ಮೀ.\n"
                    "• **ಗುಂಡಿ ತುಂಬುವುದು:** ಮೇಲ್ಮಣ್ಣು + 12 ಕೆಜಿ ಕಳಿತ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ + 200 ಗ್ರಾಂ ರಾಕ್ ಫಾಸ್ಫೇಟ್.\n"
                    "• **ಉತ್ತಮ ಕಾಲ:** ನೈಋತ್ಯ ಮಾನ್ಸೂನ್ ಪ್ರಾರಂಭವಾಗುವ ಮೇ–ಜುಲೈ ತಿಂಗಳು."
                    if is_kannada else
                    "**Planting Spacing & Pit Preparation:**\n\n"
                    "• **Flat / Level Land:** 4.9 m × 4.9 m square system (approx. 200 trees/acre or 500 trees/ha).\n"
                    "• **Hilly / Contour Slopes:** 6.7 m × 3.4 m contour planting.\n"
                    "• **Pit Dimensions:** 75 cm × 75 cm × 75 cm.\n"
                    "• **Pit Filling:** Topsoil mixed with 10–12 kg well-rotted farmyard manure and 200 g rock phosphate.\n"
                    "• **Planting Window:** May to July with the onset of the South-West monsoon for optimal root establishment.")
                    
        elif best_topic == "CLONES":
            return ("**ಕರ್ನಾಟಕ ಮತ್ತು ಕೇರಳಕ್ಕೆ ಶಿಫಾರಸು ಮಾಡಿದ ರಬ್ಬರ್ ತಳಿಗಳು (Clones):**\n\n"
                    "• **RRII 105:** ಅತ್ಯಂತ ಜನಪ್ರಿಯ ಹಾಗೂ ಗರಿಷ್ಠ ಇಳುವರಿ ನೀಡುವ ತಳಿ (ಕರ್ನಾಟಕದ ಕರಾವಳಿ ಮತ್ತು ಮಲೆನಾಡಿಗೆ ಸೂಕ್ತ).\n"
                    "• **RRII 414 / RRII 430:** ಗಾಳಿಗೆ ಮುರಿಯದ ಗಟ್ಟಿ ಮರ ಮತ್ತು ಶಿಲೀಂಧ್ರ ರೋಗಗಳಿಗೆ ಉತ್ತಮ ನಿರೋಧಕತೆ ಹೊಂದಿರುವ ಆಧುನಿಕ ತಳಿಗಳು.\n"
                    "• **PB 260:** ಬೇಗನೆ ಟ್ಯಾಪಿಂಗ್ ಹಂತಕ್ಕೆ ಬರುವ ತಳಿ, ಆದರೆ ಬಿರುಗಾಳಿಗೆ ಕೊಂಚ ಸಂವೇದನಶೀಲ.\n"
                    "• **RRIM 600:** ಉತ್ತಮ ಬೆಳವಣಿಗೆ ಮತ್ತು ಇಳುವರಿ ಹೊಂದಿರುವ ತಳಿ."
                    if is_kannada else
                    "**Recommended High-Yielding Rubber Clones for South India:**\n\n"
                    "• **RRII 105:** The benchmark high-yield clone in Karnataka and Kerala; produces peak latex yield under good management.\n"
                    "• **RRII 414 & RRII 430:** Modern fast-growing clones featuring strong wind resistance and superior tolerance to Corynespora and Powdery Mildew.\n"
                    "• **PB 260:** Early maturing with high initial yields; requires wind-protected valley planting.\n"
                    "• **RRIM 600:** Hardy clone with consistent latex yield across various soil conditions.")
                    
        elif best_topic == "SOIL_CLIMATE":
            return ("**ರಬ್ಬರ್ ಕೃಷಿಗೆ ಸೂಕ್ತ ಮಣ್ಣು ಮತ್ತು ಹವಾಮಾನ:**\n\n"
                    "• **ಮಣ್ಣು:** ಕನಿಷ್ಠ 1 ಮೀಟರ್ ಆಳವಿರುವ ಉತ್ತಮ ಬಸಿದುಹೋಗುವ ಜಂಬಿಟ್ಟಿಗೆ (Laterite) ಅಥವಾ ಕೆಂಪು ಗೋಡು ಮಣ್ಣು.\n"
                    "• **ಮಣ್ಣಿನ ಪಿಎಚ್ (pH):** 4.5 ರಿಂದ 6.0 (ಸ್ವಲ್ಪ ಆಮ್ಲೀಯ ಮಣ್ಣು ರಬ್ಬರ್‌ಗೆ ಅತ್ಯುತ್ತಮ).\n"
                    "• **ಮಳೆ ಪ್ರಮಾಣ:** ವಾರ್ಷಿಕ 2000 ರಿಂದ 3000 ಮಿ.ಮೀ ಮಳೆ ಸಮನಾಗಿ ಹಂಚಿಕೆಯಾಗಿರಬೇಕು.\n"
                    "• **ಉಷ್ಣಾಂಶ:** 20°C ನಿಂದ 34°C ಹಾಗೂ ಹೆಚ್ಚಿನ ಆರ್ದ್ರತೆ (80% ಗಿಂತ ಹೆಚ್ಚು).\n"
                    "• **ಸಮುದ್ರ ಮಟ್ಟ:** 500 ಮೀಟರ್ ಒಳಗಿನ ಪ್ರದೇಶಗಳು ಅತ್ಯಂತ ಪ್ರಶಸ್ತ."
                    if is_kannada else
                    "**Soil, Climate & Environmental Requirements:**\n\n"
                    "• **Soil Type:** Deep, well-drained acidic laterite or red loam (minimum effective depth $\\ge 1.0$ meter).\n"
                    "• **Soil pH:** 4.5 to 6.0 is optimal for rubber root uptake.\n"
                    "• **Rainfall:** 2,000 to 3,000 mm annually distributed over 100+ rainy days.\n"
                    "• **Temperature:** 20°C to 34°C with relative humidity $>80\\%$.\n"
                    "• **Elevation:** Below 500 meters above sea level for best vegetative growth and latex production.")
                    
        elif best_topic == "IRRIGATION":
            return ("**ಬೇಸಿಗೆ ನಿರ್ವಹಣೆ ಮತ್ತು ನೀರಾವರಿ (Drought Management):**\n\n"
                    "• **ಮರದ ಬುಡಕ್ಕೆ ಹೊದಿಕೆ (Mulching):** ಬೇಸಿಗೆಯಲ್ಲಿ ಮರದ ಬುಡದ 1 ಮೀಟರ್ ಸುತ್ತಳತೆಯಲ್ಲಿ ಒಣ ಎಲೆಗಳು ಅಥವಾ ತೆಂಗಿನ ತ್ಯಾಜ್ಯದಿಂದ ಹೊದಿಕೆ ಹಾಕಿ ತೇವಾಂಶ ಕಾಪಾಡಿ.\n"
                    "• **ಸಸಿಗಳಿಗೆ ನೀರುಣಿಸುವುದು:** ಸಣ್ಣ ಸಸಿಗಳಿಗೆ ಬೇಸಿಗೆಯಲ್ಲಿ ವಾರಕ್ಕೆ ಒಮ್ಮೆ 10 ಲೀಟರ್ ನೀರು ನೀಡುವುದು ಉತ್ತಮ.\n"
                    "• **ಬಿಸಿಲಿನ ರಕ್ಷಣೆ:** ಸಣ್ಣ ಗಿಡಗಳ ಕಾಂಡಕ್ಕೆ ಸುಣ್ಣ (Lime wash) ಹಚ್ಚಿ ಬಿಸಿಲ ಬೇಗೆಯಿಂದ ಬಿರುಕು ಬಿಡುವುದನ್ನು ತಪ್ಪಿಸಿ."
                    if is_kannada else
                    "**Water Stress, Drought & Irrigation Management:**\n\n"
                    "• **Basin Mulching:** Mulch tree basins up to 1-meter radius with dry leaves or coir pith before summer to conserve soil moisture.\n"
                    "• **Sapling Watering:** Young plants benefit from 10 L water weekly during severe summer dry spells.\n"
                    "• **Sun Scorch Protection:** Whitewash the trunks of young trees with dilute lime suspension to prevent sun cracking.\n"
                    "• **Water Stress Relief:** Foliar spray of 1% Potassium Chloride (KCl) helps foliage maintain water turgidity.")
                    
        elif best_topic == "RAIN_GUARD":
            return ("**ಮಳೆ ರಕ್ಷಣೆ (Rain Guarding) ಮತ್ತು ಪ್ಯಾನಲ್ ನಿರ್ವಹಣೆ:**\n\n"
                    "• **ರೇನ್ ಗಾರ್ಡ್ ಹಾಕುವುದು:** ಮಾನ್ಸೂನ್ ಮಳೆ ಆರಂಭವಾಗುವ ಮುನ್ನ (ಮೇ ತಿಂಗಳಲ್ಲಿ) ಟ್ಯಾಪಿಂಗ್ ಕಟ್‌ಗಿಂತ 8 ಸೆಂ.ಮೀ ಎತ್ತರದಲ್ಲಿ ಪಾಲಿಥಿನ್ ಶೀಟ್ ಅನ್ನು ರಬ್ಬರ್ ಬ್ಯಾಂಡಿಂಗ್ ಪೇಸ್ಟ್ ಬಳಸಿ ಅಂಟಿಸಿ.\n"
                    "• **ಲಾಭ:** ಮಳೆಗಾಲದಲ್ಲೂ ಹಾಲಿನ ನಷ್ಟವಿಲ್ಲದೆ ನಿರಂತರವಾಗಿ ಟ್ಯಾಪಿಂಗ್ ಮಾಡಬಹುದು.\n"
                    "• **ಪ್ಯಾನಲ್ ಕೊಳೆತ ತಡೆ:** ಮಳೆಗಾಲದಲ್ಲಿ ಟ್ಯಾಪಿಂಗ್ ಪ್ಯಾನಲ್‌ಗೆ 0.2% ಮ್ಯಾಂಕೋಜೆಬ್ ಅಥವಾ ಕಾಪರ್ ಪೇಸ್ಟ್ ಹಚ್ಚಿ ರಕ್ಷಿಸಿ."
                    if is_kannada else
                    "**Rain Guarding & Monsoon Panel Protection:**\n\n"
                    "• **Application:** Fix polythene aprons around the tree trunk 8 cm above the tapping cut using tree-banding compound before monsoon rains start.\n"
                    "• **Benefits:** Prevents latex wash-out, allowing 30–40 additional tapping days during monsoon months.\n"
                    "• **Bark Rot Prevention:** Apply Copper Oxychloride (0.2%) or Mancozeb paste weekly to the tapping cut to prevent Black Stripe (*Phytophthora meadii*) bark decay.")
                    
        elif best_topic == "WINTERING":
            return ("**ಚಳಿಗಾಲದ ಎಲೆ ಉದುರುವಿಕೆ (Wintering Phenomenon):**\n\n"
                    "• **ನೈಸರ್ಗಿಕ ಪ್ರಕ್ರಿಯೆ:** ಡಿಸೆಂಬರ್‌ನಿಂದ ಫೆಬ್ರವರಿ ತಿಂಗಳಲ್ಲಿ ರಬ್ಬರ್ ಎಲೆಗಳು ಹಳದಿ ಮತ್ತು ಕಂದು ಬಣ್ಣಕ್ಕೆ ತಿರುಗಿ ಉದುರುವುದು ನೈಸರ್ಗಿಕ ಲಕ್ಷಣ (ವಿಂಟರಿಂಗ್).\n"
                    "• **ಹೊಸ ಚಿಗುರು:** ಫೆಬ್ರವರಿ-ಮಾರ್ಚ್‌ನಲ್ಲಿ ಬರುವ ಹೊಸ ಎಲೆಗಳಿಗೆ ಬೂದಿ ರೋಗ (Powdery Mildew) ತಗುಲುವ ಸಾಧ್ಯತೆ ಹೆಚ್ಚು.\n"
                    "• **ಮುನ್ನೆಚ್ಚರಿಕೆ:** ಹೊಸ ಚಿಗುರು ಬಂದ ತಕ್ಷಣ ಗಂಧಕದ ಪುಡಿ (Sulphur dust) ಧೂಳೀಕರಣ ಮಾಡಿ."
                    if is_kannada else
                    "**Wintering (Annual Defoliation & Refoliation):**\n\n"
                    "• **Natural Physiological Cycle:** Rubber trees naturally drop their leaves from December to February. Leaves turn yellow or copper-red before shedding.\n"
                    "• **Refoliation Season:** Tender new copper-green foliage emerges in February–March.\n"
                    "• **Critical Advisory:** Young tender flush is highly vulnerable to **Powdery Mildew** (*Oidium heveae*). Dust fine elemental sulphur (12–15 kg/ha) early in the morning during refoliation.")
                    
        elif best_topic == "PINK_DISEASE":
            return ("**ಪಿಂಕ್ ರೋಗ (Pink Disease) ಮತ್ತು ಬ್ರೌನ್ ಬಾಸ್ಟ್ (TPD):**\n\n"
                    "• **ಪಿಂಕ್ ರೋಗ ಲಕ್ಷಣ:** ಮರದ ಕವಲುಗಳಲ್ಲಿ ಬಿಳಿ ಅಥವಾ ಗುಲಾಬಿ ಬಣ್ಣದ ಶಿಲೀಂಧ್ರ ಜಾಲ ಮತ್ತು ತೊಗಟೆ ಸೀಳುವುದು.\n"
                    "• **ಪಿಂಕ್ ರೋಗ ಚಿಕಿತ್ಸೆ:** ಸೋಂಕಿತ ಜಾಗವನ್ನು ಕೆರೆದು ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಅಥವಾ ಥೈರಮ್ (0.5%) ಹಚ್ಚಿ.\n"
                    "• **ಬ್ರೌನ್ ಬಾಸ್ಟ್ (ಹಾಲು ಬಾರದಿರುವುದು):** ಅತಿಯಾಗಿ ಟ್ಯಾಪಿಂಗ್ ಮಾಡುವುದರಿಂದ ಉಂಟಾಗುತ್ತದೆ; ಮರಕ್ಕೆ 3-6 ತಿಂಗಳು ವಿಶ್ರಾಂತಿ ನೀಡಿ ಟ್ಯಾಪಿಂಗ್ ನಿಲ್ಲಿಸಿ."
                    if is_kannada else
                    "**Pink Disease (*Corticium*) & Tapping Panel Dryness (TPD):**\n\n"
                    "• **Pink Disease:** Attacks tree fork crotches, showing white/pink cobweb fungus followed by bark splitting and latex bleeding. Scrape the lesion and apply Bordeaux Paste (1 kg copper sulphate + 2 kg lime in 10 L water).\n"
                    "• **Tapping Panel Dryness (Brown Bast):** Total cessation of latex flow caused by over-tapping or excessive stimulant use. Rest the tree for 3–6 months, reduce tapping intensity to d/3, and cease Ethrel usage.")
                    
        elif best_topic == "COVER_CROPS":
            return ("**ಹೊದಿಕೆ ಬೆಳೆಗಳು ಮತ್ತು ಕಳೆ ನಿಯಂತ್ರಣ (Cover Crops & Weeding):**\n\n"
                    "• **ಉತ್ತಮ ಹೊದಿಕೆ ಬೆಳೆ:** *ಮುಕುನಾ ಬ್ರ್ಯಾಕ್ಟಿಯೇಟಾ (Mucuna bracteata)* - ಇದು ಕಳೆಗಳನ್ನು ಹತ್ತಿಕ್ಕುತ್ತದೆ, ಮಣ್ಣಿಗೆ ಸಾರಜನಕ ಒದಗಿಸುತ್ತದೆ ಮತ್ತು ತೇವಾಂಶ ಕಾಪಾಡುತ್ತದೆ.\n"
                    "• **ರಾಸಾಯನಿಕ ಕಳೆನಾಶಕ:** ಸಾಲುಗಳ ನಡುವಿನ ಕಳೆಗಳಿಗೆ 1% ಗ್ಲೈಫೋಸೇಟ್ (Glyphosate 41% SL) ಸಿಂಪಡಿಸಿ."
                    if is_kannada else
                    "**Cover Crops & Weed Control:**\n\n"
                    "• **Recommended Cover Crop:** *Mucuna bracteata* or *Pueraria phaseoloides*. Smothers aggressive weeds, fixes over 100 kg Nitrogen/ha, and adds organic leaf mulch.\n"
                    "• **Chemical Weeding:** Spray Glyphosate 41% SL (1 to 1.5 L/ha) for perennial grasses in inter-rows, ensuring spray does not drift onto green rubber bark.")
                    
        elif best_topic == "RUBBER_BOARD":
            return ("**ರಬ್ಬರ್ ಬೋರ್ಡ್ ಸಂಪರ್ಕ ಮತ್ತು ಸಬ್ಸಿಡಿ ಮಾಹಿತಿ:**\n\n"
                    "• **ಟೋಲ್-ಫ್ರೀ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್:** 1800-425-5522 (ಸೋಮವಾರದಿಂದ ಶುಕ್ರವಾರ ಬೆಳಿಗ್ಗೆ 9:30 ರಿಂದ ಸಂಜೆ 5:30).\n"
                    "• **ಕರ್ನಾಟಕ ಪ್ರಾದೇಶಿಕ ಕಚೇರಿಗಳು:** ಮಂಗಳೂರು, ಪುತ್ತೂರು, ಬೆಳ್ತಂಗಡಿ, ಸುಳ್ಯ, ಶಿವಮೊಗ್ಗ.\n"
                    "• **ಸಬ್ಸಿಡಿಗಳು:** ಹೊಸ ತೋಟ ನಾಟಿ ಸಹಾಯಧನ, ರೇನ್ ಗಾರ್ಡ್ ಸಬ್ಸಿಡಿ ಮತ್ತು ಯಂತ್ರೋಪಕರಣ ನೆರವು ಲಭ್ಯವಿದೆ.\n"
                    "• **ವೆಬ್‌ಸೈಟ್:** rubberboard.gov.in"
                    if is_kannada else
                    "**Rubber Board of India Advisory & Helpline:**\n\n"
                    "• **Kisan Call Center Toll-Free:** 1800-425-5522 (Mon–Fri, 9:30 AM to 5:30 PM).\n"
                    "• **Regional Offices (Karnataka):** Mangaluru, Puttur, Belthangady, Sullia, and Shivamogga.\n"
                    "• **Subsidies & Schemes:** Financial replanting assistance per hectare, rain guarding subsidy, and mechanized tapper training programs.\n"
                    "• **Official Portal:** rubberboard.gov.in")
                    
        elif best_topic == "DISEASES_LIST":
            return ("ನಮ್ಮ AI ಸಿಸ್ಟಮ್ ಈ 8 ರೋಗ ಸ್ಥಿತಿಗಳನ್ನು ನಿಖರವಾಗಿ ಪತ್ತೆಹಚ್ಚಬಲ್ಲದು:\n"
                    "1. **ಅಸಹಜ ಎಲೆ ಉದುರುವಿಕೆ** (Abnormal Leaf Fall - *Phytophthora*)\n"
                    "2. **ಆಂಥ್ರಾಕ್ನೋಸ್** (Anthracnose - *Colletotrichum*)\n"
                    "3. **ಕಪ್ಪು ಚುಕ್ಕೆ / ಹಕ್ಕಿ ಕಣ್ಣು** (Black Spot / Bird's Eye)\n"
                    "4. **ಎಲೆ ಕರಕಲು ರೋಗ** (Leaf Blight - *Fusicladium*)\n"
                    "5. **ಎಲೆ ಚುಕ್ಕೆ ರೋಗ** (Leaf Spot - *Corynespora*)\n"
                    "6. **ಬೂದಿ ರೋಗ** (Powdery Mildew - *Oidium*)\n"
                    "7. **ಒಣಗಿದ ಎಲೆ** (Dry Leaf / Sun Scorch)\n"
                    "8. **ಆರೋಗ್ಯಕರ ಎಲೆ** (Healthy Leaf)"
                    if is_kannada else
                    "Our AI model diagnoses the following 8 rubber leaf conditions:\n"
                    "1. **Abnormal Leaf Fall** (*Phytophthora spp.*)\n"
                    "2. **Anthracnose** (*Colletotrichum gloeosporioides*)\n"
                    "3. **Black Spot / Bird's Eye** (*Helminthosporium heveae*)\n"
                    "4. **Leaf Blight** (*Fusicladium macrosporum*)\n"
                    "5. **Leaf Spot** (*Corynespora cassiicola*)\n"
                    "6. **Powdery Mildew** (*Oidium heveae*)\n"
                    "7. **Dry Leaf** (Abiotic / Drought Stress)\n"
                    "8. **Healthy Leaf** (No fungal pathogen)")
                    
        elif best_topic == "APP_GUIDE":
            return ("**ರಬ್ಬರ್ ಗಾರ್ಡ್ ಆ್ಯಪ್ ಬಳಕೆ ಮತ್ತು ಫೋಟೋ ಸಲಹೆ:**\n\n"
                    "• **ಫೋಟೋ ತೆಗೆಯುವುದು:** ಒಂದೇ ಎಲೆಯನ್ನು ಹತ್ತಿರದಿಂದ ಹಿಡಿದು ನೈಸರ್ಗಿಕ ಬೆಳಕಿನಲ್ಲಿ ಸ್ಪಷ್ಟವಾಗಿ ಫೋಟೋ ತೆಗೆಯಿರಿ.\n"
                    "• **Grad-CAM ನಕ್ಷೆ:** ಪತ್ತೆಯಾದ ರೋಗದ ಕೆಂಪು/ಹಳದಿ ಬಣ್ಣದ ತಪಾಸಣಾ ನಕ್ಷೆಯನ್ನು ಗಮನಿಸಿ.\n"
                    "• **ಪಿಡಿಎಫ್ ವರದಿ:** 'Export PDF' ಬಟನ್ ಒತ್ತಿ ಕೃಷಿ ಅಧಿಕಾರಿಗಳಿಗೆ ಅಥವಾ ರಬ್ಬರ್ ಬೋರ್ಡ್‌ಗೆ ವರದಿ ಶೇರ್ ಮಾಡಿ."
                    if is_kannada else
                    "**How to Use RubberGuard for Best Results:**\n\n"
                    "• **Framing:** Place a single rubber leaf centrally against a neutral background in natural daylight.\n"
                    "• **Clarity:** Keep distance 15–25 cm to avoid motion blur.\n"
                    "• **Grad-CAM Saliency:** Switch to the Heatmap tab to verify exactly where the AI detected lesion triggers.\n"
                    "• **PDF Report:** Tap 'Export PDF Report' to generate an A4 summary with severity percentage and agronomic advice.")
                    
        # Individual disease inquiries
        elif best_topic in ["ANTHRACNOSE", "POWDERY_MILDEW", "LEAF_BLIGHT", "LEAF_SPOT", "ABNORMAL_FALL", "BLACK_SPOT", "DRY_LEAF", "HEALTHY_LEAF"]:
            disease_map = {
                "ANTHRACNOSE": "Anthracnose",
                "POWDERY_MILDEW": "Powdery Mildew",
                "LEAF_BLIGHT": "Leaf Blight",
                "LEAF_SPOT": "Leaf Spot",
                "ABNORMAL_FALL": "Abnormal Leaf Fall",
                "BLACK_SPOT": "Black Spot / Bird's Eye",
                "DRY_LEAF": "Dry Leaf",
                "HEALTHY_LEAF": "Healthy"
            }
            d_name = disease_map[best_topic]
            lang_key = "kn" if is_kannada else "en"
            rec = RECOMMENDATIONS.get(d_name, {}).get(lang_key, None)
            if rec:
                if is_kannada:
                    return (f"**{rec['name']} - {rec['description']}**\n\n"
                            f"🔍 **ಪ್ರಮುಖ ಲಕ್ಷಣಗಳು:** {rec['symptoms']}\n\n"
                            f"🍀 **ಸಾವಯವ ಚಿಕಿತ್ಸೆ:** {rec['organic']}\n\n"
                            f"🧪 **ಶಿಲೀಂಧ್ರನಾಶಕ:** {rec['chemical']}\n\n"
                            f"🌾 **ಗೊಬ್ಬರ:** {rec['fertilizer']}\n\n"
                            f"⏱️ **ಚೇತರಿಕೆ ಅವಧಿ:** {rec['recovery']}")
                else:
                    return (f"**{rec['name']} ({rec['pathogen']}):**\n\n"
                            f"📖 **Overview:** {rec['description']}\n\n"
                            f"🔍 **Symptoms:** {rec['symptoms']}\n\n"
                            f"🍀 **Organic Control:** {rec['organic']}\n\n"
                            f"🧪 **Chemical Spray:** {rec['chemical']}\n\n"
                            f"🌾 **Fertilizer:** {rec['fertilizer']}\n\n"
                            f"⏱️ **Recovery Period:** {rec['recovery']}")
                            
    # Default fallback
    if is_kannada:
        return ("ನನಗೆ ಪ್ರಶ್ನೆ ಸ್ಪಷ್ಟವಾಗಲಿಲ್ಲ. ನೀವು ಈ ಕೆಳಗಿನವುಗಳ ಬಗ್ಗೆ ಕೇಳಬಹುದು:\n"
                "• ರೋಗಗಳ ಚಿಕಿತ್ಸೆ (ಉದಾ: 'ಆಂಥ್ರಾಕ್ನೋಸ್ ಚಿಕಿತ್ಸೆ' ಅಥವಾ 'ಬೂದಿ ರೋಗ')\n"
                "• 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ತಯಾರಿಸುವ ವಿಧಾನ\n"
                "• ರಬ್ಬರ್ ಟ್ಯಾಪಿಂಗ್ ಸಮಯ ಮತ್ತು ನಿಯಮಗಳು\n"
                "• ರಸಗೊಬ್ಬರ (NPK) ವೇಳಾಪಟ್ಟಿ\n"
                "• ನಾಟಿ ಅಂತರ ಮತ್ತು ಉತ್ತಮ ಕ್ಲೋನ್‌ಗಳು (RRII 105)\n"
                "• ಮಳೆ ರಕ್ಷಣೆ (ರೇನ್ ಗಾರ್ಡ್) ಮತ್ತು ಚಳಿಗಾಲದ ಎಲೆ ಉದುರುವಿಕೆ\n"
                "• ರಬ್ಬರ್ ಬೋರ್ಡ್ ಸಹಾಯವಾಣಿ: 1800-425-5522")
    else:
        return ("I couldn't quite identify your question. You can ask me about:\n"
                "• Any leaf disease (e.g. *'How to treat Anthracnose'*, *'Powdery Mildew'*, *'Leaf Blight'*)\n"
                "• 1% Bordeaux mixture preparation steps\n"
                "• Rubber tapping timing, angle, depth & rain-guards\n"
                "• Recommended NPK fertilizer schedules\n"
                "• Recommended high-yielding clones (*RRII 105*) & tree spacing\n"
                "• Soil, rainfall requirements & wintering defoliation\n"
                "• Rubber Board helpline: 1800-425-5522")

# ---------------------------------------------------------
# Streamlit Mobile Application Layout (Exact Digital Twin of Android App)
# ---------------------------------------------------------

# Initialize Session State
if "current_screen" not in st.session_state:
    st.session_state.current_screen = "home"
if "scan_source" not in st.session_state:
    st.session_state.scan_source = "camera"
if "total_scans" not in st.session_state:
    st.session_state.total_scans = 0
if "diseased_scans" not in st.session_state:
    st.session_state.diseased_scans = 0
if "healthy_scans" not in st.session_state:
    st.session_state.healthy_scans = 0
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "English"
if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None
if "gradcam_tab" not in st.session_state:
    st.session_state.gradcam_tab = "Grad-CAM Overlay"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "show_severity" not in st.session_state:
    st.session_state.show_severity = False

is_kannada = "ಕನ್ನಡ" in st.session_state.selected_lang

# Mobile Android Authentic Styling
st.markdown("""
<style>
/* Hide Streamlit default UI chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}

/* Android system fonts & background */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,600&display=swap');
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #0E1E11 !important;
}

/* Smartphone phone viewport container */
.main .block-container {
    max-width: 440px !important;
    padding-top: 0.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
    margin: 0 auto !important;
    background: #F4F7F4 !important;
    min-height: 94vh !important;
    border-radius: 28px !important;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.45) !important;
    border: 1px solid #2E5A34 !important;
}

/* Android Status Bar */
.phone-status-bar {
    background: #1B5E20;
    color: #FFFFFF;
    padding: 6px 16px;
    font-size: 11px;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 20px 20px 0 0;
    margin: -0.5rem -0.8rem 10px -0.8rem;
    letter-spacing: 0.5px;
}

/* Toolbar Header */
.phone-toolbar {
    background: #FFFFFF;
    padding: 10px 14px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    margin-bottom: 12px;
    border: 1px solid #E8F5E9;
}
.phone-toolbar-title {
    font-size: 19px;
    font-weight: 800;
    color: #1B5E20;
    letter-spacing: -0.3px;
}

/* Rounded Leaf Image Card */
.phone-image-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 10px;
    box-shadow: 0 3px 14px rgba(0, 0, 0, 0.07);
    border: 1px solid #E0E0E0;
    margin: 10px auto;
    text-align: center;
}
.phone-image-card img {
    border-radius: 16px;
    max-height: 220px;
    width: 100%;
    object-fit: cover;
}

/* Prediction Details Card */
.phone-details-card {
    background: #FFFFFF;
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    border: 1px solid #E0E0E0;
    margin-bottom: 12px;
}
.phone-disease-title {
    font-size: 21px;
    font-weight: 800;
    color: #1B5E20;
}
.phone-badge-diseased {
    background: #C62828;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 11px;
    padding: 5px 12px;
    border-radius: 6px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.phone-badge-healthy {
    background: #2E7D32;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 11px;
    padding: 5px 12px;
    border-radius: 6px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.phone-divider-line {
    height: 1px;
    background: #EEEEEE;
    margin: 12px 0;
}

/* XAI Visual Explanation Card */
.phone-xai-card {
    background: #F1F8F2;
    border-radius: 16px;
    padding: 14px 16px;
    border: 1px solid #D5E8D6;
    margin-top: 14px;
    color: #2E382E;
    font-size: 12px;
    line-height: 1.5;
}
.phone-xai-header {
    font-weight: 800;
    color: #1B5E20;
    margin-bottom: 6px;
    font-size: 14px;
}

/* Chatbot Bubbles */
.chat-bubble-user {
    background: #2E7D32;
    color: #FFFFFF;
    padding: 10px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px auto;
    max-width: 82%;
    font-size: 13.5px;
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(46, 125, 50, 0.25);
    word-wrap: break-word;
}
.chat-bubble-bot {
    background: #FFFFFF;
    color: #212121;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px auto 8px 0;
    max-width: 88%;
    font-size: 13.5px;
    line-height: 1.45;
    border: 1px solid #E0E0E0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    word-wrap: break-word;
}

/* Action Buttons */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.55rem 0.9rem !important;
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Simulated Android Status Bar (Every Screen)
# ---------------------------------------------------------
st.markdown("""
<div class="phone-status-bar">
    <span>9:36</span>
    <div style="display:flex; gap:8px; align-items:center;">
        <span>📶 5G+</span>
        <span>🔋 96%</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SCREEN 1: HOME (Exact match of fragment_home.xml & media_1793030512273.png)
# =========================================================
if st.session_state.current_screen == "home":
    # Top Toolbar
    c_h1, c_h2, c_h3 = st.columns([1, 4, 1])
    with c_h1:
        lang_btn_text = "ಕನ್ನಡ" if st.session_state.selected_lang == "English" else "English"
        if st.button("🌐", key="btn_lang_home", help=f"Switch to {lang_btn_text}"):
            st.session_state.selected_lang = "ಕನ್ನಡ (Kannada)" if st.session_state.selected_lang == "English" else "English"
            st.rerun()
    with c_h2:
        st.markdown("<div style='text-align:center; font-size:20px; font-weight:800; color:#1B5E20; padding-top:4px;'>RubberGuard AI</div>", unsafe_allow_html=True)
    with c_h3:
        if st.button("💬", key="btn_open_chat_top", help="Open RubberGuard Chatbot"):
            st.session_state.current_screen = "chatbot"
            st.rerun()

    # Greeting Banner
    st.markdown(f"""
    <div style="padding: 10px 4px 14px 4px;">
        <div style="font-size:13px; color:#558B2F; font-weight:600;">{"Welcome back," if not is_kannada else "ಸುಸ್ವಾಗತ,"}</div>
        <div style="font-size:24px; font-weight:800; color:#1B5E20; line-height:1.2;">{"Farmer Guest" if not is_kannada else "ರೈತ ಮಿತ್ರ"}</div>
    </div>
    """, unsafe_allow_html=True)

    # Hero Scan Card (matching Android card gradient)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #1B5E20 0%, #2E7D32 55%, #388E3C 100%); border-radius:20px; padding:18px 20px; color:#FFFFFF; box-shadow:0 8px 24px rgba(27,94,32,0.25); margin-bottom:14px;">
        <div style="font-size:18px; font-weight:800; margin-bottom:4px;">{"Instant Leaf Disease Scan" if not is_kannada else "ತಕ್ಷಣದ ಎಲೆ ರೋಗ ತಪಾಸಣೆ"}</div>
        <div style="font-size:12px; color:#E8F5E9; line-height:1.4;">{"AI camera identifies fungal infections, calculates disease severity, and pinpoints lesion spots with Grad-CAM." if not is_kannada else "ಕ್ಯಾಮರಾದಿಂದ ಎಲೆಯನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ, ರೋಗ ಪತ್ತೆಹಚ್ಚಿ ಮತ್ತು ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ನಕ್ಷೆ ವೀಕ್ಷಿಸಿ."}</div>
    </div>
    """, unsafe_allow_html=True)

    # Big Action Scan Buttons
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("📷 " + ("Take Photo" if not is_kannada else "ಕ್ಯಾಮರಾ ಫೋಟೋ"), type="primary", use_container_width=True):
            st.session_state.scan_source = "camera"
            st.session_state.current_screen = "scan"
            st.rerun()
    with c_btn2:
        if st.button("📁 " + ("Upload Leaf" if not is_kannada else "ಚಿತ್ರ ಅಪ್‌ಲೋಡ್"), use_container_width=True):
            st.session_state.scan_source = "upload"
            st.session_state.current_screen = "scan"
            st.rerun()

    # Statistics Card (matching Android statistics layout)
    st.markdown(f"""
    <div style="background:#FFFFFF; border-radius:18px; padding:16px 18px; box-shadow:0 2px 12px rgba(0,0,0,0.05); border:1px solid #E0E0E0; margin: 14px 0;">
        <div style="font-size:13px; font-weight:700; color:#212121; margin-bottom:10px;">{"Diagnostic Statistics" if not is_kannada else "ತಪಾಸಣಾ ವಿವರ"}</div>
        <div style="display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;">
                <div style="font-size:22px; font-weight:800; color:#1B5E20;">{st.session_state.total_scans}</div>
                <div style="font-size:10px; font-weight:600; color:#757575;">{"TOTAL SCANS" if not is_kannada else "ಒಟ್ಟು"}</div>
            </div>
            <div style="width:1px; height:30px; background:#E0E0E0;"></div>
            <div style="text-align:center;">
                <div style="font-size:22px; font-weight:800; color:#D32F2F;">{st.session_state.diseased_scans}</div>
                <div style="font-size:10px; font-weight:600; color:#757575;">{"DISEASED" if not is_kannada else "ರೋಗ ಬಾಧಿತ"}</div>
            </div>
            <div style="width:1px; height:30px; background:#E0E0E0;"></div>
            <div style="text-align:center;">
                <div style="font-size:22px; font-weight:800; color:#2E7D32;">{st.session_state.healthy_scans}</div>
                <div style="font-size:10px; font-weight:600; color:#757575;">{"HEALTHY" if not is_kannada else "ಆರೋಗ್ಯಕರ"}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Services Navigation
    st.markdown(f"<div style='font-size:13px; font-weight:700; color:#424242; margin-bottom:8px;'>{'Quick Services' if not is_kannada else 'ತ್ವರಿತ ಸೇವೆಗಳು'}</div>", unsafe_allow_html=True)
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        if st.button("🤖 " + ("AI Farm Doctor" if not is_kannada else "ಕೃಷಿ ಸಹಾಯ ಚಾಟ್"), use_container_width=True):
            st.session_state.current_screen = "chatbot"
            st.rerun()
        if st.button("🧪 " + ("1% Bordeaux Guide" if not is_kannada else "1% ಬೋರ್ಡೋ ದ್ರಾವಣ"), use_container_width=True):
            st.session_state.current_screen = "chatbot"
            st.session_state.chat_messages = [
                {"role": "user", "content": "How to prepare 1% Bordeaux mixture?" if not is_kannada else "1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ತಯಾರಿಸುವ ವಿಧಾನ ಹೇಗೆ?"},
                {"role": "assistant", "content": get_chatbot_reply("bordeaux", None, None, is_kannada)}
            ]
            st.rerun()
    with c_s2:
        if st.button("📚 " + ("Disease Library" if not is_kannada else "ರೋಗಗಳ ಕೋಶ"), use_container_width=True):
            st.session_state.current_screen = "recommendations"
            st.rerun()
        if st.button("📞 " + ("Helpline 1800-425-5522" if not is_kannada else "ಸಹಾಯವಾಣಿ"), use_container_width=True):
            st.info("📞 Rubber Board Toll-Free Helpline: 1800-425-5522 (Mangaluru, Puttur, Belthangady, Sullia, Shivamogga)")

# =========================================================
# SCREEN 2: SCAN / CAMERA
# =========================================================
elif st.session_state.current_screen == "scan":
    c_b1, c_b2 = st.columns([1, 5])
    with c_b1:
        if st.button("↺", key="btn_back_scan", help="Back to Home"):
            st.session_state.current_screen = "home"
            st.rerun()
    with c_b2:
        st.markdown(f"<div style='font-size:19px; font-weight:800; color:#1B5E20; padding-top:4px;'>{'Scan Rubber Leaf' if not is_kannada else 'ಎಲೆ ತಪಾಸಣೆ'}</div>", unsafe_allow_html=True)

    c_m1, c_m2 = st.columns(2)
    with c_m1:
        if st.button("📷 " + ("Camera" if not is_kannada else "ಕ್ಯಾಮರಾ"), type="primary" if st.session_state.scan_source == "camera" else "secondary", use_container_width=True):
            st.session_state.scan_source = "camera"
            st.rerun()
    with c_m2:
        if st.button("📁 " + ("Gallery" if not is_kannada else "ಅಪ್‌ಲೋಡ್"), type="primary" if st.session_state.scan_source == "upload" else "secondary", use_container_width=True):
            st.session_state.scan_source = "upload"
            st.rerun()

    uploaded_image = None
    if st.session_state.scan_source == "camera":
        cam_file = st.camera_input("Capture rubber leaf", label_visibility="collapsed")
        if cam_file is not None:
            uploaded_image = Image.open(cam_file).convert("RGB")
    else:
        file_input = st.file_uploader("Select leaf image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if file_input is not None:
            uploaded_image = Image.open(file_input).convert("RGB")

    if uploaded_image is not None:
        raw_np = np.array(uploaded_image)
        with st.spinner("Analyzing leaf with MobileNetV2..." if not is_kannada else "ತಪಾಸಣೆ ನಡೆಯುತ್ತಿದೆ..."):
            prep_224, segmented_img, val_metrics = preprocess_and_validate(raw_np)

        if not val_metrics["passed"]:
            st.error(f"⚠️ {val_metrics['error']}")
        else:
            interpreter, weights = load_tflite_model()
            if interpreter is not None:
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()

                input_data = np.expand_dims(prep_224.astype(np.float32), axis=0)
                interpreter.set_tensor(input_details[0]['index'], input_data)

                t0 = time.time()
                interpreter.invoke()
                latency_ms = (time.time() - t0) * 1000

                feat_map = interpreter.get_tensor(output_details[0]['index'])
                probs = interpreter.get_tensor(output_details[1]['index'])[0]

                max_idx = int(np.argmax(probs))
                confidence = float(probs[max_idx]) * 100.0
                predicted_class = CLASSES[max_idx]

                is_healthy = predicted_class == "Healthy"
                sev_pct, sev_label, sev_color = estimate_severity(raw_np, is_healthy)

                # Generate Grad-CAM
                gradcam_full = generate_gradcam_overlay(feat_map, weights, max_idx, raw_np, bbox=val_metrics.get("bbox"))

                # Update stats
                st.session_state.total_scans += 1
                if is_healthy:
                    st.session_state.healthy_scans += 1
                else:
                    st.session_state.diseased_scans += 1

                st.session_state.last_prediction = {
                    "image": uploaded_image,
                    "raw_np": raw_np,
                    "predicted_class": predicted_class,
                    "confidence": confidence,
                    "latency_ms": latency_ms,
                    "probs": probs,
                    "is_healthy": is_healthy,
                    "sev_pct": sev_pct,
                    "sev_label": sev_label,
                    "sev_color": sev_color,
                    "gradcam_full": gradcam_full
                }
                st.session_state.current_screen = "prediction"
                st.rerun()

# =========================================================
# SCREEN 3: PREDICTION RESULTS (Exact match of fragment_prediction.xml & media__1785686797129.png)
# =========================================================
elif st.session_state.current_screen == "prediction":
    pred = st.session_state.last_prediction
    if pred is None:
        st.session_state.current_screen = "home"
        st.rerun()

    # Top Toolbar
    c_p1, c_p2, c_p3 = st.columns([1, 4, 1])
    with c_p1:
        if st.button("↺", key="btn_back_pred", help="Back to Home / Scan"):
            st.session_state.current_screen = "home"
            st.rerun()
    with c_p2:
        st.markdown(f"<div style='font-size:19px; font-weight:800; color:#1B5E20; padding-top:4px;'>{'Prediction Results' if not is_kannada else 'ತಪಾಸಣಾ ಫಲಿತಾಂಶ'}</div>", unsafe_allow_html=True)
    with c_p3:
        if st.button("💬", key="btn_chat_from_pred", help="Ask AI Doctor"):
            st.session_state.current_screen = "chatbot"
            st.rerun()

    # Scanned Leaf Image (Centered rounded card matching fragment_prediction.xml)
    st.image(pred["image"], use_container_width=True)

    # Result Details Card (Matching Android fragment_prediction.xml card_result_details)
    badge_cls = "phone-badge-healthy" if pred["is_healthy"] else "phone-badge-diseased"
    badge_label = ("Healthy" if not is_kannada else "ಆರೋಗ್ಯಕರ") if pred["is_healthy"] else ("Diseased" if not is_kannada else "ರೋಗ ಬಾಧಿತ")

    st.markdown(f"""
    <div class="phone-details-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="phone-disease-title">{pred['predicted_class']}</div>
            <div class="{badge_cls}">{badge_label}</div>
        </div>
        <div class="phone-divider-line"></div>
        <div style="display:flex; justify-content:space-between;">
            <div>
                <div style="font-size:12px; color:#757575;">{"Confidence" if not is_kannada else "ಖಚಿತತೆ"}</div>
                <div style="font-size:18px; font-weight:800; color:#212121;">{pred['confidence']:.1f}%</div>
            </div>
            <div>
                <div style="font-size:12px; color:#757575;">{"Prediction Time" if not is_kannada else "ಸಮಯ"}</div>
                <div style="font-size:18px; font-weight:800; color:#212121;">{pred['latency_ms']:.0f} ms</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Optional Severity Card
    if st.session_state.show_severity and not pred["is_healthy"]:
        st.markdown(f"""
        <div class="phone-details-card" style="border-left: 5px solid {pred['sev_color']};">
            <div style="font-size:12px; color:#757575; font-weight:700; text-transform:uppercase;">{"Visual Severity Assessment" if not is_kannada else "ರೋಗದ ತೀವ್ರತೆ ಪ್ರಮಾಣ"}</div>
            <div style="font-size:20px; font-weight:800; color:{pred['sev_color']}; margin-top:4px;">{pred['sev_label']} ({pred['sev_pct']:.1f}% area)</div>
        </div>
        """, unsafe_allow_html=True)

    # Class Probabilities Card (matching card_probability_chart in fragment_prediction.xml)
    st.markdown(f"""
    <div style="background:#FFFFFF; border-radius:18px; padding:16px 18px; box-shadow:0 2px 10px rgba(0,0,0,0.05); border:1px solid #E0E0E0; margin-bottom:14px;">
        <div style="font-size:14px; font-weight:800; color:#212121; margin-bottom:8px;">{"Class Probabilities" if not is_kannada else "ವರ್ಗವಾರು ಸಂಭವನೀಯತೆ"}</div>
    </div>
    """, unsafe_allow_html=True)

    for idx, cls_name in enumerate(CLASSES):
        prob_val = float(pred["probs"][idx]) * 100.0
        if prob_val > 1.0 or cls_name == pred["predicted_class"]:
            c_cl1, c_cl2 = st.columns([3, 1])
            with c_cl1:
                st.caption(f"{cls_name}")
                st.progress(prob_val / 100.0)
            with c_cl2:
                st.markdown(f"<div style='font-size:12px; font-weight:700; color:#1B5E20; text-align:right; padding-top:6px;'>{prob_val:.1f}%</div>", unsafe_allow_html=True)

    # Flow Action Buttons (matching ll_flow_actions in fragment_prediction.xml)
    if not pred["is_healthy"]:
        if st.button("⚡ " + ("View Severity Analysis" if not is_kannada else "ರೋಗದ ತೀವ್ರತೆ ವೀಕ್ಷಿಸಿ"), use_container_width=True):
            st.session_state.show_severity = not st.session_state.show_severity
            st.rerun()

    if st.button("🔥 " + ("View Grad-CAM Heatmap" if not is_kannada else "ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ಹೀಟ್‌ಮ್ಯಾಪ್ ವೀಕ್ಷಿಸಿ"), type="primary", use_container_width=True):
        st.session_state.current_screen = "gradcam"
        st.rerun()

    if st.button("📖 " + ("View Recommendations" if not is_kannada else "ಕೃಷಿ ಪರಿಹಾರ ವೀಕ್ಷಿಸಿ"), use_container_width=True):
        st.session_state.current_screen = "recommendations"
        st.rerun()

    c_act1, c_act2 = st.columns(2)
    with c_act1:
        if st.button("💾 " + ("Save Record" if not is_kannada else "ದಾಖಲಿಸಿ"), use_container_width=True):
            st.toast("✅ Diagnostic record saved to plantation history!" if not is_kannada else "✅ ತಪಾಸಣಾ ದಾಖಲೆಯನ್ನು ಉಳಿಸಲಾಗಿದೆ!")
    with c_act2:
        lang_key = "kn" if is_kannada else "en"
        rec = RECOMMENDATIONS.get(pred["predicted_class"], {}).get(lang_key, {})
        pdf_file = generate_pdf_report(
            farmer_name="Karnataka Rubber Grower",
            disease_name=pred["predicted_class"],
            confidence=pred["confidence"],
            severity_label=pred["sev_label"],
            severity_pct=pred["sev_pct"],
            rec=rec,
            original_pil=pred["image"],
            heatmap_pil=Image.fromarray(pred["gradcam_full"] if pred["gradcam_full"] is not None else pred["raw_np"]),
            lang=lang_key
        )
        st.download_button(
            label="📄 " + ("Export PDF" if not is_kannada else "ಪಿಡಿಎಫ್ ರಫ್ತು"),
            data=pdf_file,
            file_name=f"RubberGuard_{pred['predicted_class'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# =========================================================
# SCREEN 4: GRAD-CAM HEATMAP (Exact match of fragment_gradcam.xml & media_1792858938847.png)
# =========================================================
elif st.session_state.current_screen == "gradcam":
    pred = st.session_state.last_prediction
    if pred is None:
        st.session_state.current_screen = "home"
        st.rerun()

    # Top Toolbar
    c_g1, c_g2 = st.columns([1, 5])
    with c_g1:
        if st.button("↺", key="btn_back_gradcam", help="Back to Prediction Results"):
            st.session_state.current_screen = "prediction"
            st.rerun()
    with c_g2:
        st.markdown(f"<div style='font-size:19px; font-weight:800; color:#1B5E20; padding-top:4px;'>{'Grad-CAM Heatmap' if not is_kannada else 'ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ಹೀಟ್‌ಮ್ಯಾಪ್'}</div>", unsafe_allow_html=True)

    # Segmented Tabs (Original vs Grad-CAM Overlay, matching media_1792858938847.png)
    c_tab1, c_tab2 = st.columns(2)
    with c_tab1:
        is_orig_active = st.session_state.gradcam_tab == "Original"
        if st.button("Original" if not is_kannada else "ಮೂಲ ಎಲೆ", key="tab_orig", type="primary" if is_orig_active else "secondary", use_container_width=True):
            st.session_state.gradcam_tab = "Original"
            st.rerun()
    with c_tab2:
        is_heat_active = st.session_state.gradcam_tab == "Grad-CAM Overlay"
        if st.button("Grad-CAM Overlay" if not is_kannada else "ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ನಕ್ಷೆ", key="tab_heat", type="primary" if is_heat_active else "secondary", use_container_width=True):
            st.session_state.gradcam_tab = "Grad-CAM Overlay"
            st.rerun()

    # Image Card
    if st.session_state.gradcam_tab == "Original":
        st.image(pred["image"], caption="Original Leaf Capture" if not is_kannada else "ಮೂಲ ಎಲೆ", use_container_width=True)
    else:
        if pred["gradcam_full"] is not None:
            st.image(pred["gradcam_full"], caption="Grad-CAM Saliency Overlay" if not is_kannada else "ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ಹೀಟ್‌ಮ್ಯಾಪ್", use_container_width=True)
        else:
            st.image(pred["image"], caption="Original Leaf", use_container_width=True)

    # Visual Explanation (XAI) Card (Exact verbatim match of media_1792858938847.png)
    st.markdown(f"""
    <div class="phone-xai-card">
        <div class="phone-xai-header">{"Visual Explanation (XAI)" if not is_kannada else "ದೃಶ್ಯ ವಿವರಣೆ (XAI)"}</div>
        <div style="margin-bottom:8px;">
            {"Grad-CAM (Gradient-weighted Class Activation Mapping) is an Explainable AI (XAI) technique. It highlights the exact regions in the leaf that the MobileNetV2 neural network used to determine the classification." if not is_kannada else "ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ತಂತ್ರಜ್ಞಾನವು ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆಯು ಎಲೆಯ ಯಾವ ಭಾಗವನ್ನು ನೋಡಿ ರೋಗವನ್ನು ನಿರ್ಧರಿಸಿದೆ ಎಂಬುದನ್ನು ನಿಖರವಾಗಿ ತೋರಿಸುತ್ತದೆ."}
        </div>
        <div>
            {"Red/Orange (Hot) regions indicate where the model detected key disease markers like fungal lesions, mold patches, or discoloration. Blue/Green (Cold) regions indicate areas that have little or no influence on the model's final classification." if not is_kannada else "ಕೆಂಪು ಮತ್ತು ಕಿತ್ತಳೆ ಬಣ್ಣಗಳು ಶಿಲೀಂಧ್ರ ರೋಗ ಅಥವಾ ಗಾಯವಿರುವ ಮುಖ್ಯ ಭಾಗಗಳನ್ನು ಸೂಚಿಸುತ್ತವೆ. ಹಸಿರು ಭಾಗಗಳು ಆರೋಗ್ಯಕರ ಎಲೆಯ ಅಂಗಾಂಶಗಳನ್ನು ಸೂಚಿಸುತ್ತವೆ."}
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# SCREEN 5: CHATBOT (Exact match of fragment_chatbot.xml & media_1792725418417.png)
# =========================================================
elif st.session_state.current_screen == "chatbot":
    # Top Toolbar
    c_c1, c_c2 = st.columns([1, 5])
    with c_c1:
        if st.button("↺", key="btn_back_chat", help="Back to Home"):
            st.session_state.current_screen = "home"
            st.rerun()
    with c_c2:
        st.markdown(f"<div style='font-size:19px; font-weight:800; color:#1B5E20; padding-top:4px;'>{'RubberGuard Chatbot' if not is_kannada else 'ರಬ್ಬರ್ ಗಾರ್ಡ್ ಚಾಟ್‌ಬಾಟ್'}</div>", unsafe_allow_html=True)

    # Quick Suggestion Chips
    c_cp1, c_cp2 = st.columns(2)
    with c_cp1:
        if st.button("🧪 1% Bordeaux Mixture", use_container_width=True):
            st.session_state.chat_messages = [
                {"role": "user", "content": "How to prepare 1% Bordeaux mixture?" if not is_kannada else "1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ತಯಾರಿಸುವ ವಿಧಾನ?"},
                {"role": "assistant", "content": get_chatbot_reply("bordeaux", None, None, is_kannada)}
            ]
            st.rerun()
    with c_cp2:
        if st.button("🔪 Rubber Tapping Rules", use_container_width=True):
            st.session_state.chat_messages = [
                {"role": "user", "content": "Rubber tapping timing, depth and slope" if not is_kannada else "ರಬ್ಬರ್ ಟ್ಯಾಪಿಂಗ್ ನಿಯಮಗಳು"},
                {"role": "assistant", "content": get_chatbot_reply("tapping", None, None, is_kannada)}
            ]
            st.rerun()

    if not st.session_state.chat_messages:
        initial_greeting = "Hello! I am your RubberGuard Agricultural Assistant. Ask me anything about rubber tree diseases, 1% Bordeaux mixture, tapping, fertilizers, or clones." if not is_kannada else "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ರಬ್ಬರ್ ಗಾರ್ಡ್ ಕೃಷಿ ಸಹಾಯ ಚಾಟ್‌ಬಾಟ್. ರಬ್ಬರ್ ಮರದ ರೋಗಗಳು, ಬೋರ್ಡೋ ಮಿಶ್ರಣ, ಟ್ಯಾಪಿಂಗ್, ಗೊಬ್ಬರ, ಕ್ಲೋನ್ ಅಥವಾ ಮಣ್ಣಿನ ನಿರ್ವಹಣೆಯ ಬಗ್ಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ."
        st.session_state.chat_messages = [{"role": "assistant", "content": initial_greeting}]

    # Render Chat History
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-bot">{msg["content"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

    # Chat Input (matching placeholder from media_1792725418417.png)
    input_placeholder = "Ask about disease, treatment, fertilizer..." if not is_kannada else "ರೋಗ, ಚಿಕಿತ್ಸೆ, ಗೊಬ್ಬರದ ಬಗ್ಗೆ ಕೇಳಿ..."
    if prompt := st.chat_input(input_placeholder):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        last_d = st.session_state.last_prediction["predicted_class"] if st.session_state.last_prediction else None
        last_s = st.session_state.last_prediction["sev_label"] if st.session_state.last_prediction else None
        ans = get_chatbot_reply(prompt, last_d, last_s, is_kannada)
        st.session_state.chat_messages.append({"role": "assistant", "content": ans})
        st.rerun()

# =========================================================
# SCREEN 6: RECOMMENDATIONS & COMPENDIUM
# =========================================================
elif st.session_state.current_screen == "recommendations":
    # Top Toolbar
    c_r1, c_r2 = st.columns([1, 5])
    with c_r1:
        back_target = "prediction" if st.session_state.last_prediction else "home"
        if st.button("↺", key="btn_back_recs", help="Go Back"):
            st.session_state.current_screen = back_target
            st.rerun()
    with c_r2:
        st.markdown(f"<div style='font-size:19px; font-weight:800; color:#1B5E20; padding-top:4px;'>{'Agronomic Advisory' if not is_kannada else 'ಕೃಷಿ ಸಲಹೆ ಮತ್ತು ರೋಗ ಕೋಶ'}</div>", unsafe_allow_html=True)

    lang_key = "kn" if is_kannada else "en"
    target_disease = st.session_state.last_prediction["predicted_class"] if st.session_state.last_prediction else "Abnormal Leaf Fall"

    for d_name, d_info in RECOMMENDATIONS.items():
        data = d_info[lang_key]
        is_expanded = (d_name == target_disease)
        with st.expander(f"🍂 {data['name']}", expanded=is_expanded):
            st.markdown(f"**Pathogen:** `{data.get('pathogen', 'N/A')}`")
            st.write(data["description"])
            st.markdown(f"**🔍 Symptoms:**\n{data['symptoms']}")
            st.markdown(f"**🍀 Organic Treatment:**\n{data['organic']}")
            st.markdown(f"**🧪 Chemical Fungicide:**\n{data['chemical']}")
            st.markdown(f"**🌾 Fertilizer Schedule:**\n{data['fertilizer']}")
            st.markdown(f"**🛡️ Prevention:**\n{data['prevention']}")
            st.markdown(f"**⏱️ Recovery Time:**\n{data['recovery']}")


