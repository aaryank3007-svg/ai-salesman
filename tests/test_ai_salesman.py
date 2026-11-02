import unittest
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.db import init_db, query_one, query_all
from database.seed import seed_database
from services.sku_matcher import SkuMatcher
from services.order_parser import OrderParser
from services.order_service import OrderService
from services.sarvam_client import SarvamService
from services.analytics_service import AnalyticsService
from models.schemas import OrderCreateRequest, ParsedOrderItem
from utils.validators import validate_quantity, validate_sku, check_stock_sufficiency

class TestAISalesman(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed fresh test database."""
        seed_database()
        cls.sku_matcher = SkuMatcher()
        cls.order_service = OrderService()
        cls.analytics_service = AnalyticsService()
        # Initialize parser in Demo mode to test deterministic logic
        cls.demo_sarvam = SarvamService(force_demo=True)
        cls.order_parser = OrderParser(sarvam_client=cls.demo_sarvam)

    def test_01_product_matching_exact(self):
        """Test exact matching of FMCG product names and regional aliases."""
        res = self.sku_matcher.match_product("Colgate Strong Teeth")
        self.assertEqual(res["status"], "EXACT")
        self.assertEqual(res["matched_product"]["id"], "SKU-COLG-ST-100")

        # Test Marathi/Hindi alias
        res_alias = self.sku_matcher.match_product("मॅक्सफ्रेश")
        self.assertEqual(res_alias["status"], "EXACT")
        self.assertEqual(res_alias["matched_product"]["id"], "SKU-COLG-MF-150")

        # Test brand match
        res_parle = self.sku_matcher.match_product("Parle-G")
        self.assertEqual(res_parle["status"], "EXACT")
        self.assertEqual(res_parle["matched_product"]["id"], "SKU-PARLE-G-1KG")

    def test_02_ambiguous_product_matching(self):
        """Test that generic mention 'Colgate' flags as AMBIGUOUS and lists choices."""
        res = self.sku_matcher.match_product("Colgate")
        self.assertEqual(res["status"], "AMBIGUOUS")
        self.assertGreaterEqual(len(res["candidate_products"]), 2)
        candidate_ids = [c["id"] for c in res["candidate_products"]]
        self.assertIn("SKU-COLG-ST-100", candidate_ids)
        self.assertIn("SKU-COLG-MF-150", candidate_ids)

    def test_03_quantity_extraction(self):
        """Test quantity extraction with digits and words in Hindi/Marathi."""
        transcript = "Colgate Strong Teeth ke 10 cartons aur MaxFresh ke 5 cartons"
        parsed = self.order_parser.parse_order_text(transcript, mode="DEMO")
        self.assertEqual(len(parsed.items), 2)
        self.assertEqual(parsed.items[0].ordered_quantity, 10.0)
        self.assertEqual(parsed.items[1].ordered_quantity, 5.0)

    def test_04_packaging_conversion_distinct_per_sku(self):
        """Test that different SKUs have different carton piece counts and pricing."""
        # Colgate Strong Teeth: 1 carton = 72 pcs
        c_st = query_one("SELECT pieces_per_unit FROM packaging_units WHERE product_id = 'SKU-COLG-ST-100' AND unit_name = 'carton'")
        self.assertEqual(c_st["pieces_per_unit"], 72)

        # Colgate MaxFresh: 1 carton = 48 pcs
        c_mf = query_one("SELECT pieces_per_unit FROM packaging_units WHERE product_id = 'SKU-COLG-MF-150' AND unit_name = 'carton'")
        self.assertEqual(c_mf["pieces_per_unit"], 48)

        # Surf Excel: 1 carton = 16 pcs
        c_se = query_one("SELECT pieces_per_unit FROM packaging_units WHERE product_id = 'SKU-SURF-EW-1KG' AND unit_name = 'carton'")
        self.assertEqual(c_se["pieces_per_unit"], 16)

    def test_05_unsupported_packaging_clarification(self):
        """Test asking for box unit on MaxFresh (which only comes in cartons/dozens/pieces)."""
        transcript = "MaxFresh ke 2 box bhej do"
        parsed = self.order_parser.parse_order_text(transcript, mode="DEMO")
        self.assertEqual(len(parsed.items), 1)
        self.assertTrue(parsed.items[0].needs_packaging_clarification)
        self.assertFalse(parsed.is_ready_for_confirmation)

    def test_06_invalid_quantity_validation(self):
        """Test validator catches negative and extreme quantities."""
        valid, msg = validate_quantity(-5)
        self.assertFalse(valid)
        valid_large, msg_large = validate_quantity(10000)
        self.assertFalse(valid_large)
        valid_ok, _ = validate_quantity(10)
        self.assertTrue(valid_ok)

    def test_07_price_calculation_and_discount(self):
        """Test accurate pricing and trade schemes calculation."""
        transcript = "Colgate Strong Teeth ke 10 cartons, MaxFresh ke 5 cartons aur toothbrush ke 2 dozen bhej dena."
        parsed = self.order_parser.parse_order_text(transcript, mode="DEMO")
        # 10 cartons * 3960 = 39,600
        # 5 cartons * 4416 = 22,080
        # 2 dozen * 264 = 528
        # Subtotal = 62,208
        self.assertAlmostEqual(parsed.subtotal, 62208.0, places=1)
        # 2% discount on subtotal > 10,000 = 1244.16
        self.assertAlmostEqual(parsed.discount, 1244.16, places=1)
        self.assertAlmostEqual(parsed.total_amount, 60963.84, places=1)

    def test_08_stock_validation(self):
        """Test stock sufficiency checker."""
        ok, avail = check_stock_sufficiency("SKU-TATA-TEA-500", 20)
        self.assertTrue(ok)
        ok_fail, avail = check_stock_sufficiency("SKU-TATA-TEA-500", 5000)
        self.assertFalse(ok_fail)

    def test_09_draft_order_confirmation_and_persistence(self):
        """Test that confirming a draft order persists to SQLite and decrements stock."""
        initial_stock = query_one("SELECT stock_pieces FROM products WHERE id = 'SKU-PARLE-G-1KG'")["stock_pieces"]

        req_item = ParsedOrderItem(
            product_id="SKU-PARLE-G-1KG",
            product_name="Parle-G Glucose Biscuits 1kg Pack",
            brand="Parle",
            variant="1kg Family Pack",
            ordered_quantity=2.0,
            ordered_unit="carton",
            pieces_per_unit=20,
            total_pieces=40,
            unit_price=1560.0,
            item_total=3120.0,
            stock_available_pieces=initial_stock,
            is_in_stock=True
        )

        create_req = OrderCreateRequest(
            retailer_id="RET-101",
            items=[req_item],
            order_source="TEST_SUITE"
        )

        result = self.order_service.create_order(create_req)
        self.assertTrue(result["success"])
        order_id = result["order_id"]

        # Check DB persistence
        order_row = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
        self.assertIsNotNone(order_row)
        self.assertEqual(order_row["retailer_id"], "RET-101")

        # Check stock decrement
        updated_stock = query_one("SELECT stock_pieces FROM products WHERE id = 'SKU-PARLE-G-1KG'")["stock_pieces"]
        self.assertEqual(updated_stock, initial_stock - 40)

        # Check order status history entry
        hist = query_all("SELECT * FROM order_status_history WHERE order_id = ?", (order_id,))
        self.assertGreaterEqual(len(hist), 1)

    def test_10_order_status_transitions(self):
        """Test valid state transitions and cancellation restock."""
        # Create an order
        req_item = ParsedOrderItem(
            product_id="SKU-BRIT-GD-BTR",
            product_name="Britannia Good Day",
            brand="Britannia",
            variant="200g Butter",
            ordered_quantity=1.0,
            ordered_unit="carton",
            pieces_per_unit=36,
            total_pieces=36,
            unit_price=1512.0,
            item_total=1512.0,
            stock_available_pieces=180,
            is_in_stock=True
        )
        res = self.order_service.create_order(OrderCreateRequest(retailer_id="RET-102", items=[req_item]))
        order_id = res["order_id"]

        # Advance status: PENDING -> CONFIRMED -> PACKED
        s1 = self.order_service.update_order_status(order_id, "CONFIRMED")
        self.assertTrue(s1["success"])
        s2 = self.order_service.update_order_status(order_id, "PACKED")
        self.assertTrue(s2["success"])

        # Try invalid leap: PACKED -> DELIVERED (must go through DISPATCHED)
        s_invalid = self.order_service.update_order_status(order_id, "DELIVERED")
        self.assertFalse(s_invalid["success"])

        # Cancel order and verify restock
        stock_before_cancel = query_one("SELECT stock_pieces FROM products WHERE id = 'SKU-BRIT-GD-BTR'")["stock_pieces"]
        s_cancel = self.order_service.update_order_status(order_id, "CANCELLED", reason="Customer request")
        self.assertTrue(s_cancel["success"])
        stock_after_cancel = query_one("SELECT stock_pieces FROM products WHERE id = 'SKU-BRIT-GD-BTR'")["stock_pieces"]
        self.assertEqual(stock_after_cancel, stock_before_cancel + 36)

    def test_11_analytics_assistant_queries(self):
        """Test safe predefined analytics queries."""
        r1 = self.analytics_service.answer_question("How many orders came today?")
        self.assertEqual(r1.metric_type, "orders_today")

        r2 = self.analytics_service.answer_question("Which products are selling the most?")
        self.assertEqual(r2.metric_type, "top_products")

        r3 = self.analytics_service.answer_question("Which products are running low?")
        self.assertEqual(r3.metric_type, "low_stock")

        r4 = self.analytics_service.answer_question("Show my top 10 retailers.")
        self.assertEqual(r4.metric_type, "top_retailers")

    def test_12_demo_mode_fallback(self):
        """Test that Demo mode returns simulated data cleanly without crashing."""
        demo_client = SarvamService(force_demo=True)
        self.assertFalse(demo_client.is_live)
        self.assertIn("DEMO MODE", demo_client.get_mode_label())

        # Audio transcription fallback
        tr = demo_client.transcribe_audio(b"fake_audio_bytes", language_code="hi-IN")
        self.assertEqual(tr["mode"], "DEMO")
        self.assertTrue(len(tr["transcript"]) > 0)

        # TTS fallback
        tts = demo_client.text_to_speech("Test speech")
        self.assertEqual(tts["mode"], "DEMO")
        self.assertTrue(len(tts["audio_bytes"]) > 0)

if __name__ == "__main__":
    unittest.main()
