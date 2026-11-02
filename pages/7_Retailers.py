import streamlit as st
import pandas as pd
from database.db import query_all

st.set_page_config(page_title="Retailer Management | AI Salesman", page_icon="👥", layout="wide")

st.title("👥 Retailer Network & Credit Profiles")
st.caption("Manage Kirana store accounts, credit limits, outstanding balances, and purchase histories.")

retailers = query_all("SELECT * FROM retailers ORDER BY current_balance DESC")

for ret in retailers:
    with st.container(border=True):
        col_main, col_fin = st.columns([2, 1])
        with col_main:
            st.markdown(f"### {ret['shop_name']}")
            st.write(f"**Owner:** {ret['owner_name']} | **Phone:** `{ret['phone']}`")
            st.write(f"**Address:** {ret['address']}")
            st.caption(f"Retailer ID: `{ret['id']}` | Price Tier: `{ret['price_group']}`")
            
            # Show order count
            ord_cnt = query_all("SELECT COUNT(*) as cnt, SUM(total_amount) as total FROM orders WHERE retailer_id = ?", (ret["id"],))
            cnt = ord_cnt[0]["cnt"] if ord_cnt else 0
            tot = ord_cnt[0]["total"] or 0.0
            st.info(f"📊 Cumulative Orders: **{cnt} orders** | Total Value: **₹{tot:,.2f}**")

        with col_fin:
            st.metric("Current Balance", f"₹{ret['current_balance']:,.2f}")
            st.metric("Credit Limit", f"₹{ret['credit_limit']:,.2f}")
            avail = ret['credit_limit'] - ret['current_balance']
            st.metric("Remaining Credit", f"₹{avail:,.2f}", delta="Within Limit" if avail > 0 else "Limit Exceeded")
