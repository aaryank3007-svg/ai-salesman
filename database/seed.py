import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.db import get_db, init_db

def seed_database():
    """Populate database with 10 FMCG products, 6 retailers, and 8 sample orders (DEMO DATA)."""
    init_db(force_recreate=True)
    
    products_data = [
        ("SKU-COLG-ST-100", "Colgate Strong Teeth Dental Cream 100g", "Colgate-Palmolive", "Oral Care", "100g Tube", "piece", 65.0, 55.0, 720, 100, "colgate strong teeth, colgate red, colgate paste, कोलगेट स्ट्रॉन्ग टीथ, कोलगेट पेस्ट", "toothpaste"),
        ("SKU-COLG-MF-150", "Colgate MaxFresh Blue Gel 150g", "Colgate-Palmolive", "Oral Care", "150g Peppermint", "piece", 110.0, 92.0, 240, 50, "maxfresh, colgate maxfresh, blue gel, मॅक्सफ्रेश, मैक्सफ्रेश", "toothpaste"),
        ("SKU-ORAL-TB-SZ", "Oral-B Shiny Clean Toothbrush Medium", "P&G", "Oral Care", "Medium Bristle", "piece", 30.0, 22.0, 288, 50, "toothbrush, oral b, colgate brush, ब्रश, टूथब्रश, tooth brush", "toothbrush"),
        ("SKU-PARLE-G-1KG", "Parle-G Glucose Biscuits 1kg Pack", "Parle", "Biscuits & Bakery", "1kg Family Pack", "piece", 90.0, 78.0, 100, 30, "parle-g, parle g, parle biscuit, पार्ले जी, बिस्किट, glucose biscuit", "biscuit"),
        ("SKU-BRIT-GD-BTR", "Britannia Good Day Butter Cookies 200g", "Britannia", "Biscuits & Bakery", "200g Butter", "piece", 50.0, 42.0, 180, 40, "good day, britannia good day, butter cookie, गुड डे, गुडडे", "biscuit"),
        ("SKU-MAGGI-2M-70", "Maggi 2-Minute Masala Noodles 70g", "Nestle", "Instant Food", "70g Pouch", "piece", 14.0, 11.50, 480, 100, "maggi, masala noodles, 2 minute noodles, मैगी, मॅगी, noodles", "noodles"),
        ("SKU-TATA-TEA-500", "Tata Tea Gold Premium Tea 500g", "Tata Consumer", "Beverages", "500g Poly Pack", "piece", 320.0, 275.0, 48, 20, "tata tea, tata gold, chai patti, टाटा टी, चहा पावडर, चाय", "tea"),
        ("SKU-DETT-SP-125", "Dettol Original Antiseptic Bathing Soap 125g", "Reckitt", "Personal Hygiene", "125g Bar", "piece", 55.0, 46.0, 162, 40, "dettol, dettol soap, sabun, डेटॉल, साबण, detol", "soap"),
        ("SKU-SURF-EW-1KG", "Surf Excel Easy Wash Detergent Powder 1kg", "Hindustan Unilever", "Laundry Care", "1kg Bag", "piece", 145.0, 122.0, 64, 25, "surf excel, easy wash, detergent powder, सर्फ एक्सेल, पावडर, surf", "detergent"),
        ("SKU-FORT-OIL-1L", "Fortune Sunlite Refined Sunflower Oil 1L", "Adani Wilmar", "Cooking & Edible Oils", "1L Pouch", "piece", 160.0, 138.0, 90, 30, "fortune oil, sunflower oil, tel, फॉर्च्यून तेल, तेल, refined oil", "oil")
    ]

    packaging_data = [
        # Colgate Strong Teeth: Carton=72, Box=24, Dozen=12, Piece=1
        ("SKU-COLG-ST-100", "carton", 72, 3960.0),
        ("SKU-COLG-ST-100", "box", 24, 1320.0),
        ("SKU-COLG-ST-100", "dozen", 12, 660.0),
        ("SKU-COLG-ST-100", "piece", 1, 55.0),
        
        # MaxFresh: Carton=48, Dozen=12, Piece=1 (NO box!)
        ("SKU-COLG-MF-150", "carton", 48, 4416.0),
        ("SKU-COLG-MF-150", "dozen", 12, 1104.0),
        ("SKU-COLG-MF-150", "piece", 1, 92.0),
        
        # Toothbrush: Carton=144, Dozen=12, Piece=1
        ("SKU-ORAL-TB-SZ", "carton", 144, 3168.0),
        ("SKU-ORAL-TB-SZ", "dozen", 12, 264.0),
        ("SKU-ORAL-TB-SZ", "piece", 1, 22.0),
        
        # Parle-G: Carton=20, Piece=1
        ("SKU-PARLE-G-1KG", "carton", 20, 1560.0),
        ("SKU-PARLE-G-1KG", "piece", 1, 78.0),
        
        # Good Day: Carton=36, Dozen=12, Piece=1
        ("SKU-BRIT-GD-BTR", "carton", 36, 1512.0),
        ("SKU-BRIT-GD-BTR", "dozen", 12, 504.0),
        ("SKU-BRIT-GD-BTR", "piece", 1, 42.0),
        
        # Maggi: Carton=96, Box=24, Piece=1
        ("SKU-MAGGI-2M-70", "carton", 96, 1104.0),
        ("SKU-MAGGI-2M-70", "box", 24, 276.0),
        ("SKU-MAGGI-2M-70", "piece", 1, 11.50),
        
        # Tata Tea: Carton=24, Piece=1
        ("SKU-TATA-TEA-500", "carton", 24, 6600.0),
        ("SKU-TATA-TEA-500", "piece", 1, 275.0),
        
        # Dettol Soap: Carton=54, Box=18, Piece=1
        ("SKU-DETT-SP-125", "carton", 54, 2484.0),
        ("SKU-DETT-SP-125", "box", 18, 828.0),
        ("SKU-DETT-SP-125", "piece", 1, 46.0),
        
        # Surf Excel: Carton=16, Piece=1
        ("SKU-SURF-EW-1KG", "carton", 16, 1952.0),
        ("SKU-SURF-EW-1KG", "piece", 1, 122.0),
        
        # Fortune Oil: Carton=15, Piece=1
        ("SKU-FORT-OIL-1L", "carton", 15, 2070.0),
        ("SKU-FORT-OIL-1L", "piece", 1, 138.0)
    ]

    retailers_data = [
        ("RET-101", "Lakshmi Kirana & General Stores", "Ramesh Gupta", "+91 98220 12345", "Shop 4, Market Yard, Pune - 411037", "Standard", 75000.0, 12400.0, 1),
        ("RET-102", "Shri Ganesh Supermarket", "Santosh Kadam", "+91 98190 23456", "Plot 12, Sector 17, Vashi, Navi Mumbai - 400703", "Wholesale", 150000.0, 34200.0, 1),
        ("RET-103", "Balaji Traders", "Venkat Raman", "+91 98900 34567", "Main Road, Itwari, Nagpur - 440002", "Standard", 50000.0, 8500.0, 1),
        ("RET-104", "Mahaveer Provision Stores", "Ashok Jain", "+91 98500 45678", "Near Bus Stand, Panchavati, Nashik - 422003", "Standard", 60000.0, 18900.0, 1),
        ("RET-105", "Sai Krupa Daily Needs", "Mahendra Patil", "+91 98230 56789", "Station Road, Shahupuri, Kolhapur - 416001", "Wholesale", 100000.0, 5200.0, 1),
        ("RET-106", "Apna Bazaar Kirana", "Imran Khan", "+91 98600 67890", "Gulmandi, Chhatrapati Sambhajinagar - 431001", "Standard", 40000.0, 0.0, 1)
    ]

    schemes_data = [
        ("SCH-01", "Monsoon Dhamaaka: Buy 5 Cartons Colgate ST, Get 1 Dozen Toothbrush FREE", "SKU-COLG-ST-100", 5, "SKU-ORAL-TB-SZ", 12, 2.0, 1),
        ("SCH-02", "Tea & Biscuit Combo: Buy 2 Cartons Tata Tea, Get 5% Off", "SKU-TATA-TEA-500", 2, None, 0, 5.0, 1),
        ("SCH-03", "Maggi Bulk Bonanza: Buy 3 Cartons Maggi, Get Rs 150 Cash Discount", "SKU-MAGGI-2M-70", 3, None, 0, 3.5, 1)
    ]

    orders_data = [
        ("ORD-20261101-001", "RET-101", "DELIVERED", "RETAILER_PORTAL", "Direct web order", "en-IN", 12540.0, 0.0, 12540.0, None, "2026-11-01 10:15:00"),
        ("ORD-20261101-002", "RET-102", "DELIVERED", "VOICE_AI", "Bhaiya 2 carton Colgate MaxFresh aur 4 carton Maggi bhej do", "hi-IN", 13248.0, 200.0, 13048.0, None, "2026-11-01 11:30:00"),
        ("ORD-20261101-003", "RET-103", "DISPATCHED", "VOICE_AI", "Namaste, Tata Tea che 2 carton aani Good Day che 3 carton pathva", "mr-IN", 17736.0, 350.0, 17386.0, None, "2026-11-01 16:45:00"),
        ("ORD-20261102-004", "RET-104", "PACKED", "MANUAL", "Phone order recorded by sales rep", "hi-IN", 6340.0, 0.0, 6340.0, None, "2026-11-02 09:20:00"),
        ("ORD-20261102-005", "RET-105", "CONFIRMED", "RETAILER_PORTAL", "Bulk monthly restock", "en-IN", 9870.0, 150.0, 9720.0, None, "2026-11-02 10:40:00"),
        ("ORD-20261102-006", "RET-101", "PENDING", "VOICE_AI", "Namaste bhaiya, mujhe Colgate Strong Teeth ke 10 cartons, MaxFresh ke 5 cartons aur toothbrush ke 2 dozen bhej dena.", "hi-IN", 62208.0, 500.0, 61708.0, None, "2026-11-02 12:10:00"),
        ("ORD-20261102-007", "RET-102", "PENDING", "VOICE_AI", "Aamhi 3 peti Surf Excel aani 2 box Dettol sabun magvat aahot", "mr-IN", 7512.0, 100.0, 7412.0, None, "2026-11-02 12:45:00"),
        ("ORD-20261028-008", "RET-106", "CANCELLED", "VOICE_AI", "5 carton Parle-G order", "hi-IN", 7800.0, 0.0, 7800.0, "Shop renovation - requested delay", "2026-10-28 14:00:00")
    ]

    order_items_data = [
        # ORD-001
        ("ORD-20261101-001", "SKU-COLG-ST-100", 2.0, "carton", 72, 144, 3960.0, 7920.0),
        ("ORD-20261101-001", "SKU-DETT-SP-125", 1.0, "carton", 54, 54, 2484.0, 2484.0),
        ("ORD-20261101-001", "SKU-FORT-OIL-1L", 1.0, "carton", 15, 15, 2070.0, 2070.0),

        # ORD-002
        ("ORD-20261101-002", "SKU-COLG-MF-150", 2.0, "carton", 48, 96, 4416.0, 8832.0),
        ("ORD-20261101-002", "SKU-MAGGI-2M-70", 4.0, "carton", 96, 384, 1104.0, 4416.0),

        # ORD-003
        ("ORD-20261101-003", "SKU-TATA-TEA-500", 2.0, "carton", 24, 48, 6600.0, 13200.0),
        ("ORD-20261101-003", "SKU-BRIT-GD-BTR", 3.0, "carton", 36, 108, 1512.0, 4536.0),

        # ORD-004
        ("ORD-20261102-004", "SKU-PARLE-G-1KG", 3.0, "carton", 20, 60, 1560.0, 4680.0),
        ("ORD-20261102-004", "SKU-ORAL-TB-SZ", 6.0, "dozen", 12, 72, 264.0, 1584.0),

        # ORD-005
        ("ORD-20261102-005", "SKU-SURF-EW-1KG", 4.0, "carton", 16, 64, 1952.0, 7808.0),
        ("ORD-20261102-005", "SKU-FORT-OIL-1L", 1.0, "carton", 15, 15, 2070.0, 2070.0),

        # ORD-006 (from benchmark prompt: 10 cartons Colgate ST, 5 cartons MaxFresh, 2 dozen toothbrush)
        ("ORD-20261102-006", "SKU-COLG-ST-100", 10.0, "carton", 72, 720, 3960.0, 39600.0),
        ("ORD-20261102-006", "SKU-COLG-MF-150", 5.0, "carton", 48, 240, 4416.0, 22080.0),
        ("ORD-20261102-006", "SKU-ORAL-TB-SZ", 2.0, "dozen", 12, 24, 264.0, 528.0),

        # ORD-007 (3 cartons Surf Excel, 2 boxes Dettol soap)
        ("ORD-20261102-007", "SKU-SURF-EW-1KG", 3.0, "carton", 16, 48, 1952.0, 5856.0),
        ("ORD-20261102-007", "SKU-DETT-SP-125", 2.0, "box", 18, 36, 828.0, 1656.0),

        # ORD-008
        ("ORD-20261028-008", "SKU-PARLE-G-1KG", 5.0, "carton", 20, 100, 1560.0, 7800.0)
    ]

    history_data = [
        ("ORD-20261101-001", "PENDING", "CONFIRMED", "DISTRIBUTOR", "Payment verified", "2026-11-01 10:30:00"),
        ("ORD-20261101-001", "CONFIRMED", "PACKED", "DISTRIBUTOR", "Dispatched to loading dock", "2026-11-01 12:00:00"),
        ("ORD-20261101-001", "PACKED", "DELIVERED", "DISTRIBUTOR", "Signed receipt by Ramesh Gupta", "2026-11-01 16:30:00"),
        ("ORD-20261101-002", "CONFIRMED", "DELIVERED", "DISTRIBUTOR", "Delivered by delivery van 2", "2026-11-01 18:00:00"),
        ("ORD-20261101-003", "CONFIRMED", "DISPATCHED", "DISTRIBUTOR", "Out for delivery via tempo", "2026-11-01 17:30:00"),
        ("ORD-20261102-004", "CONFIRMED", "PACKED", "DISTRIBUTOR", "Packed in crates", "2026-11-02 10:00:00"),
        ("ORD-20261102-005", "PENDING", "CONFIRMED", "DISTRIBUTOR", "Auto-confirmed under credit limit", "2026-11-02 11:00:00")
    ]

    with get_db() as conn:
        cursor = conn.cursor()
        
        # Products
        cursor.executemany("""
            INSERT INTO products (id, name, brand, category, variant, base_unit, mrp, distributor_price, stock_pieces, min_stock_threshold, aliases, image_url, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, products_data)

        # Packaging
        cursor.executemany("""
            INSERT INTO packaging_units (product_id, unit_name, pieces_per_unit, unit_price, is_allowed)
            VALUES (?, ?, ?, ?, 1)
        """, packaging_data)

        # Retailers
        cursor.executemany("""
            INSERT INTO retailers (id, shop_name, owner_name, phone, address, price_group, credit_limit, current_balance, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, retailers_data)

        # Schemes
        cursor.executemany("""
            INSERT INTO schemes (id, name, product_id, min_quantity, free_product_id, free_quantity, discount_percent, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, schemes_data)

        # Orders
        for o in orders_data:
            cursor.execute("""
                INSERT INTO orders (id, retailer_id, status, order_source, original_transcript, raw_language, subtotal, discount, total_amount, cancellation_reason, is_demo, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (o[0], o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[8], o[9], o[10], o[10]))

        # Order Items
        cursor.executemany("""
            INSERT INTO order_items (order_id, product_id, ordered_quantity, ordered_unit, pieces_per_unit, total_pieces, unit_price, item_total, is_confirmed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, order_items_data)

        # History
        for h in history_data:
            cursor.execute("""
                INSERT INTO order_status_history (order_id, old_status, new_status, changed_by, notes, changed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, h)

    print("[SUCCESS] Database seeded with 10 products, 6 retailers, 8 orders (DEMO DATA).")

if __name__ == "__main__":
    seed_database()
