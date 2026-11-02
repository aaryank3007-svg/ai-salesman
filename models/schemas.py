from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PackagingUnitModel(BaseModel):
    unit_name: str
    pieces_per_unit: int
    unit_price: float
    is_allowed: bool = True

class ProductModel(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    variant: str
    base_unit: str = "piece"
    mrp: float
    distributor_price: float
    stock_pieces: int
    min_stock_threshold: int = 50
    aliases: str = ""
    packaging_units: List[PackagingUnitModel] = []

class RetailerModel(BaseModel):
    id: str
    shop_name: str
    owner_name: str
    phone: str
    address: str
    price_group: str = "Standard"
    credit_limit: float = 50000.0
    current_balance: float = 0.0

class RawExtractedItem(BaseModel):
    product_mention: str
    raw_quantity: float = 1.0
    raw_unit: str = "carton"
    variant_mention: Optional[str] = None

class ParsedOrderItem(BaseModel):
    product_id: str
    product_name: str
    brand: str
    variant: str
    ordered_quantity: float
    ordered_unit: str
    pieces_per_unit: int
    total_pieces: int
    unit_price: float
    item_total: float
    stock_available_pieces: int
    is_in_stock: bool
    is_ambiguous: bool = False
    ambiguous_options: List[Dict[str, Any]] = []
    needs_packaging_clarification: bool = False
    clarification_message: Optional[str] = None

class OrderParseResult(BaseModel):
    transcript: str
    detected_language: str = "hi-IN"
    mode: str = "LIVE"
    items: List[ParsedOrderItem] = []
    unmatched_queries: List[str] = []
    clarification_questions: List[str] = []
    subtotal: float = 0.0
    discount: float = 0.0
    total_amount: float = 0.0
    is_ready_for_confirmation: bool = False

class OrderCreateRequest(BaseModel):
    retailer_id: str
    items: List[ParsedOrderItem]
    order_source: str = "VOICE_AI"
    original_transcript: Optional[str] = None
    raw_language: Optional[str] = "hi-IN"

class AnalyticsResponse(BaseModel):
    question: str
    answer: str
    metric_type: str
    data_summary: Dict[str, Any] = {}
