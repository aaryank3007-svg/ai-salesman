import streamlit as st
import pandas as pd
import plotly.express as px
from database.db import query_all, query_one, execute_commit

st.set_page_config(page_title="Retailer Management | AI Salesman", page_icon="👥", layout="wide")

st.title("👥 Retailer Accounts & Credit Ledger")
st.caption("Manage Kirana store accounts, credit limits, outstanding balances, order history, and purchasing patterns.")

retailers = query_all("SELECT * FROM retailers ORDER BY current_balance DESC")

# Summary metrics
total_receivables = sum(r["current_balance"] for r in retailers)
total_credit_granted = sum(r["credit_limit"] for r in retailers)

m1, m2, m3 = st.columns(3)
m1.metric("Total Retailers", len(retailers))
m2.metric("Total Outstanding Receivables", f"₹{total_receivables:,.2f}")
m3.metric("Total Credit Line Extended", f"₹{total_credit_granted:,.2f}")

st.markdown("---")

for ret in retailers:
    with st.container(border=True):
        col_main, col_fin = st.columns([2.2, 1.2])

        with col_main:
            st.markdown(f"### {ret['shop_name']}")
            st.markdown(f"**Proprietor:** {ret['owner_name']} | **Phone:** `{ret['phone']}`")
            st.write(f"📍 **Address:** {ret['address']}")
            st.caption(f"Retailer ID: `{ret['id']}` | Price Group: `{ret['price_group']}`")

            # Order History for this retailer
            ret_orders = query_all("""
                SELECT id, order_source, status, total_amount, created_at
                FROM orders
                WHERE retailer_id = ?
                ORDER BY created_at DESC
            """, (ret["id"],))

            if ret_orders:
                st.markdown(f"**Purchasing Pattern ({len(ret_orders)} orders recorded):**")
                df_orders = pd.DataFrame(ret_orders)
                df_orders.columns = ["Order ID", "Source", "Status", "Amount (₹)", "Date"]
                st.dataframe(df_orders, use_container_width=True, hide_index=True)
            else:
                st.info("No past orders recorded yet.")

        with col_fin:
            st.markdown("##### Credit & Ledger")
            st.metric("Outstanding Balance", f"₹{ret['current_balance']:,.2f}")
            st.metric("Credit Limit", f"₹{ret['credit_limit']:,.2f}")
            available_credit = ret['credit_limit'] - ret['current_balance']
            st.metric("Available Credit", f"₹{available_credit:,.2f}", delta="Healthy" if available_credit > 0 else "Limit Breached")

            # Record payment or update credit limit
            with st.expander("Record Cash/UPI Payment"):
                pay_amt = st.number_input("Payment Received (₹)", min_value=100.0, value=5000.0, step=500.0, key=f"pay_{ret['id']}")
                pay_mode = st.selectbox("Mode", ["UPI", "NEFT", "CASH", "CHEQUE"], key=f"mode_{ret['id']}")
                if st.button("Submit Payment", key=f"btn_pay_{ret['id']}", type="primary"):
                    execute_commit("""
                        UPDATE retailers
                        SET current_balance = MAX(0, current_balance - ?)
                        WHERE id = ?
                    """, (pay_amt, ret["id"]))
                    st.success(f"Recorded ₹{pay_amt} payment via {pay_mode}!")
                    st.rerun()
