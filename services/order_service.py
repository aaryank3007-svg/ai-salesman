import datetime
from typing import List, Dict, Any, Optional
from database.db import get_db, query_all, query_one
from models.schemas import OrderCreateRequest, ParsedOrderItem

class OrderService:
    """Enterprise Order Service handling inventory validation, state transitions, transactions, and audit history."""

    VALID_TRANSITIONS = {
        "PENDING": ["CONFIRMED", "REJECTED", "CANCELLED"],
        "CONFIRMED": ["PACKED", "CANCELLED"],
        "PACKED": ["DISPATCHED", "CANCELLED"],
        "DISPATCHED": ["DELIVERED", "CANCELLED"],
        "DELIVERED": [],
        "REJECTED": [],
        "CANCELLED": []
    }

    @staticmethod
    def generate_order_id() -> str:
        """Generate human-readable stable order ID without collision."""
        today_str = datetime.date.today().strftime("%Y%m%d")
        rows = query_all("SELECT id FROM orders WHERE id LIKE ?", (f"ORD-{today_str}-%",))
        max_num = 0
        for r in rows:
            parts = r["id"].split("-")
            if len(parts) == 3 and parts[2].isdigit():
                max_num = max(max_num, int(parts[2]))
        next_seq = max_num + 1
        return f"ORD-{today_str}-{next_seq:03d}"

    def create_order(self, request: OrderCreateRequest) -> Dict[str, Any]:
        """
        Atomically saves a new order, validates stock, decrements inventory, and logs audit trail.
        Never finalizes without explicit retailer/user confirmation.
        """
        if not request.items:
            return {"success": False, "message": "Cannot create empty order."}

        order_id = self.generate_order_id()
        subtotal = sum(item.item_total for item in request.items)
        discount = round(subtotal * 0.02, 2) if subtotal >= 10000 else 0.0
        total_amount = round(subtotal - discount, 2)

        with get_db() as conn:
            cursor = conn.cursor()

            # 1. Verify stock sufficiency for all items inside transaction
            for item in request.items:
                cursor.execute("SELECT stock_pieces, name FROM products WHERE id = ?", (item.product_id,))
                prod = cursor.fetchone()
                if not prod or prod["stock_pieces"] < item.total_pieces:
                    available = prod["stock_pieces"] if prod else 0
                    prod_name = prod["name"] if prod else item.product_name
                    return {
                        "success": False,
                        "message": f"Stock check failed: {prod_name} only has {available} pieces available."
                    }

            # 2. Insert into orders table
            cursor.execute("""
                INSERT INTO orders (id, retailer_id, status, order_source, original_transcript, raw_language, subtotal, discount, total_amount, is_demo)
                VALUES (?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, 1)
            """, (order_id, request.retailer_id, request.order_source, request.original_transcript, request.raw_language, subtotal, discount, total_amount))

            # 3. Insert order items & decrement stock
            for item in request.items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, ordered_quantity, ordered_unit, pieces_per_unit, total_pieces, unit_price, item_total, is_confirmed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (order_id, item.product_id, item.ordered_quantity, item.ordered_unit, item.pieces_per_unit, item.total_pieces, item.unit_price, item.item_total))

                cursor.execute("""
                    UPDATE products
                    SET stock_pieces = stock_pieces - ?
                    WHERE id = ?
                """, (item.total_pieces, item.product_id))

            # 4. Update retailer outstanding balance
            cursor.execute("""
                UPDATE retailers
                SET current_balance = current_balance + ?
                WHERE id = ?
            """, (total_amount, request.retailer_id))

            # 5. Record status history
            cursor.execute("""
                INSERT INTO order_status_history (order_id, old_status, new_status, changed_by, notes)
                VALUES (?, NULL, 'PENDING', 'AI_ORDER_ENGINE', 'Draft order confirmed by retailer.')
            """, (order_id,))

        return {
            "success": True,
            "order_id": order_id,
            "total_amount": total_amount,
            "items_count": len(request.items),
            "message": f"Order {order_id} placed successfully!"
        }

    def update_order_status(self, order_id: str, new_status: str, changed_by: str = "DISTRIBUTOR", reason: Optional[str] = None) -> Dict[str, Any]:
        """Update order status with state machine rules and inventory restock on cancellation."""
        order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
        if not order:
            return {"success": False, "message": f"Order {order_id} not found."}

        current_status = order["status"]
        allowed = self.VALID_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            return {
                "success": False,
                "message": f"Cannot transition order from {current_status} to {new_status}. Allowed: {', '.join(allowed) if allowed else 'None'}"
            }

        with get_db() as conn:
            cursor = conn.cursor()

            # Update order
            cursor.execute("""
                UPDATE orders
                SET status = ?, cancellation_reason = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, reason, order_id))

            # Record history
            note = f"Status changed to {new_status}. " + (f"Reason: {reason}" if reason else "")
            cursor.execute("""
                INSERT INTO order_status_history (order_id, old_status, new_status, changed_by, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, current_status, new_status, changed_by, note))

            # If cancelled or rejected, restock inventory and credit retailer balance back
            if new_status in ["CANCELLED", "REJECTED"]:
                items = query_all("SELECT product_id, total_pieces FROM order_items WHERE order_id = ?", (order_id,))
                for it in items:
                    cursor.execute("""
                        UPDATE products
                        SET stock_pieces = stock_pieces + ?
                        WHERE id = ?
                    """, (it["total_pieces"], it["product_id"]))

                cursor.execute("""
                    UPDATE retailers
                    SET current_balance = MAX(0, current_balance - ?)
                    WHERE id = ?
                """, (order["total_amount"], order["retailer_id"]))

        return {
            "success": True,
            "order_id": order_id,
            "old_status": current_status,
            "new_status": new_status,
            "message": f"Order {order_id} updated to {new_status}."
        }

    def get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Fetch order with customer details, order line items, and audit history."""
        order = query_one("""
            SELECT o.*, r.shop_name, r.owner_name, r.phone, r.address, r.credit_limit, r.current_balance
            FROM orders o
            JOIN retailers r ON o.retailer_id = r.id
            WHERE o.id = ?
        """, (order_id,))
        if not order:
            return None

        items = query_all("""
            SELECT oi.*, p.name as product_name, p.brand, p.variant, p.mrp
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,))

        history = query_all("""
            SELECT * FROM order_status_history
            WHERE order_id = ?
            ORDER BY changed_at ASC
        """, (order_id,))

        return {
            "order": order,
            "items": items,
            "history": history
        }
