import streamlit as st
import tempfile
import os
from database.db import query_all
from services.sarvam_client import SarvamService
from services.order_parser import OrderParser
from services.order_service import OrderService
from models.schemas import OrderCreateRequest

st.set_page_config(page_title="AI Voice Agent | AI Salesman", page_icon="🎙️", layout="wide")

if "sarvam_client" not in st.session_state:
    st.session_state.sarvam_client = SarvamService()
sarvam = st.session_state.sarvam_client
order_parser = OrderParser(sarvam_client=sarvam)
order_service = OrderService()

st.title("🎙️ AI Voice Ordering Terminal")
st.caption("Retailers speak naturally in Hindi, Marathi, or English. AI Salesman transcribes, validates SKUs, checks stock, and drafts orders.")

# Mode banner
if sarvam.is_live:
    st.success("🟢 **LIVE MODE**: Connected to Sarvam AI (Speech-to-Text Saaras v3 + Text-to-Speech Bulbul v3 + Sarvam 105B)")
else:
    st.warning("🟡 **DEMO MODE**: Simulated AI responses active (Enter Sarvam API Key in Settings for live calls)")

# Retailer Selection
retailers = query_all("SELECT id, shop_name, owner_name, current_balance, credit_limit FROM retailers")
ret_dict = {f"{r['shop_name']} ({r['id']}) - Balance: ₹{r['current_balance']:,.0f}": r['id'] for r in retailers}

col_ret, col_lang = st.columns([2, 1])
with col_ret:
    selected_ret_label = st.selectbox("Select Retailer Profile:", list(ret_dict.keys()))
    selected_ret_id = ret_dict[selected_ret_label]
with col_lang:
    lang = st.selectbox("Language / भाषा:", ["hi-IN (Hindi)", "mr-IN (Marathi)", "en-IN (English)"])
    lang_code = lang.split()[0]

st.markdown("---")

# Sample Prompts
st.markdown("##### 💡 Try Sample Voice Prompts (Click to Fill)")
c1, c2, c3 = st.columns(3)
sample_text = ""
if c1.button("🗣️ Hindi FMCG Order (Colgate & Toothbrush)"):
    sample_text = "Namaste bhaiya, mujhe Colgate Strong Teeth ke 10 cartons, MaxFresh ke 5 cartons aur toothbrush ke 2 dozen bhej dena."
if c2.button("🗣️ Marathi Order (Surf Excel & Dettol)"):
    sample_text = "Aamhi 3 peti Surf Excel aani 2 box Dettol sabun magvat aahot"
if c3.button("🗣️ English Restock (Parle-G & Maggi)"):
    sample_text = "Please send 5 cartons of Parle-G biscuits and 3 cartons of Maggi noodles"

# Audio Input Options
tab_voice, tab_text = st.tabs(["🎙️ Voice Audio Input", "⌨️ Text Order Input"])

transcript = ""

with tab_voice:
    st.markdown("Upload audio or record retailer voice order (WAV / MP3):")
    audio_file = st.file_uploader("Upload Audio Note", type=["wav", "mp3", "m4a", "ogg"])
    
    if audio_file:
        st.audio(audio_file)
        if st.button("Transcribe & Process Audio with Sarvam AI", type="primary"):
            with st.spinner("Processing speech with Sarvam Saaras AI..."):
                t_res = sarvam.transcribe_audio(audio_file, language_code=lang_code)
                transcript = t_res.get("transcript", "")
                if t_res.get("mode") == "DEMO":
                    st.info(f"ℹ️ {t_res.get('note')}")
                st.session_state["active_transcript"] = transcript

with tab_text:
    typed_input = st.text_area("Or type/edit spoken transcript:", value=sample_text or st.session_state.get("active_transcript", ""), height=100)
    if st.button("Process Order Intent", type="primary"):
        transcript = typed_input
        st.session_state["active_transcript"] = transcript

active_transcript = st.session_state.get("active_transcript", "")

if active_transcript:
    st.markdown("---")
    st.markdown("### 📋 **AI Order Interpretation & Catalogue Matching**")
    st.info(f"**Retailer Transcript:** \"{active_transcript}\"")
    
    mode = "LIVE" if sarvam.is_live else "DEMO"
    parsed_order = order_parser.parse_order_text(active_transcript, language_code=lang_code, mode=mode)
    
    if parsed_order.clarification_questions:
        st.warning("⚠️ **Clarifications / Alerts:**")
        for q in parsed_order.clarification_questions:
            st.write(f"- {q}")

    if parsed_order.items:
        st.markdown("#### Draft Order Items")
        item_rows = []
        for it in parsed_order.items:
            stock_badge = "✅ In Stock" if it.is_in_stock else "❌ Out of Stock"
            if it.is_ambiguous:
                stock_badge = "❓ Ambiguous SKU"
            item_rows.append({
                "SKU": it.product_id,
                "Product Name": it.product_name,
                "Quantity": f"{it.ordered_quantity:g} {it.ordered_unit}",
                "Conversion": f"{it.pieces_per_unit} pcs/unit ({it.total_pieces} pcs total)",
                "Unit Price": f"₹{it.unit_price:,.2f}",
                "Item Total": f"₹{it.item_total:,.2f}",
                "Stock Status": stock_badge
            })
        st.dataframe(item_rows, use_container_width=True)
        
        # Summary
        c_sub, c_disc, c_tot = st.columns(3)
        c_sub.metric("Subtotal", f"₹{parsed_order.subtotal:,.2f}")
        c_disc.metric("Trade Scheme Discount", f"₹{parsed_order.discount:,.2f}")
        c_tot.metric("Final Total", f"₹{parsed_order.total_amount:,.2f}")

        # Voice Feedback (Sarvam TTS)
        if st.button("🔊 Play Spoken AI Order Confirmation (Sarvam Bulbul TTS)"):
            with st.spinner("Generating speech confirmation..."):
                tts_text = f"Aapka order {len(parsed_order.items)} items ke liye taiyar hai. Kul rashi rupaye {parsed_order.total_amount:,.0f} hai. Kya main ise confirm karoon?"
                tts_res = sarvam.text_to_speech(tts_text, language_code=lang_code)
                if tts_res.get("success") and tts_res.get("audio_bytes"):
                    st.audio(tts_res["audio_bytes"], format="audio/wav")

        st.markdown("<br>", unsafe_allow_html=True)
        
        if parsed_order.is_ready_for_confirmation:
            if st.button("✅ Confirm and Send Order to Distributor Dashboard", type="primary", use_container_width=True):
                req = OrderCreateRequest(
                    retailer_id=selected_ret_id,
                    items=parsed_order.items,
                    order_source="VOICE_AI",
                    original_transcript=active_transcript,
                    raw_language=lang_code
                )
                res = order_service.create_order(req)
                if res["success"]:
                    st.success(f"🎉 {res['message']} Order ID: **{res['order_id']}**")
                    st.balloons()
                    st.session_state["active_transcript"] = ""
                else:
                    st.error(res["message"])
        else:
            st.error("Cannot confirm draft order: Please resolve ambiguities, packaging mismatches, or out-of-stock items shown above.")
