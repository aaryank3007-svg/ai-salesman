import streamlit as st
import io
from database.db import query_all, query_one
from services.sarvam_client import SarvamService
from services.order_parser import OrderParser
from services.order_service import OrderService
from models.schemas import OrderCreateRequest

st.set_page_config(page_title="Voice Agent | AI Salesman", page_icon="🎙️", layout="wide")

# Custom UI Styles
st.markdown("""
<style>
    .agent-header {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        padding: 24px 30px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
    }
    .badge-live {
        background: #065F46; color: #A7F3D0; font-weight: 700; padding: 4px 12px; border-radius: 9999px; font-size: 0.8rem; border: 1px solid #10B981;
    }
    .badge-demo {
        background: #78350F; color: #FDE68A; font-weight: 700; padding: 4px 12px; border-radius: 9999px; font-size: 0.8rem; border: 1px solid #F59E0B;
    }
    .order-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .clarification-alert {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 16px;
        color: #92400E;
    }
</style>
""", unsafe_allow_html=True)

if "sarvam_client" not in st.session_state:
    st.session_state.sarvam_client = SarvamService()
sarvam = st.session_state.sarvam_client
order_parser = OrderParser(sarvam_client=sarvam)
order_service = OrderService()

# Header Banner
st.markdown(f"""
<div class="agent-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h2 style="margin:0; font-weight:800; color:white;">🎙️ AI Voice Ordering Terminal</h2>
            <p style="margin:4px 0 0 0; color:#C7D2FE; font-size:0.95rem;">
                Retailers speak naturally in Hindi, Marathi, or English. AI Salesman parses quantities, handles packaging conversions, checks inventory, and speaks back confirmation.
            </p>
        </div>
        <div>
            {"<span class='badge-live'>🟢 LIVE SARVAM AI</span>" if sarvam.is_live else "<span class='badge-demo'>🟡 DEMO MODE</span>"}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Retailer & Language Selection
c_ret, c_lang = st.columns([2, 1])
retailers = query_all("SELECT id, shop_name, owner_name, current_balance, credit_limit FROM retailers")
ret_map = {f"{r['shop_name']} ({r['id']}) - Balance: ₹{r['current_balance']:,.0f}": r['id'] for r in retailers}

with c_ret:
    selected_ret_label = st.selectbox("👤 Select Retailer Profile:", list(ret_map.keys()))
    selected_ret_id = ret_map[selected_ret_label]
    ret_obj = query_one("SELECT * FROM retailers WHERE id = ?", (selected_ret_id,))

with c_lang:
    lang_choice = st.selectbox("🗣️ Spoken Language:", [
        "hi-IN — Hindi (हिंदी)",
        "mr-IN — Marathi (मराठी)",
        "en-IN — Indian English"
    ])
    lang_code = lang_choice.split()[0]

st.markdown("---")

# Quick Audio Prompts
st.markdown("##### ⚡ Quick Demonstration Scenarios (Click to Test Prompts):")
p1, p2, p3, p4 = st.columns(4)
sample_prompt = ""

if p1.button("🛒 Standard FMCG Order", use_container_width=True):
    sample_prompt = "Namaste bhaiya, mujhe Colgate Strong Teeth ke 10 cartons, MaxFresh ke 5 cartons aur toothbrush ke 2 dozen bhej dena."
if p2.button("📦 Marathi Laundry & Soap", use_container_width=True):
    sample_prompt = "Aamhi 3 peti Surf Excel aani 2 box Dettol sabun magvat aahot, lavkar pathva."
if p3.button("❓ Ambiguous Product Test", use_container_width=True):
    sample_prompt = "Bhaiya mujhe 5 carton Colgate bhej do kal tak."
if p4.button("⚠️ Incompatible Unit Test", use_container_width=True):
    sample_prompt = "Mujhe Colgate MaxFresh ke 3 box aur Parle G ke 2 carton bhej do."

# Voice Input Section (Live Microphone + Upload Fallback)
st.markdown("### 🎙️ Retailer Voice Input")

tab_mic, tab_upload, tab_text = st.tabs([
    "🎙️ Live Microphone Recording",
    "📁 Audio File Upload Fallback",
    "⌨️ Spoken Transcript Text Editor"
])

recorded_audio = None
uploaded_audio = None

with tab_mic:
    st.caption("Click the red record button, speak your order naturally in Hindi, Marathi, or English, then click stop:")
    mic_audio = st.audio_input("Record retailer order:")
    if mic_audio:
        st.audio(mic_audio)
        if st.button("🚀 Transcribe with Sarvam Saaras AI", type="primary", key="transcribe_mic"):
            with st.spinner("Processing speech with Sarvam AI Cloud..."):
                res = sarvam.transcribe_audio(mic_audio, language_code=lang_code)
                st.session_state["active_transcript"] = res.get("transcript", "")
                if res.get("mode") == "DEMO":
                    st.info(f"ℹ️ {res.get('note')}")

with tab_upload:
    st.caption("Upload a pre-recorded audio note (.wav, .mp3, .m4a):")
    uploaded_file = st.file_uploader("Upload audio file", type=["wav", "mp3", "m4a", "ogg"], key="voice_upload")
    if uploaded_file:
        st.audio(uploaded_file)
        if st.button("🚀 Transcribe Uploaded Audio", type="primary", key="transcribe_upload"):
            with st.spinner("Transcribing with Sarvam Saaras AI..."):
                res = sarvam.transcribe_audio(uploaded_file, language_code=lang_code)
                st.session_state["active_transcript"] = res.get("transcript", "")
                if res.get("mode") == "DEMO":
                    st.info(f"ℹ️ {res.get('note')}")

with tab_text:
    st.caption("Or directly inspect/edit the spoken order text:")
    text_input = st.text_area("Spoken Transcript:", value=sample_prompt or st.session_state.get("active_transcript", ""), height=80)
    if st.button("⚡ Process Order Transcript", type="primary", key="process_text"):
        st.session_state["active_transcript"] = text_input

# Active Transcript Processing
current_transcript = st.session_state.get("active_transcript", "")

if current_transcript:
    st.markdown("---")
    st.markdown("### 📝 **Parsed Order & Catalogue Matching**")
    
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.info(f"**Recognized Transcript:** \"{current_transcript}\"")
    with col_t2:
        st.markdown(f"**Mode:** `{'LIVE CALL (Sarvam)' if sarvam.is_live else 'DEMO SIMULATION'}`")

    # Run AI Order Engine
    mode_str = "LIVE" if sarvam.is_live else "DEMO"
    parsed_order = order_parser.parse_order_text(current_transcript, language_code=lang_code, mode=mode_str)

    # Show Clarification Alerts if any
    if parsed_order.clarification_questions:
        st.markdown("""
        <div class="clarification-alert">
            <strong>⚠️ Clarification Required before Confirmation:</strong>
        </div>
        """, unsafe_allow_html=True)
        for q in parsed_order.clarification_questions:
            st.warning(f"• {q}")

    # Itemized Breakdown
    if parsed_order.items:
        st.markdown("#### 📦 Identified Items & Packaging Conversions")
        
        for idx, item in enumerate(parsed_order.items):
            with st.container(border=True):
                c_sku, c_conv, c_pricing, c_status = st.columns([2.5, 2, 1.5, 1.5])
                
                with c_sku:
                    if item.is_ambiguous:
                        st.markdown(f"**❓ Ambiguous Mention:** `{item.product_name}`")
                        st.caption("Multiple catalogue variants match. Please pick one below:")
                        opt_names = [f"{o['name']} ({o['variant']})" for o in item.ambiguous_options]
                        sel_variant = st.selectbox("Select exact SKU variant:", opt_names, key=f"ambig_{idx}")
                    else:
                        st.markdown(f"**{item.product_name}**")
                        st.caption(f"Brand: {item.brand} | SKU: `{item.product_id}` | Variant: {item.variant}")

                with c_conv:
                    if item.needs_packaging_clarification:
                        st.markdown(f"<span style='color:#DC2626; font-weight:700;'>Requested Unit: {item.ordered_quantity:g} {item.ordered_unit}</span>", unsafe_allow_html=True)
                        st.caption(f"⚠️ {item.clarification_message}")
                    else:
                        st.markdown(f"**{item.ordered_quantity:g} {item.ordered_unit.capitalize()}**")
                        st.caption(f"Conversion: {item.pieces_per_unit} pieces / {item.ordered_unit} (= **{item.total_pieces} pcs**)")

                with c_pricing:
                    if not item.is_ambiguous and not item.needs_packaging_clarification:
                        st.markdown(f"**Rate:** ₹{item.unit_price:,.2f} / {item.ordered_unit}")
                        st.markdown(f"**Line Total:** ₹{item.item_total:,.2f}")
                    else:
                        st.write("—")

                with c_status:
                    if item.is_ambiguous:
                        st.markdown("<span style='color:#D97706; font-weight:700;'>❓ Ambiguous</span>", unsafe_allow_html=True)
                    elif item.needs_packaging_clarification:
                        st.markdown("<span style='color:#DC2626; font-weight:700;'>⚠️ Unit Mismatch</span>", unsafe_allow_html=True)
                    elif item.is_in_stock:
                        st.markdown("<span style='color:#059669; font-weight:700;'>✅ In Stock</span>", unsafe_allow_html=True)
                        st.caption(f"{item.stock_available_pieces} pcs in warehouse")
                    else:
                        st.markdown("<span style='color:#DC2626; font-weight:700;'>❌ Insufficient Stock</span>", unsafe_allow_html=True)
                        st.caption(f"Only {item.stock_available_pieces} pcs available")

        # Order Summary Box
        st.markdown("<br>", unsafe_allow_html=True)
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Items Count", f"{len(parsed_order.items)} line items")
        col_s2.metric("Subtotal", f"₹{parsed_order.subtotal:,.2f}")
        col_s3.metric("Trade Scheme Discount (2%)", f"₹{parsed_order.discount:,.2f}")
        col_s4.metric("Net Payable Amount", f"₹{parsed_order.total_amount:,.2f}")

        # Spoken Confirmation via Sarvam Bulbul TTS
        st.markdown("---")
        st.markdown("#### 🔊 Spoken Confirmation (Sarvam AI Bulbul v3)")
        col_tts_btn, col_tts_player = st.columns([1.5, 2.5])
        
        with col_tts_btn:
            if st.button("📢 Generate & Play Spoken Order Summary", use_container_width=True):
                with st.spinner("Synthesizing speech with Sarvam Bulbul..."):
                    speech_text = (
                        f"Namaste {ret_obj['owner_name']} ji. Aapke order mein {len(parsed_order.items)} items shamil hain. "
                        f"Kul rashi rupaye {parsed_order.total_amount:,.0f} hai. Kya main is order ko confirm karoon?"
                    )
                    tts_result = sarvam.text_to_speech(speech_text, language_code=lang_code)
                    if tts_result.get("success") and tts_result.get("audio_bytes"):
                        st.session_state["tts_audio"] = tts_result["audio_bytes"]

        with col_tts_player:
            if "tts_audio" in st.session_state:
                st.audio(st.session_state["tts_audio"], format="audio/wav")

        # Confirmation Action
        st.markdown("<br>", unsafe_allow_html=True)
        if parsed_order.is_ready_for_confirmation:
            st.success("✅ **Order Validated:** All items matched, packaging verified, and warehouse stock confirmed.")
            if st.button("🛒 Explicitly Confirm and Send Order to Distributor", type="primary", use_container_width=True):
                req = OrderCreateRequest(
                    retailer_id=selected_ret_id,
                    items=parsed_order.items,
                    order_source="VOICE_AI",
                    original_transcript=current_transcript,
                    raw_language=lang_code
                )
                res = order_service.create_order(req)
                if res["success"]:
                    st.balloons()
                    st.success(f"🎉 {res['message']} Order ID: **{res['order_id']}** has been sent to the distributor dispatch queue!")
                    st.session_state["active_transcript"] = ""
                    if "tts_audio" in st.session_state:
                        del st.session_state["tts_audio"]
                else:
                    st.error(f"Error creating order: {res['message']}")
        else:
            st.error("⛔ **Draft Order Incomplete:** Please address the clarification alerts above (resolve ambiguous variants or adjust out-of-stock quantities) before confirming.")
