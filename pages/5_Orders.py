import streamlit as st
import pandas as pd
from database.db import query_all, query_one
from services.order_service import OrderService

st.set_page_config(page_title="Order Management | AI Salesman", page_icon="🚚", layout="wide")

order_service = OrderService()

st.title("🚚 Order Dispatch & Pipeline Management")
st.caption("Track order status, manage fulfillment (Confirm -> Pack -> Dispatch -> Deliver), or reject with reason.")

# Status Filter
status_filter = st.selectbox("Filter by Status", ["ALL", "PENDING", "CONFIRMED", "PACKED", "DISPATCHED", "DELIVERED", "CANCELLED"])

query = """
    SELECT o.id, r.shop_name, r.owner_name, r.phone, o.status, o.order_source, o.total_amount, o.created_at, o.cancellation_reason
    FROM orders o
    JOIN retailers r ON o.retailer_id = r.id
"""
if status_filter != "ALL":
    query += f" WHERE o.status = '{status_filter}'"
query += " ORDER BY o.created_at DESC"

orders = query_all(query)

st.markdown(f"**Showing {len(orders)} orders**")

for ord_row in orders:
    with st.expander(f"📦 Order {ord_row['id']} — {ord_row['shop_name']} | Status: {ord_row['status']} | ₹{ord_row['total_amount']:,.2f}", expanded=(ord_row['status'] == 'PENDING')):
        c_info, c_action = st.columns([2, 1])
        
        with c_info:
            st.markdown(f"**Retailer:** {ord_row['shop_name']} ({ord_row['owner_name']}, Ph: `{ord_row['phone']}`)")
            st.markdown(f"**Source:** `{ord_row['order_source']}` | **Order Date:** {ord_row['created_at']}")
            if ord_row['cancellation_reason']:
                st.error(f"Cancellation Reason: {ord_row['cancellation_reason']}")

            # Order items table
            items = query_all("""
                SELECT p.name, oi.ordered_quantity, oi.ordered_unit, oi.pieces_per_unit, oi.total_pieces, oi.unit_price, oi.item_total
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (ord_row["id"],))
            df_it = pd.DataFrame(items)
            if not df_it.empty:
                df_it.columns = ["Product", "Qty", "Unit", "Pcs/Unit", "Total Pcs", "Unit Price", "Item Total"]
                st.dataframe(df_it, use_container_width=True, hide_index=True)

        with c_action:
            st.markdown("##### Update Status")
            curr_status = ord_row["status"]
            allowed = order_service.VALID_TRANSITIONS.get(curr_status, [])
            
            if allowed:
                for target_st in allowed:
                    if target_st not in ["CANCELLED", "REJECTED"]:
                        if st.button(f"Mark as {target_st}", key=f"btn_{ord_row['id']}_{target_st}", type="primary"):
                            res = order_service.update_order_status(ord_row["id"], target_st)
                            if res["success"]:
                                st.success(res["message"])
                                st.rerun()
                            else:
                                st.error(res["message"])

                # Cancel option
                if "CANCELLED" in allowed or "REJECTED" in allowed:
                    cancel_reason = st.text_input("Cancel / Rejection Reason:", key=f"reason_{ord_row['id']}")
                    if st.button("❌ Cancel / Reject Order", key=f"cancel_{ord_row['id']}"):
                        target = "CANCELLED" if "CANCELLED" in allowed else "REJECTED"
                        res = order_service.update_order_status(ord_row["id"], target, reason=cancel_reason or "Distributor cancelled")
                        if res["success"]:
                            st.warning(res["message"])
                            st.rerun()
            else:
                st.info(f"Order is in final state: {curr_status}")
