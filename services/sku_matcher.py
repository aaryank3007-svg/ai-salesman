import re
from typing import List, Dict, Any, Optional, Tuple
from database.db import query_all

class SkuMatcher:
    """Intelligent SKU matching engine with FMCG alias support, variant resolution, and ambiguity detection."""

    def __init__(self):
        self._load_catalogue()

    def _load_catalogue(self):
        """Load active products and their aliases and packaging from database."""
        self.products = query_all("""
            SELECT id, name, brand, category, variant, mrp, distributor_price, stock_pieces, aliases
            FROM products
        """)
        self.catalogue = []
        for p in self.products:
            raw_aliases = p.get("aliases", "")
            alias_list = [self._normalize_text(a) for a in raw_aliases.split(",") if a.strip()]
            alias_list.append(self._normalize_text(p["name"]))
            self.catalogue.append({
                "product": p,
                "aliases": alias_list,
                "brand_clean": self._normalize_text(p["brand"])
            })

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Strip only ASCII punctuation, preserve Devanagari combining marks."""
        t = text.lower().strip()
        return re.sub(r'[\.,!?;"\'\(\)\[\]\-]', '', t).strip()

    def match_product(self, raw_mention: str, variant_hint: Optional[str] = None) -> Dict[str, Any]:
        mention = self._normalize_text(raw_mention)
        if not mention:
            return {
                "status": "NOT_FOUND",
                "matched_product": None,
                "confidence": 0.0,
                "candidate_products": [],
                "clarification_needed": True,
                "message": "Product name not detected."
            }

        # Check if mention matches brand name (e.g. "colgate")
        brand_matches = []
        for item in self.catalogue:
            prod = item["product"]
            b = item["brand_clean"]
            if mention == b or mention in b or b in mention:
                brand_matches.append(prod)

        # 1. Exact alias matches
        exact_alias_matches = []
        partial_matches = []

        for item in self.catalogue:
            prod = item["product"]
            aliases = item["aliases"]
            for alias in aliases:
                if alias == mention:
                    if prod not in exact_alias_matches:
                        exact_alias_matches.append(prod)
                    break
                elif alias in mention or mention in alias:
                    if prod not in partial_matches and prod not in exact_alias_matches:
                        partial_matches.append(prod)

        # If brand match found with multiple products (e.g. "colgate") and no variant
        if len(brand_matches) > 1 and not variant_hint and len(exact_alias_matches) <= 1:
            prod_names = [f"{p['name']} ({p['variant']})" for p in brand_matches]
            return {
                "status": "AMBIGUOUS",
                "matched_product": None,
                "confidence": 0.50,
                "candidate_products": brand_matches,
                "clarification_needed": True,
                "message": f"Multiple products match '{raw_mention}': {', '.join(prod_names)}. Please specify the exact variant."
            }

        # If variant hint provided
        if variant_hint:
            hint_clean = self._normalize_text(variant_hint)
            candidates = exact_alias_matches or partial_matches or brand_matches
            filtered = [p for p in candidates if hint_clean in self._normalize_text(p["variant"]) or hint_clean in self._normalize_text(p["name"])]
            if len(filtered) == 1:
                return {
                    "status": "EXACT",
                    "matched_product": filtered[0],
                    "confidence": 0.98,
                    "candidate_products": [filtered[0]],
                    "clarification_needed": False,
                    "message": f"Exact match found: {filtered[0]['name']}"
                }

        # Evaluate matches
        candidates = exact_alias_matches if exact_alias_matches else partial_matches

        # Deduplicate
        unique_candidates = list({c["id"]: c for c in candidates}.values())

        if len(unique_candidates) == 1:
            return {
                "status": "EXACT",
                "matched_product": unique_candidates[0],
                "confidence": 0.95 if exact_alias_matches else 0.85,
                "candidate_products": unique_candidates,
                "clarification_needed": False,
                "message": f"Matched to {unique_candidates[0]['name']}"
            }
        elif len(unique_candidates) > 1:
            prod_names = [f"{p['name']} ({p['variant']})" for p in unique_candidates]
            return {
                "status": "AMBIGUOUS",
                "matched_product": None,
                "confidence": 0.50,
                "candidate_products": unique_candidates,
                "clarification_needed": True,
                "message": f"Multiple products match '{raw_mention}': {', '.join(prod_names)}. Please specify the exact variant."
            }
        else:
            return {
                "status": "NOT_FOUND",
                "matched_product": None,
                "confidence": 0.0,
                "candidate_products": [],
                "clarification_needed": True,
                "message": f"Product '{raw_mention}' could not be found in distributor catalogue."
            }
