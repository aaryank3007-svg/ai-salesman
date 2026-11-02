import re
import json
from typing import List, Dict, Any, Optional
from utils.config import UNIT_MAPPINGS, WORD_TO_NUMBER
from services.sku_matcher import SkuMatcher
from database.db import query_all, query_one
from models.schemas import ParsedOrderItem, OrderParseResult

class OrderParser:
    """Dedicated AI Order Processing Engine that translates multilingual retailer speech into validated orders."""

    UNIT_REGEX = r'(?:carton(?:s)?|peti(?:s)?|box(?:es)?|dabba(?:s)?|dabbe|dozen(?:s)?|darjan|piece(?:s)?|pcs|packet(?:s)?|pkt(?:s)?|पेटी|पेट्या|खोके|खोका|पुडे|पुडा|डब्बे|डब्बा|बॉक्स|दर्जन|डझन|नग|पीस|पॅकेट)'

    def __init__(self, sarvam_client=None):
        self.sku_matcher = SkuMatcher()
        self.sarvam_client = sarvam_client

    def parse_order_text(self, transcript: str, language_code: str = "hi-IN", mode: str = "LIVE") -> OrderParseResult:
        if not transcript or not transcript.strip():
            return OrderParseResult(
                transcript="",
                detected_language=language_code,
                mode=mode,
                items=[],
                clarification_questions=["No speech transcript provided. Please speak or type your order."],
                is_ready_for_confirmation=False
            )

        extracted_raw_items = []

        if mode == "LIVE" and self.sarvam_client and getattr(self.sarvam_client, "is_live", False):
            extracted_raw_items = self._extract_with_sarvam_llm(transcript)

        if not extracted_raw_items:
            extracted_raw_items = self._extract_with_rule_engine(transcript)

        parsed_items: List[ParsedOrderItem] = []
        unmatched: List[str] = []
        clarifications: List[str] = []

        for raw in extracted_raw_items:
            prod_name = raw.get("product", "").strip()
            qty = float(raw.get("quantity", 1))
            unit = self._normalize_unit(raw.get("unit", "carton"))
            variant_hint = raw.get("variant", None)

            match_res = self.sku_matcher.match_product(prod_name, variant_hint)

            if match_res["status"] == "NOT_FOUND":
                unmatched.append(prod_name)
                clarifications.append(f"We could not find '{prod_name}' in the distributor catalogue.")
                continue

            elif match_res["status"] == "AMBIGUOUS":
                candidate_opts = [
                    {"id": c["id"], "name": c["name"], "variant": c["variant"]}
                    for c in match_res["candidate_products"]
                ]
                clarifications.append(match_res["message"])
                parsed_items.append(ParsedOrderItem(
                    product_id="AMBIGUOUS",
                    product_name=prod_name,
                    brand="Multiple",
                    variant="Unspecified",
                    ordered_quantity=qty,
                    ordered_unit=unit,
                    pieces_per_unit=1,
                    total_pieces=int(qty),
                    unit_price=0.0,
                    item_total=0.0,
                    stock_available_pieces=0,
                    is_in_stock=False,
                    is_ambiguous=True,
                    ambiguous_options=candidate_opts,
                    needs_packaging_clarification=False,
                    clarification_message=match_res["message"]
                ))
                continue

            # Exact match
            prod = match_res["matched_product"]
            prod_id = prod["id"]

            pkg_rule = query_one(
                "SELECT * FROM packaging_units WHERE product_id = ? AND LOWER(unit_name) = LOWER(?) AND is_allowed = 1",
                (prod_id, unit)
            )

            if not pkg_rule:
                allowed_units = query_all(
                    "SELECT unit_name, pieces_per_unit FROM packaging_units WHERE product_id = ? AND is_allowed = 1",
                    (prod_id,)
                )
                allowed_desc = ", ".join([f"{u['unit_name']} ({u['pieces_per_unit']} pcs)" for u in allowed_units])
                pkg_msg = f"{prod['name']} is not packaged in '{unit}'. Available units: {allowed_desc}."
                clarifications.append(pkg_msg)

                fallback_pkg = allowed_units[0] if allowed_units else {"pieces_per_unit": 1, "unit_name": "piece"}
                ppu = fallback_pkg["pieces_per_unit"]
                total_pcs = int(qty * ppu)
                unit_price = prod["distributor_price"] * ppu
                item_total = round(qty * unit_price, 2)
                stock_avail = prod["stock_pieces"]

                parsed_items.append(ParsedOrderItem(
                    product_id=prod_id,
                    product_name=prod["name"],
                    brand=prod["brand"],
                    variant=prod["variant"],
                    ordered_quantity=qty,
                    ordered_unit=unit,
                    pieces_per_unit=ppu,
                    total_pieces=total_pcs,
                    unit_price=unit_price,
                    item_total=item_total,
                    stock_available_pieces=stock_avail,
                    is_in_stock=(stock_avail >= total_pcs),
                    is_ambiguous=False,
                    needs_packaging_clarification=True,
                    clarification_message=pkg_msg
                ))
            else:
                ppu = pkg_rule["pieces_per_unit"]
                total_pcs = int(qty * ppu)
                unit_price = pkg_rule["unit_price"]
                item_total = round(qty * unit_price, 2)
                stock_avail = prod["stock_pieces"]
                is_in_stock = (stock_avail >= total_pcs)

                if not is_in_stock:
                    stock_msg = f"Insufficient stock for {prod['name']} ({qty} {unit} = {total_pcs} pcs). Available: {stock_avail} pcs."
                    clarifications.append(stock_msg)

                parsed_items.append(ParsedOrderItem(
                    product_id=prod_id,
                    product_name=prod["name"],
                    brand=prod["brand"],
                    variant=prod["variant"],
                    ordered_quantity=qty,
                    ordered_unit=unit,
                    pieces_per_unit=ppu,
                    total_pieces=total_pcs,
                    unit_price=unit_price,
                    item_total=item_total,
                    stock_available_pieces=stock_avail,
                    is_in_stock=is_in_stock,
                    is_ambiguous=False,
                    needs_packaging_clarification=False,
                    clarification_message=None if is_in_stock else f"Only {stock_avail} pieces available in warehouse."
                ))

        subtotal = sum(item.item_total for item in parsed_items if not item.is_ambiguous and not item.needs_packaging_clarification)
        discount = round(subtotal * 0.02, 2) if subtotal >= 10000 else 0.0
        total_amount = round(subtotal - discount, 2)

        applied_schemes = []
        if discount > 0:
            applied_schemes.append(f"🎁 2% Distributor Bulk Order Discount (Saved ₹{discount:,.2f})")
        
        # Check active promotional schemes
        for it in parsed_items:
            sch = query_one("SELECT * FROM schemes WHERE product_id = ? AND is_active = 1", (it.product_id,))
            if sch and it.ordered_unit == "carton" and it.ordered_quantity >= sch["min_quantity"]:
                if sch["free_product_id"]:
                    free_prod = query_one("SELECT name FROM products WHERE id = ?", (sch["free_product_id"],))
                    fp_name = free_prod["name"] if free_prod else "Bonus SKU"
                    applied_schemes.append(f"🎉 Promotion: {sch['name']} (Qualified for {sch['free_quantity']} Free Pieces of {fp_name})")

        ready = (
            len(parsed_items) > 0 and
            all(not item.is_ambiguous for item in parsed_items) and
            all(not item.needs_packaging_clarification for item in parsed_items) and
            all(item.is_in_stock for item in parsed_items)
        )

        return OrderParseResult(
            transcript=transcript,
            detected_language=language_code,
            mode=mode,
            items=parsed_items,
            unmatched_queries=unmatched,
            clarification_questions=clarifications,
            applied_schemes=applied_schemes,
            subtotal=subtotal,
            discount=discount,
            total_amount=total_amount,
            is_ready_for_confirmation=ready
        )

    def _normalize_unit(self, raw_unit: str) -> str:
        u = raw_unit.lower().strip()
        # strip plural s or es
        if u.endswith("es"):
            base = u[:-2]
            if base in UNIT_MAPPINGS:
                return UNIT_MAPPINGS[base]
        elif u.endswith("s"):
            base = u[:-1]
            if base in UNIT_MAPPINGS:
                return UNIT_MAPPINGS[base]
        return UNIT_MAPPINGS.get(u, "carton")

    def _extract_with_sarvam_llm(self, transcript: str) -> List[Dict[str, Any]]:
        system_prompt = (
            "You are an Indian FMCG order parser. Extract items from Indian shopkeeper speech (Hindi, Marathi, English). "
            "Return ONLY valid JSON array with keys: 'product' (string), 'quantity' (number), 'unit' (carton/box/dozen/piece), 'variant' (optional string). "
            "Example: [{\"product\": \"Colgate Strong Teeth\", \"quantity\": 10, \"unit\": \"carton\"}]"
        )
        try:
            res = self.sarvam_client.chat_query(f"Parse this order: \"{transcript}\"", system_prompt)
            if res.get("success") and res.get("content"):
                raw_text = res["content"]
                match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
        except Exception as e:
            print(f"[WARN] Sarvam LLM parse failed: {e}")
        return []

    def _extract_with_rule_engine(self, transcript: str) -> List[Dict[str, Any]]:
        text = transcript.lower()

        # Clean common trailing/leading filler sentences first
        text = re.sub(r'\b(namaste|bhaiya|mujhe|aamhi|please|send|deliver|today|chahiye|lavkar)\b', '', text)
        text = re.sub(r'\b(bhej dena|bhej do|pathva|pathvun dya|kar do|de do|magvat aahot)\b', '', text)

        for word, num in WORD_TO_NUMBER.items():
            pattern = r'\b' + re.escape(word) + r'\b'
            text = re.sub(pattern, str(num), text)

        segments = re.split(r'[,+]|\baur\b|\baani\b|\band\b|\bva\b', text)
        results = []

        unit_p = r'(' + self.UNIT_REGEX + r')'

        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue

            # Pattern 1: <product> (ke/che/of) <quantity> <unit>
            m1 = re.search(r'(.+?)\s*(?:ke|che|ka|of|ze)?\s*(\d+(?:\.\d+)?)\s*' + unit_p, seg)
            # Pattern 2: <quantity> <unit> (ke/che/of) <product>
            m2 = re.search(r'(\d+(?:\.\d+)?)\s*' + unit_p + r'\s*(?:ke|che|of|ze)?\s*(.+)', seg)

            if m1:
                prod = self._clean_filler_words(m1.group(1))
                qty = float(m1.group(2))
                unit = m1.group(3).strip()
                if prod:
                    results.append({"product": prod, "quantity": qty, "unit": unit})
            elif m2:
                qty = float(m2.group(1))
                unit = m2.group(2).strip()
                prod = self._clean_filler_words(m2.group(3))
                if prod:
                    results.append({"product": prod, "quantity": qty, "unit": unit})
            else:
                num_match = re.search(r'(\d+(?:\.\d+)?)', seg)
                qty = float(num_match.group(1)) if num_match else 1.0
                unit_match = re.search(unit_p, seg)
                unit = unit_match.group(1) if unit_match else "carton"
                clean_seg = self._clean_filler_words(seg)
                if clean_seg:
                    results.append({"product": clean_seg, "quantity": qty, "unit": unit})

        return results

    def _clean_filler_words(self, text: str) -> str:
        fillers = [
            r'\bnamaste\b', r'\bbhaiya\b', r'\bmujhe\b', r'\bbhej dena\b', r'\bbhej do\b',
            r'\bpathva\b', r'\bpathvun dya\b', r'\baamhi\b', r'\bmagvat aahot\b',
            r'\bplease\b', r'\bsend\b', r'\bdeliver\b', r'\btoday\b', r'\bke\b', r'\bche\b',
            r'\bka\b', r'\bof\b', r'\bchahiye\b', r'\blavkar\b', r'\bdelivery\b'
        ]
        cleaned = text
        for f in fillers:
            cleaned = re.sub(f, '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b\d+\b', '', cleaned)
        cleaned = re.sub(self.UNIT_REGEX, '', cleaned, flags=re.IGNORECASE)
        # Strip ASCII punctuation
        cleaned = re.sub(r'[\.,!?;"\'\(\)\[\]]', '', cleaned)
        return cleaned.strip()
