import streamlit as st
import pandas as pd
import plotly.express as px
from services.analytics_service import AnalyticsService
from services.sarvam_client import SarvamService

st.set_page_config(page_title="AI Business Insights | AI Salesman", page_icon="💡", layout="wide")

if "sarvam_client" not in st.session_state:
    st.session_state.sarvam_client = SarvamService()
sarvam = st.session_state.sarvam_client
analytics = AnalyticsService()

st.title("💡 AI Business Assistant for FMCG Distributors")
st.caption("Ask natural language business questions. Powered by predefined safe parameterized analytics engines.")

st.markdown("""
<style>
    .query-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Predefined Quick Questions
st.markdown("##### 🔍 Choose a Business Intelligence Query:")
q1, q2, q3 = st.columns(3)
q4, q5, q6 = st.columns(3)

chosen_query = ""
if q1.button("📦 1. How many orders came today?", use_container_width=True):
    chosen_query = "How many orders came today?"
if q2.button("🔥 2. Which products are selling the most?", use_container_width=True):
    chosen_query = "Which products are selling the most?"
if q3.button("⚠️ 3. Which retailers haven't ordered in 30 days?", use_container_width=True):
    chosen_query = "Which retailers haven't ordered in 30 days?"
if q4.button("🚨 4. Which products are running low?", use_container_width=True):
    chosen_query = "Which products are running low?"
if q5.button("👑 5. Show my top 10 retailers.", use_container_width=True):
    chosen_query = "Show my top 10 retailers."
if q6.button("💰 6. How much sales did I generate this month?", use_container_width=True):
    chosen_query = "How much sales did I generate this month?"

custom_query = st.text_input("Or type your own distributor query:", value=chosen_query)

if custom_query:
    st.markdown("---")
    with st.spinner("Analyzing distributor ledger and inventory..."):
        resp = analytics.answer_question(custom_query)
        
        col_ans, col_voice = st.columns([3, 1])
        with col_ans:
            st.markdown(resp.answer)
        
        with col_voice:
            if st.button("🔊 Listen to Summary (Sarvam Bulbul TTS)"):
                with st.spinner("Synthesizing audio..."):
                    # Strip markdown formatting for TTS
                    clean_text = resp.answer.replace("*", "").replace("#", "").replace("•", "")
                    tts_res = sarvam.text_to_speech(clean_text[:300], language_code="hi-IN")
                    if tts_res.get("success") and tts_res.get("audio_bytes"):
                        st.audio(tts_res["audio_bytes"], format="audio/wav")

        st.markdown("<br>", unsafe_allow_html=True)

        # Plotly visual if data is present
        data = resp.data_summary
        if resp.metric_type == "top_products" and "products" in data:
            df = pd.DataFrame(data["products"])
            fig = px.bar(
                df,
                x="total_revenue",
                y="name",
                orientation='h',
                title="Top FMCG Products by Revenue (₹)",
                labels={"total_revenue": "Revenue (₹)", "name": "Product"},
                color="total_revenue",
                color_continuous_scale="Viridis",
                text="total_revenue"
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=360)
            st.plotly_chart(fig, use_container_width=True)

        elif resp.metric_type == "top_retailers" and "retailers" in data:
            df = pd.DataFrame(data["retailers"])
            fig = px.bar(
                df,
                x="shop_name",
                y="total_spent",
                title="Top Retailers by Purchase Value (₹)",
                labels={"total_spent": "Cumulative Orders (₹)", "shop_name": "Store"},
                color="total_spent",
                color_continuous_scale="Blues",
                text="total_spent"
            )
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)

        elif resp.metric_type == "low_stock" and "products" in data:
            df = pd.DataFrame(data["products"])
            if not df.empty:
                fig = px.bar(
                    df,
                    x="name",
                    y=["stock_pieces", "min_stock_threshold"],
                    barmode="group",
                    title="Current Stock vs Minimum Safety Threshold",
                    labels={"value": "Pieces", "name": "Product SKU"},
                    color_discrete_map={"stock_pieces": "#EF4444", "min_stock_threshold": "#64748B"}
                )
                fig.update_layout(height=360)
                st.plotly_chart(fig, use_container_width=True)
