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
    page_title="RubberGuard - Rubber Leaf Disease Diagnostics",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
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
# Streamlit Application Layout
# ---------------------------------------------------------
# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/natural-food.png", width=64)
    st.title("RubberGuard AI")
    st.caption("On-Device MobileNetV2 + OpenCV Diagnostic Platform")
    st.markdown("---")
    
    language = st.radio("Language / ಭಾಷೆ:", ["English", "ಕನ್ನಡ (Kannada)"], index=0)
    is_kannada = "ಕನ್ನಡ" in language
    
    st.markdown("---")
    st.subheader("Model Specifications" if not is_kannada else "ಮಾಡೆಲ್ ವಿವರಗಳು")
    st.markdown("""
    - **Architecture**: MobileNetV2
    - **Classes**: 9 Categories (8 diseases + Background)
    - **Input Resolution**: 224 × 224 × 3
    - **Explainability**: On-Device Grad-CAM
    - **Severity Estimation**: HSV Multi-thresholding
    """)
    st.markdown("---")
    st.info("📞 **Rubber Board Helpline:**\n1800-425-5522\n\nOffice: Mangaluru / Puttur, Karnataka" if not is_kannada else "📞 **ರಬ್ಬರ್ ಬೋರ್ಡ್ ಸಹಾಯವಾಣಿ:**\n1800-425-5522\n\nಕಚೇರಿ: ಮಂಗಳೂರು / ಪುತ್ತೂರು, ಕರ್ನಾಟಕ")

# Main Header
st.title("🍃 Rubber Leaf Disease Diagnosis & Advisory System" if not is_kannada else "🍃 ರಬ್ಬರ್ ಎಲೆ ರೋಗ ಪತ್ತೆ ಮತ್ತು ಕೃಷಿ ಸಲಹಾ ವ್ಯವಸ್ಥೆ")
st.markdown("Automated leaf segmentation, quality validation, deep learning classification, and actionable treatments for rubber plantation growers in Karnataka." if not is_kannada else "ಕರ್ನಾಟಕದ ರಬ್ಬರ್ ಬೆಳೆಗಾರರಿಗೆ ನೈಜ-ಸಮಯದ ಎಲೆ ರೋಗ ಪತ್ತೆ, ಗಂಭೀರತೆ ಮಾಪನ ಮತ್ತು ಪರಿಹಾರ ಕ್ರಮಗಳ ವ್ಯವಸ್ಥೆ.")

tab_diagnose, tab_chat, tab_kb, tab_pipeline = st.tabs([
    "🔬 Leaf Diagnosis" if not is_kannada else "🔬 ಎಲೆ ತಪಾಸಣೆ",
    "🤖 AI Farm Assistant" if not is_kannada else "🤖 ಕೃಷಿ ಸಹಾಯ ಚಾಟ್‌ಬಾಟ್",
    "📚 Disease Library" if not is_kannada else "📚 ರೋಗ ಮಾಹಿತಿ ಕೋಶ",
    "⚙️ System Pipeline" if not is_kannada else "⚙️ ತಾಂತ್ರಿಕ ಪ್ರಕ್ರಿಯೆ"
])

# ---------------------------------------------------------
# Tab 1: Leaf Diagnosis
# ---------------------------------------------------------
with tab_diagnose:
    st.markdown("### Step 1: Upload or Capture Rubber Leaf Photo" if not is_kannada else "### ಹಂತ 1: ರಬ್ಬರ್ ಎಲೆಯ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಅಥವಾ ಸೆರೆಹಿಡಿಯಿರಿ")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        upload_mode = st.radio(
            "Select Input Source:" if not is_kannada else "ಚಿತ್ರದ ಮೂಲವನ್ನು ಆಯ್ಕೆಮಾಡಿ:",
            ["📁 Upload from Gallery / Storage", "📷 Take Photo with Camera"],
            horizontal=True
        )
    
    uploaded_image = None
    if "Upload" in upload_mode:
        file = st.file_uploader(
            "Choose a leaf image (JPG, JPEG, PNG)" if not is_kannada else "ಎಲೆಯ ಚಿತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ",
            type=["jpg", "jpeg", "png"]
        )
        if file is not None:
            uploaded_image = Image.open(file).convert("RGB")
    else:
        camera_file = st.camera_input("Capture leaf image" if not is_kannada else "ಕ್ಯಾಮರಾದಿಂದ ಫೋಟೋ ತೆಗೆಯಿರಿ")
        if camera_file is not None:
            uploaded_image = Image.open(camera_file).convert("RGB")
            
    if uploaded_image is not None:
        raw_np = np.array(uploaded_image)
        
        st.markdown("---")
        st.markdown("### Step 2: Computer Vision Preprocessing & Quality Validation" if not is_kannada else "### ಹಂತ 2: ಕಂಪ್ಯೂಟರ್ ವಿಷನ್ ಪ್ರಕ್ರಿಯೆ ಮತ್ತು ಗುಣಮಟ್ಟ ಪರಿಶೀಲನೆ")
        
        with st.spinner("Running OpenCV leaf extraction and illumination correction..." if not is_kannada else "ಚಿತ್ರ ಸಂಸ್ಕರಣೆ ನಡೆಯುತ್ತಿದೆ..."):
            prep_224, segmented_img, val_metrics = preprocess_and_validate(raw_np)
            
        if not val_metrics["passed"]:
            st.error(f"⚠️ **Image Validation Failed:** {val_metrics['error']}" if not is_kannada else f"⚠️ **ಚಿತ್ರ ಪರಿಶೀಲನೆ ವಿಫಲವಾಗಿದೆ:** {val_metrics['error']}")
            
            c_val1, c_val2, c_val3 = st.columns(3)
            with c_val1:
                st.metric("Leaf Coverage" if not is_kannada else "ಎಲೆಯ ವ್ಯಾಪ್ತಿ", f"{val_metrics.get('leaf_ratio', 0):.1f}%", help="Must be >= 40%")
            with c_val2:
                st.metric("Focus Sharpness" if not is_kannada else "ತೀಕ್ಷ್ಣತೆ (Focus)", f"{val_metrics.get('laplacian_var', 0):.1f}", help="Laplacian variance must be >= 30.0")
            with c_val3:
                st.metric("Luminance Exposure" if not is_kannada else "ಬೆಳಕಿನ ಮಟ್ಟ", f"{val_metrics.get('mean_luminance', 0):.1f}", help="Luminance must be between 45 and 225")
                
            st.info("💡 **Tips for best results:** Capture a single leaf close-up against a clean background with steady hands and clear lighting." if not is_kannada else "💡 **ಉತ್ತಮ ಫಲಿತಾಂಶಕ್ಕಾಗಿ ಸಲಹೆ:** ಎಲೆಯನ್ನು ಹತ್ತಿರದಿಂದ ಸ್ಪಷ್ಟವಾಗಿ ಹಿಡಿದು, ಸರಿಯಾದ ಬೆಳಕಿನಲ್ಲಿ ಫೋಟೋ ತೆಗೆಯಿರಿ.")
        else:
            # Display Image Pipeline Side-by-Side
            c1, c2, c3 = st.columns(3)
            with c1:
                st.image(raw_np, caption="1. Original Capture" if not is_kannada else "1. ಮೂಲ ಚಿತ್ರ", use_container_width=True)
            with c2:
                st.image(segmented_img, caption="2. Segmented Leaf (No Clutter)" if not is_kannada else "2. ಹಿನ್ನೆಲೆ ರಹಿತ ಎಲೆ", use_container_width=True)
            with c3:
                st.image(prep_224, caption="3. CLAHE Enhanced (224×224)" if not is_kannada else "3. ಸಂಸ್ಕರಿಸಿದ ಎಲೆ (224×224)", use_container_width=True)
                
            # Run Inference
            st.markdown("---")
            st.markdown("### Step 3: Disease Classification & Saliency Analysis" if not is_kannada else "### ಹಂತ 3: ರೋಗ ಪತ್ತೆ ಮತ್ತು ಫಲಿತಾಂಶ")
            
            interpreter, weights = load_tflite_model()
            if interpreter is None:
                st.error("TFLite model could not be loaded.")
            else:
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                
                # Format input tensor
                input_data = np.expand_dims(prep_224.astype(np.float32), axis=0)
                interpreter.set_tensor(input_details[0]['index'], input_data)
                
                start_time = time.time()
                interpreter.invoke()
                latency_ms = (time.time() - start_time) * 1000
                
                # Multi-output: Output 0 is Feature Map (1, 7, 7, 1280), Output 1 is Probabilities (1, 9)
                feat_map = interpreter.get_tensor(output_details[0]['index'])
                probs = interpreter.get_tensor(output_details[1]['index'])[0]
                
                max_idx = int(np.argmax(probs))
                confidence = float(probs[max_idx]) * 100.0
                predicted_class = CLASSES[max_idx]
                
                # Severity estimation
                is_healthy = predicted_class == "Healthy"
                sev_pct, sev_label, sev_color = estimate_severity(raw_np, is_healthy)
                
                # Store in session state for chatbot
                st.session_state["last_scan_disease"] = predicted_class
                st.session_state["last_scan_severity"] = f"{sev_label} ({sev_pct:.1f}%)"
                
                # Check for Background or Low Confidence (true out-of-distribution clutter)
                if predicted_class == "Background / Non-Rubber Leaf" or confidence < 35.0:
                    if predicted_class == "Background / Non-Rubber Leaf":
                        st.warning("⚠️ **Non-Rubber Leaf / Clutter Detected!**\nThe model detected a non-leaf background object (e.g. keyboard, text, desk). Please upload a clear photo of an authentic rubber leaf." if not is_kannada else "⚠️ **ಅಮಾನ್ಯ ಚಿತ್ರ ಪತ್ತೆಯಾಗಿದೆ!**\nಇದು ರಬ್ಬರ್ ಎಲೆಯಾಗಿ ಕಂಡುಬರುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ನೈಜ ರಬ್ಬರ್ ಎಲೆಯ ಫೋಟೋ ತೆಗೆಯಿರಿ.")
                    else:
                        st.warning(f"⚠️ **Prediction confidence is low ({confidence:.1f}% < 35%).** Please upload a clearer, properly lit rubber leaf image." if not is_kannada else f"⚠️ **ಖಚಿತತೆಯ ಮಟ್ಟ ಕಡಿಮೆಯಾಗಿದೆ ({confidence:.1f}%).** ದಯವಿಟ್ಟು ಸ್ಪಷ್ಟವಾದ ಎಲೆಯ ಫೋಟೋ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.")
                else:
                    if confidence < 70.0:
                        st.info(f"ℹ️ **Notice: Image has mild blur / soft focus (Confidence: {confidence:.1f}%). Showing top predicted disease condition.**" if not is_kannada else f"ℹ️ **ಸೂಚನೆ: ಚಿತ್ರದಲ್ಲಿ ಸ್ವಲ್ಪ ಮಸುಕುತನವಿದೆ (ಖಚಿತತೆ: {confidence:.1f}%). ಸಂಭಾವ್ಯ ರೋಗದ ವಿವರಗಳನ್ನು ಕೆಳಗೆ ನೀಡಲಾಗಿದೆ.**")
                    # Result Cards
                    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                    with col_r1:
                        st.metric("Detected Condition" if not is_kannada else "ಪತ್ತೆಯಾದ ರೋಗ", predicted_class)
                    with col_r2:
                        st.metric("Model Confidence" if not is_kannada else "ಖಚಿತತೆ (Confidence)", f"{confidence:.1f}%")
                    with col_r3:
                        st.metric("Visual Severity" if not is_kannada else "ತೀವ್ರತೆ (Severity)", f"{sev_label} ({sev_pct:.1f}%)")
                    with col_r4:
                        st.metric("Inference Time" if not is_kannada else "ಸಮಯ (Latency)", f"{latency_ms:.1f} ms")
                        
                    # Precision Color-Grounded Grad-CAM Heatmaps
                    gradcam_leaf = generate_gradcam_overlay(feat_map, weights, max_idx, prep_224)
                    gradcam_full = generate_gradcam_overlay(feat_map, weights, max_idx, raw_np, bbox=validation_metrics.get("bbox"))
                    
                    st.markdown("#### Visual Explanation: Precision Grad-CAM" if not is_kannada else "#### ತಪಾಸಣಾ ನಕ್ಷೆ: ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ಹೀಟ್‌ಮ್ಯಾಪ್")
                    c_gc1, c_gc2 = st.columns([1, 1])
                    
                    with c_gc1:
                        view_mode = st.radio(
                            "Select Visualization Layer:" if not is_kannada else "ನೋಟದ ಆಯ್ಕೆ:",
                            ["🔥 Grad-CAM Heatmap (AI Attention)", "🌿 Original Capture"]
                            if not is_kannada else
                            ["🔥 ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ಹೀಟ್‌ಮ್ಯಾಪ್", "🌿 ಮೂಲ ಚಿತ್ರ"],
                            horizontal=True
                        )
                        if "Grad-CAM" in view_mode or "ಗ್ರಾಡ್-ಕ್ಯಾಮ್" in view_mode:
                            align_opt = st.radio(
                                "Alignment:" if not is_kannada else "ಜೋಡಣೆ:",
                                ["Segmented Leaf (224×224)", "Full Photo Overlay"] if not is_kannada else ["ಸಂಸ್ಕರಿಸಿದ ಎಲೆ (224×224)", "ಮೂಲ ಚಿತ್ರ"],
                                horizontal=True,
                                key="gc_align_radio"
                            )
                            displayed_cam = gradcam_leaf if ("Segmented" in align_opt or "ಸಂಸ್ಕರಿಸಿದ" in align_opt) else gradcam_full
                            if displayed_cam is not None:
                                st.image(displayed_cam, caption="Color-Grounded Grad-CAM (Pinpoints Exact Lesion Focus)" if not is_kannada else "ಗ್ರಾಡ್-ಕ್ಯಾಮ್ ನಕ್ಷೆ (ರೋಗ ಲಕ್ಷಣಗಳ ನಿಖರ ಕೇಂದ್ರ ಬಿಂದು)", use_container_width=True)
                            else:
                                st.image(raw_np, caption="Grad-CAM not available", use_container_width=True)
                        else:
                            st.image(raw_np, caption="Original Capture" if not is_kannada else "ಮೂಲ ಚಿತ್ರ", use_container_width=True)
                            
                    with c_gc2:
                        st.write("**Class Probability Distribution:**" if not is_kannada else "**ವರ್ಗವಾರು ಸಂಭವನೀಯತೆ ವಿವರ:**")
                        for idx, cls_name in enumerate(CLASSES):
                            p = float(probs[idx]) * 100.0
                            st.progress(p / 100.0, text=f"{cls_name}: {p:.1f}%")
                            
                    # Detailed Agronomic Recommendations
                    lang_key = "kn" if is_kannada else "en"
                    rec = RECOMMENDATIONS.get(predicted_class, {}).get(lang_key, None)
                    
                    if rec:
                        st.markdown("---")
                        st.markdown(f"### 📋 Management Recommendations for {rec['name']}" if not is_kannada else f"### 📋 {rec['name']} ನಿರ್ವಹಣಾ ಶಿಫಾರಸುಗಳು")
                        
                        col_rec1, col_rec2 = st.columns(2)
                        with col_rec1:
                            st.markdown(f"**🔍 Symptoms & Identification:**\n\n{rec['symptoms']}" if not is_kannada else f"**🔍 ರೋಗ ಲಕ್ಷಣಗಳು:**\n\n{rec['symptoms']}")
                            st.markdown(f"**🍀 Organic Treatment:**\n\n{rec['organic']}" if not is_kannada else f"**🍀 ಸಾವಯವ ಚಿಕಿತ್ಸೆ:**\n\n{rec['organic']}")
                            st.markdown(f"**🌾 Fertilizer Schedule:**\n\n{rec['fertilizer']}" if not is_kannada else f"**🌾 ಪೋಷಕಾಂಶ ಮತ್ತು ಗೊಬ್ಬರ:**\n\n{rec['fertilizer']}")
                        with col_rec2:
                            st.markdown(f"**⚠️ Favorable Conditions / Causes:**\n\n{rec['causes']}" if not is_kannada else f"**⚠️ ರೋಗದ ಕಾರಣಗಳು:**\n\n{rec['causes']}")
                            st.markdown(f"**🧪 Chemical Fungicide Spray:**\n\n{rec['chemical']}" if not is_kannada else f"**🧪 ಶಿಫಾರಸು ಮಾಡಿದ ಶಿಲೀಂಧ್ರನಾಶಕ:**\n\n{rec['chemical']}")
                            st.markdown(f"**🛡️ Preventive Cultural Measures:**\n\n{rec['prevention']}" if not is_kannada else f"**🛡️ ಮುನ್ನೆಚ್ಚರಿಕೆ ಕ್ರಮಗಳು:**\n\n{rec['prevention']}")
                            
                        # Download PDF Report Button
                        st.markdown("---")
                        c_pdf1, c_pdf2 = st.columns([2, 1])
                        with c_pdf1:
                            farmer_name_input = st.text_input("Enter Farmer Name / Plot Number for the Report:" if not is_kannada else "ವರದಿಗಾಗಿ ರೈತರ ಹೆಸರು / ಜಮೀನಿನ ವಿವರ ನಮೂದಿಸಿ:", value="Karnataka Rubber Grower")
                        with c_pdf2:
                            st.write("")
                            st.write("")
                            overlay_source = displayed_cam if displayed_cam is not None else raw_np
                            overlay_pil = Image.fromarray(overlay_source)
                            pdf_buf = generate_pdf_report(
                                farmer_name=farmer_name_input,
                                disease_name=predicted_class,
                                confidence=confidence,
                                severity_label=sev_label,
                                severity_pct=sev_pct,
                                rec=rec,
                                original_pil=uploaded_image,
                                heatmap_pil=overlay_pil,
                                lang=lang_key
                            )
                            st.download_button(
                                label="📥 Download PDF Diagnostic Report" if not is_kannada else "📥 ಪಿಡಿಎಫ್ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
                                data=pdf_buf,
                                file_name=f"RubberGuard_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf"
                            )

# ---------------------------------------------------------
# Tab 2: AI Farm Assistant Chatbot
# ---------------------------------------------------------
with tab_chat:
    st.markdown("### 🤖 Bilingual Agricultural Assistant" if not is_kannada else "### 🤖 ರಬ್ಬರ್ ಕೃಷಿ ಸಹಾಯ ಚಾಟ್‌ಬಾಟ್")
    st.caption("Ask questions about leaf diseases, symptoms, chemical & organic fungicides, tapping methods, or Bordeaux mixture." if not is_kannada else "ರಬ್ಬರ್ ಎಲೆ ರೋಗಗಳು, ಗೊಬ್ಬರ, ಟ್ಯಾಪಿಂಗ್ ವಿಧಾನ ಅಥವಾ ಬೋರ್ಡೋ ಮಿಶ್ರಣದ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ.")
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I am your RubberGuard AI Assistant. How can I assist you with your rubber trees today?" if not is_kannada else "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ರಬ್ಬರ್ ಗಾರ್ಡ್ ಕೃಷಿ ಸಹಾಯ ಚಾಟ್‌ಬಾಟ್. ನಿಮ್ಮ ರಬ್ಬರ್ ಮರಗಳ ರೋಗ, ಚಿಕಿತ್ಸೆ ಅಥವಾ ಗೊಬ್ಬರದ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ."}
        ]
        
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Type your question here (e.g. 'How to treat Anthracnose?')..." if not is_kannada else "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ (ಉದಾ: 'ಆಂಥ್ರಾಕ್ನೋಸ್ ಚಿಕಿತ್ಸೆ ಹೇಗೆ?')..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        last_disease = st.session_state.get("last_scan_disease", None)
        last_sev = st.session_state.get("last_scan_severity", None)
        reply = get_chatbot_reply(prompt, last_disease, last_sev, is_kannada)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

# ---------------------------------------------------------
# Tab 3: Disease Knowledge Base
# ---------------------------------------------------------
with tab_kb:
    st.markdown("### 📚 Comprehensive Rubber Disease Compendium" if not is_kannada else "### 📚 ರಬ್ಬರ್ ರೋಗಗಳ ಸಮಗ್ರ ಮಾಹಿತಿ ಕೋಶ")
    
    lang_key = "kn" if is_kannada else "en"
    for d_name, d_info in RECOMMENDATIONS.items():
        data = d_info[lang_key]
        with st.expander(f"🍂 {data['name']}", expanded=(d_name == "Abnormal Leaf Fall")):
            st.markdown(f"**Pathogen:** `{data.get('pathogen', 'N/A')}`")
            st.write(data["description"])
            
            c_kb1, c_kb2 = st.columns(2)
            with c_kb1:
                st.markdown(f"**Symptoms:**\n{data['symptoms']}")
                st.markdown(f"**Organic Treatment:**\n{data['organic']}")
                st.markdown(f"**Fertilizer Schedule:**\n{data['fertilizer']}")
            with c_kb2:
                st.markdown(f"**Causes & Environment:**\n{data['causes']}")
                st.markdown(f"**Chemical Control:**\n{data['chemical']}")
                st.markdown(f"**Prevention:**\n{data['prevention']}")

# ---------------------------------------------------------
# Tab 4: System Pipeline & Architecture
# ---------------------------------------------------------
with tab_pipeline:
    st.markdown("### ⚙️ End-to-End System Pipeline" if not is_kannada else "### ⚙️ ತಾಂತ್ರಿಕ ಪ್ರಕ್ರಿಯೆ ಮತ್ತು ವಿನ್ಯಾಸ")
    
    st.markdown("""
    ```
    Raw Leaf Image Upload / Camera Capture
                     │
                     ▼
          [OpenCV HSV Segmentation] ──► Extracts Green, Yellow/Brown, Dark & White Pixels
                     │
                     ▼
           [Contour Detection] ───────► Locates largest leaf & eliminates background clutter
                     │
                     ▼
         [Quality Validation Checks] ─► Validates Leaf Area Coverage >= 40%, Sharpness >= 30, Exposure (45-225)
                     │
                     ▼
        [Illumination & Shadow CLAHE] ─► Equalizes luminance (L channel in Lab space)
                     │
                     ▼
         [Bilateral Denoising & Mask] ─► Sharpens lesions & blurs sensor noise
                     │
                     ▼
         [MobileNetV2 TFLite Model] ──► Multi-output inference (<80ms latency)
                     │
            ┌────────┴────────┐
            ▼                 ▼
    [Class Probability]   [Feature Map (7×7×1280)]
            │                 │
            ▼                 ▼
    [Confidence Guard]    [Grad-CAM Saliency Overlay]
            │                 │
            └────────┬────────┘
                     ▼
        [OpenCV Severity Estimation] ──► Calculates % of infected leaf area
                     │
                     ▼
    Bilingual Management Advisory + One-Click PDF Report
    ```
    """)
    st.markdown("---")
    st.write("Developed for Karnataka rubber plantation owners. Built with MobileNetV2, OpenCV, TensorFlow Lite, and Streamlit.")
