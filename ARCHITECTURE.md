# 🏛️ Architecture & System Design — AI Salesman

## 1. High-Level Architecture Flow
```
[ Kirana Retailer Voice Input (Hindi / Marathi / English) ]
                           │
                           ▼
          [ Sarvam AI Speech-to-Text (Saaras v3) ]
                           │
                           ▼
             [ Retailer Raw Transcript ]
                           │
                           ▼
         [ AI Order Processing Engine & NLP ]
         ├── Sarvam 105B LLM Intent Parser
         └── Deterministic FMCG Tokenizer Fallback
                           │
                           ▼
              [ SKU & Variant Matcher ]
         ├── Multi-lingual Aliases (Devanagari + Hinglish)
         └── Ambiguity Resolver (Brand vs Variant)
                           │
                           ▼
            [ Packaging Conversion Engine ]
         ├── SKU-specific units (Carton, Box, Dozen, Piece)
         └── Incompatible unit clarification generator
                           │
                           ▼
           [ Stock & Pricing Validation Engine ]
         ├── Real-time warehouse availability check
         └── Trade scheme discounts calculation
                           │
                           ▼
                [ Draft Order Review ]
              (Requires explicit confirmation)
                           │
                           ▼
      [ Sarvam AI Text-to-Speech (Bulbul v3) ]
                           │
                           ▼
      [ Persistent SQLite Distributor Database ]
```

## 2. Packaging Conversion Rule Matrix
In Indian distribution, packaging units are strictly SKU-dependent:
- **Colgate Strong Teeth 100g**: 1 Carton = 72 pcs | 1 Box = 24 pcs | 1 Dozen = 12 pcs | 1 Piece = 1 pc
- **Colgate MaxFresh 150g**: 1 Carton = 48 pcs | 1 Dozen = 12 pcs | 1 Piece = 1 pc *(No boxes supported)*
- **Oral-B Toothbrush**: 1 Carton = 144 pcs | 1 Dozen = 12 pcs | 1 Piece = 1 pc
- **Parle-G 1kg**: 1 Carton = 20 pcs | 1 Piece = 1 pc
- **Maggi 70g**: 1 Carton = 96 pcs | 1 Box = 24 pcs | 1 Piece = 1 pc
- **Tata Tea Gold 500g**: 1 Carton = 24 pcs | 1 Piece = 1 pc
- **Dettol Soap 125g**: 1 Carton = 54 pcs | 1 Box = 18 pcs | 1 Piece = 1 pc
- **Surf Excel 1kg**: 1 Carton = 16 pcs | 1 Piece = 1 pc
- **Fortune Oil 1L**: 1 Carton = 15 pcs | 1 Piece = 1 pc

## 3. Order Lifecycle State Machine
```
[ DRAFT ] ──(Retailer Confirms)──> [ PENDING ]
                                      │
           ┌──────────────────────────┴──────────────────────────┐
           ▼                                                     ▼
     [ REJECTED ]                                          [ CONFIRMED ]
  (Inventory restored)                                           │
                                                                 ▼
                                                             [ PACKED ]
                                                                 │
                                                                 ▼
                                                           [ DISPATCHED ]
                                                                 │
                                                                 ▼
                                                           [ DELIVERED ]
```
