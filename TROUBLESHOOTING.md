# 🛠️ Troubleshooting Guide — AI Salesman

## 1. Sarvam API Key Configuration
- **Symptom:** App indicates `🟡 DEMO MODE Active`.
- **Solution:** 
  1. Open `.env` file in the root directory.
  2. Ensure `SARVAM_API_KEY=sk_...` is set without quotation marks.
  3. Restart the Streamlit server (`streamlit run app.py`).

## 2. Audio Transcription / Codec Warnings
- **Symptom:** Audio file fails to transcribe.
- **Solution:** 
  - Ensure the audio file is in standard `.wav`, `.mp3`, or `.m4a` format.
  - The built-in audio handler automatically formats stream bytes into PCM 16-bit WAV for Sarvam Saaras.
  - If microphone recording is blocked by browser permissions, use the file upload fallback on the Voice Agent page.

## 3. Database Re-seeding
- **Symptom:** Want to restore the original 10 products and 8 sample orders.
- **Solution:**
  - Navigate to **Settings (`pages/9_Settings.py`)** and click **Re-seed Database**.
  - Or run:
    ```powershell
    python database/seed.py
    ```

## 4. Port 8501 Already in Use
- **Symptom:** Streamlit says port 8501 is occupied.
- **Solution:**
  ```powershell
  streamlit run app.py --server.port 8502
  ```
