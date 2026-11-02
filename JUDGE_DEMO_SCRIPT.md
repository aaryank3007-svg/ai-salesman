# 🏆 Judge Demo Script (3 to 5 Minutes) — AI Salesman

## Minute 0:00 - 0:45 | The Problem & Hook
- **Speaker:** "Distributors across India lose 15-20% of daily sales due to missed phone calls, language barriers, and manual order-entry mistakes. Kirana store owners speak in Hindi or Marathi using local terms like '5 peti' or '2 darjan'."
- **Action:** Open `app.py` in browser. Show the executive dashboard with real FMCG distributor metrics. Point out the **LIVE Sarvam AI** connection indicator.

## Minute 0:45 - 2:00 | The Core Demo: Voice AI Ordering Terminal
- **Speaker:** "Let's see AI Salesman in action as a Kirana retailer placing an order."
- **Action:** Navigate to **AI Voice Salesman (`pages/3_Voice_Agent.py`)**.
- **Action:** Click the sample prompt:
  *"Namaste bhaiya, mujhe Colgate Strong Teeth ke 10 cartons, MaxFresh ke 5 cartons aur toothbrush ke 2 dozen bhej dena."*
- **Click:** **Process Order Intent**.
- **Highlight to Judges:**
  1. **Multilingual Entity Extraction:** Sarvam AI accurately parses Hindi and Hinglish.
  2. **Product & Variant Resolution:** Correctly disambiguates 'Colgate Strong Teeth' vs 'MaxFresh'.
  3. **SKU-Specific Packaging Conversions:** 10 cartons of Colgate ST = 720 pcs, 5 cartons of MaxFresh = 240 pcs, 2 dozen toothbrushes = 24 pcs. Notice how every product uses its own conversion factor!
  4. **Live Warehouse Stock Check:** Real-time stock validation prevents over-committing inventory.
- **Action:** Click **🔊 Play Spoken AI Order Confirmation**. Listen to Sarvam Bulbul TTS speak back the summary in natural Hindi.
- **Action:** Click **✅ Confirm and Send Order**. Watch the balloons and instant order persistence!

## Minute 2:00 - 3:00 | Distributor Pipeline & Fulfillment
- **Speaker:** "Now let's switch hats to the distributor fulfilling this order."
- **Action:** Navigate to **Order Dispatch Pipeline (`pages/5_Orders.py`)**.
- **Highlight to Judges:**
  - Show the newly created order in `PENDING` state.
  - Advance the order: `Confirm` ➔ `Mark as Packed` ➔ `Dispatch`.
  - Point out that if an order is cancelled, inventory is automatically restored.

## Minute 3:00 - 4:15 | AI Business Assistant
- **Speaker:** "Distributors don't have time to write complex SQL or review spreadsheets. They can ask our AI Business Assistant in plain English."
- **Action:** Navigate to **AI Business Assistant (`pages/8_Business_Insights.py`)**.
- **Click:**
  - *"How many orders came today?"* (Instant breakdown)
  - *"Which products are selling the most?"* (Interactive Plotly revenue chart)
  - *"Which retailers haven't ordered in 30 days?"* (Automated sales outreach list)

## Minute 4:15 - 5:00 | Closing & Impact
- **Speaker:** "AI Salesman turns every Indian Kirana shopkeeper's voice into an instant enterprise order. It eliminates friction, saves hours for salespeople, and operates 24/7 in native Indian languages using Sarvam AI."

