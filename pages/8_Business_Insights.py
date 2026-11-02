import streamlit as st
import pandas as pd
import plotly.express as px
from services.analytics_service import AnalyticsService

st.set_page_config(page_title="AI Business Insights | AI Salesman", page_icon="💡", layout="wide")

analytics = AnalyticsService()

st.title("💡 AI Business Assistant for Distributors")
st.caption("Ask natural language business questions. Powered by predefined safe parameterized analytics engines.")

st.markdown("##### 🔍 Predefined Quick Questions:")
q1, q2, q3 = st.columns(3)
q4, q5, q6 = st.columns(3)

chosen_query = ""
if q1.button("📦 How many orders came today?"):
    chosen_query = "How many orders came today?"
if q2.button("🔥 Which products are selling the most?"):
    chosen_query = "Which products are selling the most?"
if q3.button("⚠️ Which retailers haven't ordered in 30 days?"):
    chosen_query = "Which retailers haven't ordered in 30 days?"
if q4.button("🚨 Which products are running low?"):
    chosen_query = "Which products are running low?"
if q5.button("👑 Show my top 10 retailers."):
    chosen_query = "Show my top 10 retailers."
if q6.button("💰 How much sales did I generate this month?"):
    chosen_query = "How much sales did I generate this month?"

custom_query = st.text_input("Or enter your own distributor question:", value=chosen_query)

if custom_query:
    st.markdown("---")
    with st.spinner("Analyzing distributor ledger and inventory..."):
        resp = analytics.answer_question(custom_query)
        st.markdown(resp.answer)

        # Plotly visual if data is present
        data = resp.data_summary
        if resp.metric_type == "top_products" and "products" in data:
            df = pd.DataFrame(data["products"])
            fig = px.bar(df, x="name", y="total_revenue", title="Top Products by Revenue (₹)", color="total_revenue", color_continuous_scale="Viridis")
            st.plotly_chart(fig, use_container_width=True)
        elif resp.metric_type == "top_retailers" and "retailers" in data:
            df = pd.DataFrame(data["retailers"])
            fig = px.bar(df, x="shop_name", y="total_spent", title="Top Retailers by Purchase Value (₹)", color="total_spent", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)
        elif resp.metric_type == "low_stock" and "products" in data:
            df = pd.DataFrame(data["products"])
            if not df.empty:
                fig = px.bar(df, x="name", y="stock_pieces", title="Current Stock vs Threshold", color="stock_pieces", color_continuous_scale="Reds")
                st.plotly_chart(fig, use_container_width=True)

