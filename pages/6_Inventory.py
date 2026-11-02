import streamlit as st
import pandas as pd
from database.db import query_all, execute_commit

st.set_page_config(page_title="Inventory Management | AI Salesman", page_icon="🏷️", layout="wide")

st.title("🏷️ Inventory & Stock Control")
st.caption("Real-time warehouse stock tracking, threshold warnings, and manual stock replenishment.")

products = query_all("SELECT * FROM products ORDER BY stock_pieces ASC")

st.markdown("### Stock Overview")
for p in products:
    is_low = p["stock_pieces"] <= p["min_stock_threshold"]
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
        c1.write(f"**{p['name']}** (`{p['id']}`)")
        c1.caption(f"Brand: {p['brand']} | Category: {p['category']}")
        
        status_text = f"<span style='color: {'#DC2626' if is_low else '#10B981'}; font-weight:700;'>{p['stock_pieces']} pcs</span>"
        c2.markdown(f"Current Stock: {status_text}", unsafe_allow_html=True)
        c2.caption(f"Min Threshold: {p['min_stock_threshold']} pcs")

        add_qty = c3.number_input(f"Add Stock (pcs)", min_value=10, max_value=2000, value=100, step=10, key=f"add_{p['id']}")
        if c4.button("📥 Restock", key=f"btn_add_{p['id']}"):
            execute_commit("UPDATE products SET stock_pieces = stock_pieces + ? WHERE id = ?", (add_qty, p["id"]))
            st.success(f"Added {add_qty} pieces to {p['name']}!")
            st.rerun()

