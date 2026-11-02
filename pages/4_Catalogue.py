import streamlit as st
import pandas as pd
from database.db import query_all, execute_commit

st.set_page_config(page_title="Product Catalogue | AI Salesman", page_icon="📦", layout="wide")

st.title("📦 FMCG Product Catalogue & Packaging Rules")
st.caption("Distributor SKU master with packaging unit conversions (Cartons, Boxes, Dozens, Pieces) and pricing.")

products = query_all("SELECT * FROM products")

# Search
search_term = st.text_input("🔍 Search products by name, brand, or alias (e.g. 'Colgate', 'Noodles', 'साबण'):")
if search_term:
    s = search_term.lower()
    products = [p for p in products if s in p["name"].lower() or s in p["brand"].lower() or s in p["aliases"].lower()]

for prod in products:
    with st.container(border=True):
        col1, col2 = st.columns([1.5, 2])
        with col1:
            st.markdown(f"### {prod['name']}")
            st.markdown(f"**Brand:** {prod['brand']} | **Category:** {prod['category']}")
            st.markdown(f"**SKU ID:** `{prod['id']}` | **Variant:** {prod['variant']}")
            st.markdown(f"**MRP:** ₹{prod['mrp']:.2f} | **Distributor Price:** ₹{prod['distributor_price']:.2f}")
            st.markdown(f"**Stock:** `{prod['stock_pieces']} pieces` (Threshold: {prod['min_stock_threshold']} pcs)")
            st.caption(f"Spoken Aliases: {prod['aliases']}")

        with col2:
            st.markdown("##### Packaging Conversion Matrix")
            pkgs = query_all("SELECT unit_name, pieces_per_unit, unit_price, is_allowed FROM packaging_units WHERE product_id = ?", (prod["id"],))
            df_pkg = pd.DataFrame(pkgs)
            if not df_pkg.empty:
                df_pkg.columns = ["Unit", "Pieces per Unit", "Unit Price (₹)", "Allowed"]
                df_pkg["Unit Price (₹)"] = df_pkg["Unit Price (₹)"].apply(lambda x: f"₹{x:,.2f}")
                st.dataframe(df_pkg, use_container_width=True, hide_index=True)
            else:
                st.write("No packaging units configured.")
