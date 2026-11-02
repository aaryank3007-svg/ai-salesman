import streamlit as st
import os
from database.seed import seed_database
from services.sarvam_client import SarvamService
from utils.config import SARVAM_API_KEY, SUPPORTED_LANGUAGES

st.set_page_config(page_title="Settings | AI Salesman", page_icon="⚙️", layout="wide")

if "sarvam_client" not in st.session_state:
    st.session_state.sarvam_client = SarvamService()
sarvam = st.session_state.sarvam_client

st.title("⚙️ System Settings & Sarvam AI Configuration")
st.caption("Control live API keys, test speech models, switch between Live and Demo modes, and reset demo data.")

# Status
st.markdown("### 🔌 Sarvam Connection Status")
if sarvam.is_live:
    st.success("🟢 **LIVE MODE ACTIVE**: Authenticated with Sarvam AI API.")
    st.write(f"• **Speech-to-Text Model:** `saaras:v3`")
    st.write(f"• **Text-to-Speech Model:** `bulbul:v3`")
    st.write(f"• **Chat Completion Model:** `sarvam-105b`")
else:
    st.warning("🟡 **DEMO MODE ACTIVE**: Simulated speech and parsing active.")

st.markdown("---")

st.markdown("### 🔊 Test Sarvam Voice Synthesis")
test_text = st.text_input("Spoken preview text:", value="नमस्ते, AI सेल्समैन में आपका स्वागत है।")
sel_lang = st.selectbox("Language Code", list(SUPPORTED_LANGUAGES.keys()))

if st.button("Generate Audio Test", type="primary"):
    with st.spinner("Synthesizing voice..."):
        res = sarvam.text_to_speech(test_text, language_code=sel_lang)
        if res.get("success") and res.get("audio_bytes"):
            st.audio(res["audio_bytes"], format="audio/wav")
            st.success(f"Generated via {res.get('mode', 'DEMO')} mode!")

st.markdown("---")
st.markdown("### 🔄 Reset Demo Data")
if st.button("Re-seed Database (10 Products, 6 Retailers, 8 Orders)"):
    seed_database()
    st.success("Database re-seeded with demo FMCG dataset!")
    st.rerun()
