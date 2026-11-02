import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()

# App Modes
APP_MODE_DEFAULT = os.getenv("APP_MODE", "LIVE" if SARVAM_API_KEY else "DEMO").upper()

# Sarvam Configurations
SARVAM_STT_MODEL = "saaras:v3"
SARVAM_TTS_MODEL = "bulbul:v3"
SARVAM_CHAT_MODEL = "sarvam-105b"

SUPPORTED_LANGUAGES = {
    "hi-IN": {"name": "Hindi (हिंदी)", "default_speaker": "ritu", "alternate_speaker": "anushka"},
    "mr-IN": {"name": "Marathi (मराठी)", "default_speaker": "mrunal_mr_narration", "alternate_speaker": "ishita_mr_conversational"},
    "en-IN": {"name": "Indian English", "default_speaker": "simran", "alternate_speaker": "priya"}
}

DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "hi-IN")

# Unit Normalization Dictionary (multilingual Indian Kirana terms)
UNIT_MAPPINGS = {
    "carton": "carton",
    "cartons": "carton",
    "ctn": "carton",
    "peti": "carton",
    "petis": "carton",
    "पेटी": "carton",
    "पेट्या": "carton",
    "खोका": "carton",
    "खोके": "carton",
    "पुडा": "carton",
    "box": "box",
    "boxes": "box",
    "dabba": "box",
    "dabbe": "box",
    "डब्बा": "box",
    "डब्बे": "box",
    "बॉक्स": "box",
    "dozen": "dozen",
    "dozens": "dozen",
    "darjan": "dozen",
    "दर्जन": "dozen",
    "डझन": "dozen",
    "piece": "piece",
    "pieces": "piece",
    "pcs": "piece",
    "packet": "piece",
    "packets": "piece",
    "pkt": "piece",
    "नग": "piece",
    "पीस": "piece",
    "पॅकेट": "piece",
    "पॉकेट": "piece"
}

# Number words in Hindi/Marathi/English
WORD_TO_NUMBER = {
    "ek": 1, "एक": 1, "one": 1,
    "do": 2, "दोन": 2, "दो": 2, "two": 2,
    "teen": 3, "तीन": 3, "three": 3,
    "chaar": 4, "चार": 4, "four": 4,
    "paanch": 5, "पाच": 5, "पांच": 5, "five": 5,
    "chhah": 6, "सहा": 6, "छह": 6, "six": 6,
    "saat": 7, "सात": 7, "seven": 7,
    "aath": 8, "आठ": 8, "eight": 8,
    "nau": 9, "नऊ": 9, "नौ": 9, "nine": 9,
    "das": 10, "दहा": 10, "दस": 10, "ten": 10,
    "gyarah": 11, "अकरा": 11, "ग्यारह": 11, "eleven": 11,
    "barah": 12, "बारा": 12, "बारह": 12, "twelve": 12,
    "pandrah": 15, "पंधरा": 15, "पंद्रह": 15, "fifteen": 15,
    "bees": 20, "वीस": 20, "बीस": 20, "twenty": 20,
    "pachees": 25, "पंचवीस": 25, "पच्चीस": 25, "twenty five": 25,
    "tees": 30, "तीस": 30, "thirty": 30,
    "chalees": 40, "चाळीस": 40, "चालीस": 40, "forty": 40,
    "pachas": 50, "पन्नास": 50, "पचास": 50, "fifty": 50,
    "sau": 100, "शंभर": 100, "सौ": 100, "hundred": 100
}
