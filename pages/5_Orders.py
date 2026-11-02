import streamlit as st
import pandas as pd
from database.db import query_all, query_one, execute_commit
from services.order_service import OrderService

st.set_page_config(page_title="Order Management | AI Salesman", page_icon="🚚", layout="wide")

order_service = OrderService()

st.title("🚚 Order Dispatch Pipeline & Management")
st.caption("Distributor workflow: Review incoming orders, confirm, edit quantities, pack, dispatch, deliver, or reject.")

# Pipeline Status Metrics
counts = query_all("SELECT status, COUNT(*) as cnt, SUM(total_amount) as total FROM orders GROUP BY status")
cnt_dict = {c["status"]: c for c in counts}

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Pending Approval", cnt_dict.get("PENDING", {}).get("cnt", 0))
c2.metric("Confirmed Orders", cnt_dict.get("CONFIRMED", {}).get("cnt", 0))
c3.metric("Packed & Ready", cnt_dict.get("PACKED", {}).get("cnt", 0))
c4.metric("Dispatched on Road", cnt_dict.get("DISPATCHED", {}).get("cnt", 0))
c5.metric("Successfully Delivered", cnt_dict.get("DELIVERED", {}).get("cnt", 0))

st.markdown("---")

# Filter
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    status_filter = st.selectbox("Filter Status Pipeline:", ["ALL", "PENDING", "CONFIRMED", "PACKED", "DISPATCHED", "DELIVERED", "CANCELLED", "REJECTED"])

query = """
    SELECT o.id, r.shop_name, r.owner_name, r.phone, r.address, o.status, o.order_source, o.original_transcript, o.subtotal, o.discount, o.total_amount, o.cancellation_reason, o.created_at
    FROM orders o
    JOIN retailers r ON o.retailer_id = r.id
"""
if status_filter != "ALL":
    query += f" WHERE o.status = '{status_filter}'"
query += " ORDER BY o.created_at DESC"

orders = query_all(query)
st.markdown(f"**Showing {len(orders)} Orders in Pipeline**")

for ord_row in orders:
    curr_status = ord_row["status"]
    
    badge_color = {
        "PENDING": "#F59E0B",
        "CONFIRMED": "#2563EB",
        "PACKED": "#4F46E5",
        "DISPATCHED": "#7C3AED",
        "DELIVERED": "#059669",
        "CANCELLED": "#DC2626",
        "REJECTED": "#DC2626"
    }.get(curr_status, "#6B7280")

    with st.expander(f"📦 Order {ord_row['id']} — {ord_row['shop_name']} | Status: {curr_status} | ₹{ord_row['total_amount']:,.2f}", expanded=(curr_status == 'PENDING')):
        c_left, c_right = st.columns([2.2, 1.2])

        with c_left:
            st.markdown(f"**Customer:** {ord_row['shop_name']} ({ord_row['owner_name']})")
            st.write(f"📞 `{ord_row['phone']}` | 📍 {ord_row['address']}")
            st.caption(f"Source: `{ord_row['order_source']}` | Placed on: {ord_row['created_at']}")
            if ord_row["original_transcript"]:
                st.info(f"🗣️ Original Spoken Voice: *\"{ord_row['original_transcript']}\"*")
            if ord_row["cancellation_reason"]:
                st.error(f"Reason: {ord_row['cancellation_reason']}")

            # Items
            st.markdown("##### Order Items Breakdown")
            items = query_all("""
                SELECT oi.id, p.id as sku, p.name, oi.ordered_quantity, oi.ordered_unit, oi.pieces_per_unit, oi.total_pieces, oi.unit_price, oi.item_total
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (ord_row["id"],))

            df_items = pd.DataFrame(items)
            if not df_items.empty:
                df_view = df_items[["sku", "name", "ordered_quantity", "ordered_unit", "pieces_per_unit", "total_pieces", "unit_price", "item_total"]].copy()
                df_view.columns = ["SKU", "Product", "Qty", "Unit", "Pcs/Unit", "Total Pcs", "Unit Rate (₹)", "Total (₹)"]
                st.dataframe(df_view, use_container_width=True, hide_index=True)

            st.markdown(f"**Subtotal:** ₹{ord_row['subtotal']:,.2f} | **Scheme Discount:** ₹{ord_row['discount']:,.2f} | **Net Payable:** **₹{ord_row['total_amount']:,.2f}**")

        with c_right:
            st.markdown(f"##### Current Status: <span style='color:{badge_color}; font-weight:800;'>{curr_status}</span>", unsafe_allow_html=True)
            allowed = order_service.VALID_TRANSITIONS.get(curr_status, [])
            
            if allowed:
                st.markdown("**Advance Workflow:**")
                for target_st in allowed:
                    if target_st not in ["CANCELLED", "REJECTED"]:
                        btn_label = {
                            "CONFIRMED": "✅ Confirm Order",
                            "PACKED": "📦 Mark as Packed",
                            "DISPATCHED": "🚚 Mark as Dispatched",
                            "DELIVERED": "🏁 Mark as Delivered"
                        }.get(target_st, f"Move to {target_st}")
                        
                        if st.button(btn_label, key=f"adv_{ord_row['id']}_{target_st}", type="primary", use_container_width=True):
                            res = order_service.update_order_status(ord_row["id"], target_st)
                            if res["success"]:
                                st.success(res["message"])
                                st.rerun()
                            else:
                                st.error(res["message"])

                st.markdown("---")
                if "REJECTED" in allowed or "CANCELLED" in allowed:
                    cancel_reason = st.text_input("Rejection / Cancellation Reason:", key=f"c_reason_{ord_row['id']}")
                    col_rej, col_can = st.columns(2)
                    if "REJECTED" in allowed:
                        if col_rej.button("❌ Reject", key=f"rej_{ord_row['id']}", use_container_width=True):
                            res = order_service.update_order_status(ord_row["id"], "REJECTED", reason=cancel_reason or "Stock unavailable / Credit limit")
                            st.warning(res["message"])
                            st.rerun()
                    if "CANCELLED" in allowed:
                        if col_can.button("🚫 Cancel", key=f"can_{ord_row['id']}", use_container_width=True):
                            res = order_service.update_order_status(ord_row["id"], "CANCELLED", reason=cancel_reason or "Customer requested cancellation")
                            st.warning(res["message"])
                            st.rerun()
            else:
                st.success("Order has reached its terminal state.")
