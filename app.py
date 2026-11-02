import streamlit as st
import datetime
from database.db import query_all, query_one
from services.sarvam_client import SarvamService
from utils.config import SARVAM_API_KEY, SUPPORTED_LANGUAGES

# Configure Page
st.set_page_config(
    page_title="AI Salesman | Voice-First FMCG Distribution",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom SaaS Enterprise Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .hero-banner {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        border-radius: 16px;
        padding: 32px 36px;
        color: white;
        margin-bottom: 28px;
        box-shadow: 0 10px 25px -5px rgba(30, 27, 75, 0.25);
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #C7D2FE;
        margin-bottom: 18px;
        max-width: 720px;
        line-height: 1.5;
    }
    
    .status-badge-live {
        display: inline-flex;
        align-items: center;
        background-color: #065F46;
        color: #A7F3D0;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 9999px;
        border: 1px solid #10B981;
    }
    
    .status-badge-demo {
        display: inline-flex;
        align-items: center;
        background-color: #78350F;
        color: #FDE68A;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 9999px;
        border: 1px solid #F59E0B;
    }

    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    
    .kpi-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .kpi-val {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        margin: 6px 0 4px 0;
    }

    .badge-pending { background-color: #FEF3C7; color: #92400E; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
    .badge-confirmed { background-color: #DBEAFE; color: #1E40AF; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
    .badge-packed { background-color: #E0E7FF; color: #3730A3; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
    .badge-dispatched { background-color: #F3E8FF; color: #6B21A8; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
    .badge-delivered { background-color: #D1FAE5; color: #065F46; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
    .badge-cancelled { background-color: #FEE2E2; color: #991B1B; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "sarvam_client" not in st.session_state:
    st.session_state.sarvam_client = SarvamService()

sarvam = st.session_state.sarvam_client

# Sidebar Branding
with st.sidebar:
    st.markdown("### 🛒 **AI SALESMAN**")
    st.caption("Voice-First Indian FMCG Distribution")
    st.markdown("---")
    
    if sarvam.is_live:
        st.markdown('<div class="status-badge-live">🟢 LIVE: Sarvam AI Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge-demo">🟡 DEMO MODE Active</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Platform Navigation**")
    st.page_link("app.py", label="Home & Launchpad", icon="🏠")
    st.page_link("pages/1_Overview.py", label="Distributor Dashboard", icon="📊")
    st.page_link("pages/2_Retailer_Portal.py", label="Retailer Web Portal", icon="🏪")
    st.page_link("pages/3_Voice_Agent.py", label="AI Voice Salesman", icon="🎙️")
    st.page_link("pages/4_Catalogue.py", label="Catalogue & Packaging", icon="📦")
    st.page_link("pages/5_Orders.py", label="Order Dispatch Pipeline", icon="🚚")
    st.page_link("pages/6_Inventory.py", label="Inventory Control", icon="🏷️")
    st.page_link("pages/7_Retailers.py", label="Retailer Network", icon="👥")
    st.page_link("pages/8_Business_Insights.py", label="AI Business Assistant", icon="💡")
    st.page_link("pages/9_Settings.py", label="System Settings", icon="⚙️")
    st.markdown("---")
    st.caption("Built for Indian Kirana & Wholesale Distributors | Powered by Sarvam AI")

# Main Header Hero
st.markdown(f"""
<div class="hero-banner">
    <div class="hero-title">AI SALESMAN</div>
    <div class="hero-subtitle">
        Your Voice-First Sales Assistant for Indian Distribution. Empowering Kirana retailers to place orders naturally in Hindi, Marathi, and English while automating catalogue matching, stock validation, and fulfillment.
    </div>
    <div>
        {"<span class='status-badge-live'>🟢 Sarvam Cloud Active (Saaras v3 + Bulbul v3 + Sarvam 105B)</span>" if sarvam.is_live else "<span class='status-badge-demo'>🟡 Demo Simulation Active (Configure API Key in Settings to Enable Live Calls)</span>"}
    </div>
</div>
""", unsafe_allow_html=True)

# Fetch quick stats
total_orders = query_one("SELECT COUNT(*) as cnt FROM orders WHERE status != 'CANCELLED'")["cnt"]
pending_orders = query_one("SELECT COUNT(*) as cnt FROM orders WHERE status = 'PENDING'")["cnt"]
total_sales = query_one("SELECT SUM(total_amount) as s FROM orders WHERE status != 'CANCELLED'")["s"] or 0.0
low_stock_cnt = query_one("SELECT COUNT(*) as cnt FROM products WHERE stock_pieces <= min_stock_threshold")["cnt"]
retailer_cnt = query_one("SELECT COUNT(*) as cnt FROM retailers")["cnt"]

# KPI Metrics Grid
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Pipeline Sales</div>
        <div class="kpi-val">₹{total_sales:,.0f}</div>
        <span style="color: #10B981; font-weight: 600; font-size: 0.8rem;">↑ 18.4% vs last week</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Active Orders</div>
        <div class="kpi-val">{total_orders}</div>
        <span style="color: #3B82F6; font-weight: 600; font-size: 0.8rem;">8 Sample FMCG Orders</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Pending Approval</div>
        <div class="kpi-val">{pending_orders}</div>
        <span style="color: #F59E0B; font-weight: 600; font-size: 0.8rem;">Requires Dispatch Action</span>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Low Stock Alerts</div>
        <div class="kpi-val" style="color: {'#EF4444' if low_stock_cnt > 0 else '#10B981'};">{low_stock_cnt}</div>
        <span style="color: #EF4444; font-weight: 600; font-size: 0.8rem;">SKUs below threshold</span>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Active Retailers</div>
        <div class="kpi-val">{retailer_cnt}</div>
        <span style="color: #6366F1; font-weight: 600; font-size: 0.8rem;">Maharashtra Network</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Hub
st.markdown("### 🚀 **Platform Modules**")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("""
    #### 🎙️ **Voice Ordering Salesman**
    Retailers can speak naturally in their mother tongue (Marathi, Hindi, English). The AI transcribes the audio, extracts quantities, handles unit conversions (cartons vs dozens vs boxes), confirms stock, and submits draft orders.
    """)
    if st.button("🎙️ Open Voice Ordering Terminal", use_container_width=True, type="primary"):
        st.switch_page("pages/3_Voice_Agent.py")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    #### 🏪 **Retailer Ordering Portal**
    Dedicated web catalogue for Kirana stores. Browse categories, select carton/box quantities, inspect trade schemes, view past orders, and repeat previous orders in one click.
    """)
    if st.button("🏪 Launch Retailer Portal", use_container_width=True):
        st.switch_page("pages/2_Retailer_Portal.py")

with col_right:
    st.markdown("""
    #### 📊 **Distributor Command Center**
    Full visibility over order fulfillment: confirm pending orders, print dispatch manifests, monitor inventory levels, and manage retailer credit terms.
    """)
    if st.button("📊 View Executive Dashboard", use_container_width=True):
        st.switch_page("pages/1_Overview.py")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    #### 💡 **AI Business Assistant**
    Ask natural language questions about your business: *"How many orders came today?"*, *"Which products are selling the most?"*, or *"Which retailers haven't ordered in 30 days?"*
    """)
    if st.button("💡 Ask AI Business Assistant", use_container_width=True):
        st.switch_page("pages/8_Business_Insights.py")

st.markdown("---")

# Recent Pipeline Activity Table
st.markdown("### ⏱️ **Recent Live Orders**")
recent_orders = query_all("""
    SELECT o.id, r.shop_name, o.order_source, o.status, o.total_amount, o.created_at
    FROM orders o
    JOIN retailers r ON o.retailer_id = r.id
    ORDER BY o.created_at DESC
    LIMIT 5
""")

badge_map = {
    "PENDING": "badge-pending",
    "CONFIRMED": "badge-confirmed",
    "PACKED": "badge-packed",
    "DISPATCHED": "badge-dispatched",
    "DELIVERED": "badge-delivered",
    "CANCELLED": "badge-cancelled"
}

table_html = """
<table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
<thead>
    <tr style="border-bottom: 2px solid #E2E8F0; text-align: left; color: #475569;">
        <th style="padding: 10px;">Order ID</th>
        <th style="padding: 10px;">Retailer Store</th>
        <th style="padding: 10px;">Source</th>
        <th style="padding: 10px;">Status</th>
        <th style="padding: 10px;">Amount</th>
        <th style="padding: 10px;">Date & Time</th>
    </tr>
</thead>
<tbody>
"""

for o in recent_orders:
    b_class = badge_map.get(o["status"], "badge-pending")
    table_html += f"""
    <tr style="border-bottom: 1px solid #F1F5F9;">
        <td style="padding: 12px 10px; font-weight: 700; color: #1E293B;">{o["id"]}</td>
        <td style="padding: 12px 10px; color: #334155;">{o["shop_name"]}</td>
        <td style="padding: 12px 10px;"><code style="color: #4F46E5; background: #EEF2FF; padding: 2px 6px; border-radius: 4px;">{o["order_source"]}</code></td>
        <td style="padding: 12px 10px;"><span class="{b_class}">{o["status"]}</span></td>
        <td style="padding: 12px 10px; font-weight: 700; color: #0F172A;">₹{o["total_amount"]:,.2f}</td>
        <td style="padding: 12px 10px; color: #64748B;">{o["created_at"]}</td>
    </tr>
    """

table_html += "</tbody></table>"
st.markdown(table_html, unsafe_allow_html=True)
