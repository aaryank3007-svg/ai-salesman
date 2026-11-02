import streamlit as st
import pandas as pd
from database.db import query_all, query_one
from services.order_service import OrderService
from services.order_parser import OrderParser
from services.sarvam_client import SarvamService
from models.schemas import OrderCreateRequest, ParsedOrderItem

st.set_page_config(page_title="Retailer Portal | AI Salesman", page_icon="🏪", layout="wide")

if "sarvam_client" not in st.session_state:
    st.session_state.sarvam_client = SarvamService()
sarvam = st.session_state.sarvam_client
order_service = OrderService()
order_parser = OrderParser(sarvam_client=sarvam)

# Cart state
if "retailer_cart" not in st.session_state:
    st.session_state["retailer_cart"] = []

st.markdown("""
<style>
    .portal-banner {
        background: linear-gradient(135deg, #065F46 0%, #047857 50%, #059669 100%);
        border-radius: 14px;
        padding: 22px 28px;
        color: white;
        margin-bottom: 22px;
    }
    .cart-summary {
        background: #F8FAFC;
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }
    .timeline-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #10B981;
        border-radius: 50%;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Retailer Switcher
retailers = query_all("SELECT * FROM retailers")
ret_dict = {f"{r['shop_name']} ({r['owner_name']}, {r['address'].split(',')[-1].strip()})": r for r in retailers}

col_s1, col_s2 = st.columns([2.5, 1.5])
with col_s1:
    selected_label = st.selectbox("🏬 Logged in Kirana Profile:", list(ret_dict.keys()))
    current_retailer = ret_dict[selected_label]

with col_s2:
    cart_items_count = len(st.session_state["retailer_cart"])
    st.markdown(f"🛒 **Active Cart:** `{cart_items_count} items`")

# Header Card
st.markdown(f"""
<div class="portal-banner">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h2 style="margin:0; font-weight:800; color:white;">🏪 {current_retailer['shop_name']}</h2>
            <p style="margin:4px 0 0 0; color:#D1FAE5; font-size:0.92rem;">
                Proprietor: <strong>{current_retailer['owner_name']}</strong> | Phone: {current_retailer['phone']} | Price Group: <strong>{current_retailer['price_group']}</strong>
            </p>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.8rem; color:#A7F3D0; text-transform:uppercase; font-weight:700;">Outstanding Balance</div>
            <div style="font-size:1.6rem; font-weight:800; color:white;">₹{current_retailer['current_balance']:,.2f}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation Tabs
tab_shop, tab_cart, tab_voice, tab_history, tab_ledger = st.tabs([
    "📦 FMCG Catalogue & Order",
    f"🛒 Shopping Cart ({cart_items_count})",
    "🎙️ Quick Voice Order",
    "📜 Order History & Tracking",
    "💵 Payment & Credit Ledger"
])

# 1. CATALOGUE TAB
with tab_shop:
    c_find, c_cat = st.columns([2, 1])
    with c_find:
        search = st.text_input("🔍 Search products (Colgate, Parle, Maggi, Sabun...):")
    with c_cat:
        cats = ["ALL"] + [c["category"] for c in query_all("SELECT DISTINCT category FROM products")]
        sel_cat = st.selectbox("Filter Category:", cats)

    prods = query_all("SELECT * FROM products ORDER BY category, name")
    if sel_cat != "ALL":
        prods = [p for p in prods if p["category"] == sel_cat]
    if search:
        s = search.lower()
        prods = [p for p in prods if s in p["name"].lower() or s in p["brand"].lower() or s in p["aliases"].lower()]

    st.markdown(f"**Showing {len(prods)} Wholesale Products:**")
    
    for p in prods:
        is_low = p["stock_pieces"] <= p["min_stock_threshold"]
        with st.container(border=True):
            col_info, col_order = st.columns([2.5, 2])
            
            with col_info:
                st.markdown(f"### {p['name']}")
                st.markdown(f"**Brand:** {p['brand']} | **Category:** `{p['category']}` | **Variant:** {p['variant']}")
                st.write(f"MRP: ~~₹{p['mrp']:.2f}~~ | **Distributor Wholesale Price: ₹{p['distributor_price']:.2f}** / piece")
                st.caption(f"Stock in Warehouse: **{p['stock_pieces']} pieces** {'(⚠️ Low Stock)' if is_low else ''}")

            with col_order:
                pkgs = query_all("SELECT unit_name, pieces_per_unit, unit_price FROM packaging_units WHERE product_id = ?", (p["id"],))
                pkg_dict = {f"{k['unit_name'].capitalize()} ({k['pieces_per_unit']} pcs @ ₹{k['unit_price']:,.2f})": k for k in pkgs}
                
                sel_pkg_label = st.selectbox("Packaging Unit:", list(pkg_dict.keys()), key=f"sel_pkg_{p['id']}")
                chosen_pkg = pkg_dict[sel_pkg_label]
                
                c_qty, c_btn = st.columns([1, 1.2])
                qty = c_qty.number_input("Qty:", min_value=1, max_value=100, value=1, key=f"qty_sel_{p['id']}")
                
                total_pcs = int(qty * chosen_pkg["pieces_per_unit"])
                total_amt = round(qty * chosen_pkg["unit_price"], 2)
                c_btn.markdown(f"<div style='margin-top:28px; font-weight:700;'>₹{total_amt:,.2f}</div>", unsafe_allow_html=True)
                
                if c_btn.button("➕ Add to Cart", key=f"cart_add_{p['id']}", type="primary"):
                    if p["stock_pieces"] < total_pcs:
                        st.error(f"Cannot add: Only {p['stock_pieces']} pcs available in warehouse.")
                    else:
                        st.session_state["retailer_cart"].append({
                            "product_id": p["id"],
                            "product_name": p["name"],
                            "brand": p["brand"],
                            "variant": p["variant"],
                            "ordered_quantity": float(qty),
                            "ordered_unit": chosen_pkg["unit_name"],
                            "pieces_per_unit": chosen_pkg["pieces_per_unit"],
                            "total_pieces": total_pcs,
                            "unit_price": chosen_pkg["unit_price"],
                            "item_total": total_amt,
                            "stock_available_pieces": p["stock_pieces"],
                            "is_in_stock": True
                        })
                        st.success(f"Added {qty} {chosen_pkg['unit_name']} to cart!")
                        st.rerun()

# 2. CART TAB
with tab_cart:
    cart = st.session_state["retailer_cart"]
    if not cart:
        st.info("🛒 Your shopping cart is empty. Browse the catalogue or use voice ordering to add items!")
    else:
        st.markdown(f"### 🛒 Review Shopping Cart ({len(cart)} items)")
        df_cart = pd.DataFrame(cart)[["product_name", "ordered_quantity", "ordered_unit", "pieces_per_unit", "total_pieces", "unit_price", "item_total"]]
        df_cart.columns = ["Product", "Qty", "Unit", "Pcs/Unit", "Total Pcs", "Wholesale Rate (₹)", "Line Total (₹)"]
        st.dataframe(df_cart, use_container_width=True, hide_index=True)

        subtotal = sum(i["item_total"] for i in cart)
        discount = round(subtotal * 0.02, 2) if subtotal >= 10000 else 0.0
        final_total = round(subtotal - discount, 2)

        c_c1, c_c2, c_c3 = st.columns(3)
        c_c1.metric("Cart Subtotal", f"₹{subtotal:,.2f}")
        c_c2.metric("Bulk Trade Discount (2%)", f"₹{discount:,.2f}")
        c_c3.metric("Final Net Amount", f"₹{final_total:,.2f}")

        col_clr, col_order = st.columns([1, 2])
        if col_clr.button("🗑️ Clear Cart"):
            st.session_state["retailer_cart"] = []
            st.rerun()

        if col_order.button("🚀 Place Confirmed Order to Distributor", type="primary", use_container_width=True):
            items_models = [ParsedOrderItem(**item) for item in cart]
            req = OrderCreateRequest(
                retailer_id=current_retailer["id"],
                items=items_models,
                order_source="RETAILER_PORTAL"
            )
            res = order_service.create_order(req)
            if res["success"]:
                st.balloons()
                st.success(f"🎉 {res['message']} Order ID: **{res['order_id']}** placed successfully!")
                st.session_state["retailer_cart"] = []
                st.rerun()
            else:
                st.error(res["message"])

# 3. QUICK VOICE ORDER TAB
with tab_voice:
    st.markdown("### 🎙️ Instant Voice Ordering")
    st.caption("Speak your order in Hindi, Marathi, or English. Items will be added directly into your cart!")
    v_audio = st.audio_input("Speak order:")
    if v_audio:
        st.audio(v_audio)
        if st.button("Transcribe & Add to Cart", type="primary"):
            with st.spinner("Processing speech with Sarvam AI Saaras..."):
                t_res = sarvam.transcribe_audio(v_audio, language_code="hi-IN")
                text = t_res.get("transcript", "")
                st.info(f"Recognized: *\"{text}\"*")
                parsed = order_parser.parse_order_text(text, language_code="hi-IN")
                if parsed.is_ready_for_confirmation and parsed.items:
                    for it in parsed.items:
                        st.session_state["retailer_cart"].append(it.model_dump())
                    st.success(f"Added {len(parsed.items)} voice-ordered items into your cart!")
                    st.rerun()
                else:
                    st.warning("Could not auto-add: Clarification needed.")
                    for q in parsed.clarification_questions:
                        st.write(f"- {q}")

# 4. ORDER HISTORY & TRACKING
with tab_history:
    st.markdown("### 📜 Past Orders & Real-Time Tracking")
    past_orders = query_all("SELECT * FROM orders WHERE retailer_id = ? ORDER BY created_at DESC", (current_retailer["id"],))
    
    if past_orders:
        for ord_row in past_orders:
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([2.5, 1.2, 1.2, 1.5])
                
                ca.markdown(f"**Order ID:** `{ord_row['id']}` ({ord_row['created_at']})")
                ca.caption(f"Source: {ord_row['order_source']} | Transcript: {ord_row['original_transcript'] or 'Web Portal'}")
                
                # Tracking badge
                st_color = {"PENDING":"#D97706", "CONFIRMED":"#2563EB", "PACKED":"#4F46E5", "DISPATCHED":"#7C3AED", "DELIVERED":"#059669", "CANCELLED":"#DC2626"}.get(ord_row["status"], "#6B7280")
                cb.markdown(f"<span style='color:{st_color}; font-weight:800;'>● {ord_row['status']}</span>", unsafe_allow_html=True)
                
                cc.markdown(f"**₹{ord_row['total_amount']:,.2f}**")
                
                if cd.button("🔁 Repeat This Order", key=f"rpt_{ord_row['id']}"):
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
                        retailer_id=current_retailer["id"],
                        items=new_items,
                        order_source="REPEAT_ORDER"
                    ))
                    if rep_res["success"]:
                        st.balloons()
                        st.success(f"Order repeated successfully! New ID: **{rep_res['order_id']}**")
                        st.rerun()
                    else:
                        st.error(rep_res["message"])
    else:
        st.info("No past orders on file for this retailer.")

# 5. PAYMENT & CREDIT LEDGER
with tab_ledger:
    st.markdown("### 💵 Credit Ledger & Account Standing")
    c_l1, c_l2, c_l3 = st.columns(3)
    c_l1.metric("Current Balance Due", f"₹{current_retailer['current_balance']:,.2f}")
    c_l2.metric("Total Credit Limit", f"₹{current_retailer['credit_limit']:,.2f}")
    avail = current_retailer['credit_limit'] - current_retailer['current_balance']
    c_l3.metric("Available Credit Margin", f"₹{avail:,.2f}", delta="Approved" if avail > 0 else "Breached")
