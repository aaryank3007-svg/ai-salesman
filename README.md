# 🛒 AI SALESMAN
> **Your Voice-First Sales Assistant for Indian Distribution**
> Powered by **Sarvam AI** (Saaras v3 Speech-to-Text, Bulbul v3 Text-to-Speech, Sarvam 105B LLM) & Streamlit.

---

## 🌟 Overview
**AI Salesman** is an AI-powered voice ordering and distributor management platform tailored for Indian FMCG distributors, wholesalers, and Kirana store owners. 

Retailers speak naturally in **Hindi**, **Marathi**, or **Indian English** (e.g., *"Namaste bhaiya, mujhe Colgate Strong Teeth ke 10 cartons, MaxFresh ke 5 cartons aur toothbrush ke 2 dozen bhej dena"*). The AI extracts products, handles SKU-specific packaging conversions (Carton, Box, Dozen, Piece), verifies warehouse stock, calculates distributor pricing, and drafts orders for explicit confirmation.

---

## 🚀 Quick Start (Windows / Mac / Linux)

### 1. Clone & Enter Project Directory
```powershell
cd "C:\Users\Aaryank\Desktop\sarvam ai"
```

### 2. Configure Environment Secrets
Create a `.env` file in the root directory:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
APP_MODE=LIVE
DEFAULT_LANGUAGE=hi-IN
```
*(If no API key is provided, the platform automatically runs in deterministic **DEMO MODE** with full simulated voice ordering)*.

### 3. Run the Application
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Run Automated Verification Tests
```powershell
python tests/test_ai_salesman.py
```

---

## 🏗️ Core Platform Modules
1. **🏠 Launchpad (`app.py`)**: Executive overview, KPI metric cards, and live system status.
2. **📊 Distributor Dashboard (`pages/1_Overview.py`)**: Real-time sales, order status breakdown, and low stock warnings.
3. **🏪 Retailer Web Portal (`pages/2_Retailer_Portal.py`)**: Self-service FMCG catalogue, packaging selectors, and 1-click repeat orders.
4. **🎙️ AI Voice Terminal (`pages/3_Voice_Agent.py`)**: Voice recording/upload, Sarvam transcription, SKU matching, packaging conversion validation, and spoken TTS confirmations.
5. **📦 Product Catalogue (`pages/4_Catalogue.py`)**: 10 FMCG products with custom packaging rules per SKU.
6. **🚚 Order Pipeline (`pages/5_Orders.py`)**: Full state-machine order progression (`PENDING -> CONFIRMED -> PACKED -> DISPATCHED -> DELIVERED`).
7. **🏷️ Inventory Management (`pages/6_Inventory.py`)**: Warehouse stock control, threshold alarms, and 1-click restocking.
8. **👥 Retailer Accounts (`pages/7_Retailers.py`)**: 6 Kirana profiles with credit limit and balance tracking.
9. **💡 AI Business Assistant (`pages/8_Business_Insights.py`)**: Natural language analytics answering daily sales, best-selling SKUs, and dormant accounts.
10. **⚙️ Settings (`pages/9_Settings.py`)**: Live vs Demo toggle, audio synthesis test, and database reset.

