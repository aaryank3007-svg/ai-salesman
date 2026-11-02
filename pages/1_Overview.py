import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.db import query_all, query_one
from services.order_service import OrderService

st.set_page_config(page_title="Distributor Dashboard | AI Salesman", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .page-title { font-size: 1.8rem; font-weight: 800; color: #1E1B4B; margin-bottom: 4px; }
    .page-subtitle { color: #64748B; font-size: 0.95rem; margin-bottom: 24px; }
    .kpi-box { background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; text-align: left; }
    .kpi-title { font-size: 0.8rem; font-weight: 600; color: #64748B; text-transform: uppercase; }
    .kpi-number { font-size: 1.7rem; font-weight: 800; color: #0F172A; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">📊 Distributor Command Center</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Real-time FMCG wholesale distribution analytics, order pipeline, and inventory status.</div>', unsafe_allow_html=True)

# Metrics calculation
orders = query_all("SELECT * FROM orders")
products = query_all("SELECT * FROM products")
retailers = query_all("SELECT * FROM retailers")

total_orders_today = len([o for o in orders if o["created_at"].startswith("2026-11-02")]) or len(orders)
pending = len([o for o in orders if o["status"] == "PENDING"])
confirmed = len([o for o in orders if o["status"] == "CONFIRMED"])
dispatched = len([o for o in orders if o["status"] == "DISPATCHED"])
delivered = len([o for o in orders if o["status"] == "DELIVERED"])
total_sales = sum(o["total_amount"] for o in orders if o["status"] not in ["CANCELLED", "REJECTED"])
low_stock = len([p for p in products if p["stock_pieces"] <= p["min_stock_threshold"]])

# Top KPI row
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.markdown(f'<div class="kpi-box"><div class="kpi-title">Total Orders Today</div><div class="kpi-number">{total_orders_today}</div><span style="color:#10B981;font-size:0.8rem;">● Live Pipeline</span></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-box"><div class="kpi-title">Pending Orders</div><div class="kpi-number" style="color:#D97706;">{pending}</div><span style="color:#D97706;font-size:0.8rem;">Action Required</span></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-box"><div class="kpi-title">Confirmed</div><div class="kpi-number" style="color:#2563EB;">{confirmed}</div><span style="color:#2563EB;font-size:0.8rem;">In Warehouse</span></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-box"><div class="kpi-title">Dispatched</div><div class="kpi-number" style="color:#7C3AED;">{dispatched}</div><span style="color:#7C3AED;font-size:0.8rem;">Out in Tempos</span></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="kpi-box"><div class="kpi-title">Total Revenue</div><div class="kpi-number">₹{total_sales:,.0f}</div><span style="color:#10B981;font-size:0.8rem;">Gross Pipeline</span></div>', unsafe_allow_html=True)
with c6:
    st.markdown(f'<div class="kpi-box"><div class="kpi-title">Low Stock Alert</div><div class="kpi-number" style="color:#DC2626;">{low_stock}</div><span style="color:#DC2626;font-size:0.8rem;">SKUs below min</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts Section
col_chart1, col_chart2 = st.columns([1.4, 1])

with col_chart1:
    st.markdown("##### 📈 Order Pipeline Volume by Status")
    status_counts = pd.DataFrame(orders)["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    
    color_map = {
        "PENDING": "#F59E0B",
        "CONFIRMED": "#3B82F6",
        "PACKED": "#6366F1",
        "DISPATCHED": "#8B5CF6",
        "DELIVERED": "#10B981",
        "CANCELLED": "#EF4444"
    }
    
    fig_bar = px.bar(
        status_counts,
        x="Status",
        y="Count",
        color="Status",
        color_discrete_map=color_map,
        text="Count"
    )
    fig_bar.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=280,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    st.markdown("##### 🛒 Category Sales Share")
    cat_sales = query_all("""
        SELECT p.category, SUM(oi.item_total) as sales
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status != 'CANCELLED'
        GROUP BY p.category
    """)
    df_cat = pd.DataFrame(cat_sales)
    if not df_cat.empty:
        fig_pie = px.pie(
            df_cat,
            names="category",
            values="sales",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_pie.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=280
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No category sales recorded.")

st.markdown("---")

# Critical Action Items
col_act1, col_act2 = st.columns(2)

with col_act1:
    st.markdown("##### ⚠️ Pending Approval (Requires Distributor Confirmation)")
    pending_items = query_all("""
        SELECT o.id, r.shop_name, o.total_amount, o.order_source, o.created_at
        FROM orders o
        JOIN retailers r ON o.retailer_id = r.id
        WHERE o.status = 'PENDING'
        ORDER BY o.created_at DESC
    """)
    if pending_items:
        for p_ord in pending_items:
            with st.container(border=True):
                c_a, c_b, c_c = st.columns([2, 1, 1])
                c_a.write(f"**{p_ord['id']}** — {p_ord['shop_name']}")
                c_a.caption(f"Source: {p_ord['order_source']} | Date: {p_ord['created_at']}")
                c_b.write(f"**₹{p_ord['total_amount']:,.2f}**")
                
                if c_c.button("Confirm", key=f"conf_{p_ord['id']}", type="primary"):
                    OrderService().update_order_status(p_ord["id"], "CONFIRMED")
                    st.success(f"{p_ord['id']} confirmed!")
                    st.rerun()
    else:
        st.success("No orders awaiting confirmation. All orders are moving smoothly.")

with col_act2:
    st.markdown("##### 🚨 Low Stock Threshold Warnings")
    low_stock_items = query_all("""
        SELECT id, name, brand, stock_pieces, min_stock_threshold
        FROM products
        WHERE stock_pieces <= min_stock_threshold
        ORDER BY stock_pieces ASC
    """)
    if low_stock_items:
        for l_prod in low_stock_items:
            with st.container(border=True):
                st.write(f"**{l_prod['name']}** ({l_prod['brand']})")
                st.markdown(
                    f"Current Stock: <strong style='color:#DC2626;'>{l_prod['stock_pieces']} pcs</strong> (Min Threshold: {l_prod['min_stock_threshold']} pcs)",
                    unsafe_allow_html=True
                )
    else:
        st.success("All inventory levels are above the safety thresholds.")
