import streamlit as st
import pandas as pd
from database.db import query_all, query_one, execute_commit

st.set_page_config(page_title="Product Catalogue | AI Salesman", page_icon="📦", layout="wide")

st.title("📦 FMCG Product Master & Packaging Rules")
st.caption("Manage distributor product catalogue, SKU variants, pricing tiers, and packaging conversion rates.")

# Actions: Add Product Modal / Expander
with st.expander("➕ Add New FMCG Product SKU"):
    with st.form("add_product_form"):
        c1, c2, c3 = st.columns(3)
        sku_id = c1.text_input("SKU ID (e.g. SKU-NEST-KITKAT-40G)")
        name = c2.text_input("Product Name (e.g. Nestle KitKat 40g)")
        brand = c3.text_input("Brand (e.g. Nestle)")

        c4, c5, c6 = st.columns(3)
        cat = c4.selectbox("Category", ["Oral Care", "Biscuits & Bakery", "Instant Food", "Beverages", "Personal Hygiene", "Laundry Care", "Cooking & Edible Oils", "Confectionery"])
        variant = c5.text_input("Variant (e.g. 40g 4-Finger)")
        base_unit = c6.selectbox("Base Unit", ["piece", "packet", "bottle"])

        c7, c8, c9, c10 = st.columns(4)
        mrp = c7.number_input("MRP (₹)", min_value=1.0, value=30.0, step=1.0)
        dp = c8.number_input("Distributor Price (₹)", min_value=1.0, value=25.0, step=0.5)
        stock = c9.number_input("Opening Stock (pieces)", min_value=0, value=200, step=10)
        threshold = c10.number_input("Low Stock Threshold", min_value=10, value=50, step=5)

        aliases = st.text_input("Spoken Aliases (comma-separated):", value="kitkat, chocolate, किटकैट")
        
        st.markdown("**Default Packaging Conversion:**")
        cp1, cp2 = st.columns(2)
        ctn_pcs = cp1.number_input("Pieces in 1 Carton", min_value=1, value=48)
        ctn_price = cp2.number_input("Carton Wholesale Price (₹)", min_value=1.0, value=float(48 * 25.0))

        submitted = st.form_submit_button("Save New Product", type="primary")
        if submitted:
            if not sku_id or not name:
                st.error("SKU ID and Name are required!")
            else:
                existing = query_one("SELECT id FROM products WHERE id = ?", (sku_id,))
                if existing:
                    st.error(f"Product with SKU '{sku_id}' already exists!")
                else:
                    execute_commit("""
                        INSERT INTO products (id, name, brand, category, variant, base_unit, mrp, distributor_price, stock_pieces, min_stock_threshold, aliases, is_demo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (sku_id, name, brand, cat, variant, base_unit, mrp, dp, stock, threshold, aliases))
                    
                    # Add packaging
                    execute_commit("""
                        INSERT INTO packaging_units (product_id, unit_name, pieces_per_unit, unit_price, is_allowed)
                        VALUES (?, 'carton', ?, ?, 1)
                    """, (sku_id, ctn_pcs, ctn_price))
                    execute_commit("""
                        INSERT INTO packaging_units (product_id, unit_name, pieces_per_unit, unit_price, is_allowed)
                        VALUES (?, 'piece', 1, ?, 1)
                    """, (sku_id, dp))
                    
                    st.success(f"Product '{name}' added successfully!")
                    st.rerun()

st.markdown("---")

# Filter & Search
c_search, c_filter = st.columns([2, 1])
with c_search:
    search = st.text_input("🔍 Search catalogue (Name, Brand, or Alias):")
with c_filter:
    all_cats = query_all("SELECT DISTINCT category FROM products")
    cat_list = ["ALL"] + [c["category"] for c in all_cats]
    sel_cat = st.selectbox("Filter Category:", cat_list)

products = query_all("SELECT * FROM products ORDER BY name ASC")
if sel_cat != "ALL":
    products = [p for p in products if p["category"] == sel_cat]
if search:
    s = search.lower()
    products = [p for p in products if s in p["name"].lower() or s in p["brand"].lower() or s in p["aliases"].lower()]

st.markdown(f"**Total SKUs listed:** {len(products)}")

for prod in products:
    is_low = prod["stock_pieces"] <= prod["min_stock_threshold"]
    with st.container(border=True):
        col_main, col_pkg, col_edit = st.columns([2.5, 2.5, 1.2])

        with col_main:
            st.markdown(f"#### {prod['name']}")
            st.caption(f"**Brand:** {prod['brand']} | **Category:** {prod['category']} | **SKU:** `{prod['id']}`")
            st.write(f"**MRP:** ₹{prod['mrp']:.2f} | **Distributor Price:** ₹{prod['distributor_price']:.2f}")
            
            stock_badge = f"<span style='color:{'#DC2626' if is_low else '#059669'}; font-weight:700;'>{prod['stock_pieces']} pcs</span>"
            st.markdown(f"**Current Stock:** {stock_badge} (Min Safety Alert: {prod['min_stock_threshold']} pcs)", unsafe_allow_html=True)
            st.caption(f"Spoken Voice Aliases: `{prod['aliases']}`")

        with col_pkg:
            st.markdown("##### Packaging Matrix")
            pkgs = query_all("SELECT unit_name, pieces_per_unit, unit_price FROM packaging_units WHERE product_id = ?", (prod["id"],))
            for pk in pkgs:
                st.write(f"• **1 {pk['unit_name'].capitalize()}** = {pk['pieces_per_unit']} pcs @ **₹{pk['unit_price']:,.2f}**")

        with col_edit:
            st.markdown("##### Manage")
            new_dp = st.number_input("Update DP (₹)", min_value=1.0, value=float(prod['distributor_price']), key=f"dp_{prod['id']}")
            if st.button("Update Price", key=f"btn_dp_{prod['id']}"):
                execute_commit("UPDATE products SET distributor_price = ? WHERE id = ?", (new_dp, prod["id"]))
                st.success("Updated price!")
                st.rerun()

            if st.button("🗑️ Delete SKU", key=f"del_{prod['id']}"):
                execute_commit("DELETE FROM packaging_units WHERE product_id = ?", (prod["id"],))
                execute_commit("DELETE FROM products WHERE id = ?", (prod["id"],))
                st.warning(f"Deleted SKU {prod['id']}")
                st.rerun()
