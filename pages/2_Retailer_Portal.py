import streamlit as st
import pandas as pd
from database.db import query_all, query_one
from services.order_service import OrderService
from models.schemas import OrderCreateRequest, ParsedOrderItem

st.set_page_config(page_title="Retailer Portal | AI Salesman", page_icon="🏪", layout="wide")

order_service = OrderService()

st.title("🏪 Retailer Self-Service Portal")
st.caption("Browse distributor catalogue, check wholesale pricing, place orders in bulk units, and reorder from history.")

# Retailer Switcher
retailers = query_all("SELECT * FROM retailers")
ret_names = {r["shop_name"]: r for r in retailers}
selected_shop = st.selectbox("Logged in Kirana Store:", list(ret_names.keys()))
ret_info = ret_names[selected_shop]

c1, c2, c3 = st.columns(3)
c1.metric("Store Owner", ret_info["owner_name"])
c2.metric("Outstanding Balance", f"₹{ret_info['current_balance']:,.2f}")
c3.metric("Available Credit Limit", f"₹{ret_info['credit_limit'] - ret_info['current_balance']:,.2f}")

st.markdown("---")

tab_cat, tab_hist = st.tabs(["📦 FMCG Catalogue & Quick Order", "📜 Order History & Repeat Order"])

with tab_cat:
    products = query_all("SELECT * FROM products")
    categories = list(set(p["category"] for p in products))
    sel_cat = st.multiselect("Filter by Category", categories, default=categories)
    
    filtered_prods = [p for p in products if p["category"] in sel_cat]
    
    st.markdown("##### Available Products & Packaging")
    for prod in filtered_prods:
        with st.container(border=True):
            col_info, col_pkg, col_btn = st.columns([2.5, 2, 1.2])
            with col_info:
                st.markdown(f"**{prod['name']}**")
                st.caption(f"Brand: {prod['brand']} | MRP: ₹{prod['mrp']} | Distributor Price: ₹{prod['distributor_price']}")
                st.caption(f"Stock: {prod['stock_pieces']} pcs available")
            
            with col_pkg:
                pkgs = query_all("SELECT * FROM packaging_units WHERE product_id = ?", (prod["id"],))
                pkg_options = {f"{p['unit_name'].capitalize()} ({p['pieces_per_unit']} pcs @ ₹{p['unit_price']:,.2f})": p for p in pkgs}
                sel_pkg_label = st.selectbox("Select Packaging Unit", list(pkg_options.keys()), key=f"pkg_{prod['id']}")
                chosen_pkg = pkg_options[sel_pkg_label]
                qty = st.number_input("Quantity", min_value=1, max_value=50, value=1, key=f"qty_{prod['id']}")

            with col_btn:
                line_total = qty * chosen_pkg["unit_price"]
                st.markdown(f"**Total:** ₹{line_total:,.2f}")
                if st.button("Order Now", key=f"buy_{prod['id']}", type="primary"):
                    item = ParsedOrderItem(
                        product_id=prod["id"],
                        product_name=prod["name"],
                        brand=prod["brand"],
                        variant=prod["variant"],
                        ordered_quantity=float(qty),
                        ordered_unit=chosen_pkg["unit_name"],
                        pieces_per_unit=chosen_pkg["pieces_per_unit"],
                        total_pieces=int(qty * chosen_pkg["pieces_per_unit"]),
                        unit_price=chosen_pkg["unit_price"],
                        item_total=line_total,
                        stock_available_pieces=prod["stock_pieces"],
                        is_in_stock=(prod["stock_pieces"] >= qty * chosen_pkg["pieces_per_unit"])
                    )
                    res = order_service.create_order(OrderCreateRequest(
                        retailer_id=ret_info["id"],
                        items=[item],
                        order_source="RETAILER_PORTAL"
                    ))
                    if res["success"]:
                        st.success(f"Order {res['order_id']} placed successfully!")
                        st.rerun()
                    else:
                        st.error(res["message"])

with tab_hist:
    st.markdown("##### Past Orders for this Retailer")
    past_orders = query_all("SELECT * FROM orders WHERE retailer_id = ? ORDER BY created_at DESC", (ret_info["id"],))
    if past_orders:
        for ord_row in past_orders:
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([2, 1, 1, 1.2])
                ca.write(f"**{ord_row['id']}** ({ord_row['created_at']})")
                ca.caption(f"Source: {ord_row['order_source']} | Transcript: {ord_row['original_transcript'] or 'Web Portal'}")
                cb.write(f"Status: **{ord_row['status']}**")
                cc.write(f"**₹{ord_row['total_amount']:,.2f}**")
                if cd.button("🔁 Repeat Order", key=f"repeat_{ord_row['id']}"):
                    # Duplicate past order items
                    past_items = query_all("SELECT * FROM order_items WHERE order_id = ?", (ord_row["id"],))
                    new_items = []
                    for pi in past_items:
                        prod = query_one("SELECT * FROM products WHERE id = ?", (pi["product_id"],))
                        new_items.append(ParsedOrderItem(
                            product_id=pi["product_id"],
                            product_name=prod["name"],
                            brand=prod["brand"],
                            variant=prod["variant"],
                            ordered_quantity=pi["ordered_quantity"],
                            ordered_unit=pi["ordered_unit"],
                            pieces_per_unit=pi["pieces_per_unit"],
                            total_pieces=pi["total_pieces"],
                            unit_price=pi["unit_price"],
                            item_total=pi["item_total"],
                            stock_available_pieces=prod["stock_pieces"],
                            is_in_stock=(prod["stock_pieces"] >= pi["total_pieces"])
                        ))
                    rep_res = order_service.create_order(OrderCreateRequest(
                        retailer_id=ret_info["id"],
                        items=new_items,
                        order_source="REPEAT_ORDER"
                    ))
                    if rep_res["success"]:
                        st.success(f"Repeated order created: **{rep_res['order_id']}**")
                        st.rerun()
                    else:
                        st.error(rep_res["message"])
    else:
        st.info("No past orders found for this retailer.")

