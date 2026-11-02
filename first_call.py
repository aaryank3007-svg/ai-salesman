import os
import base64
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY not found in environment!")

client = SarvamAI(api_subscription_key=api_key)

print("[INFO] Testing Sarvam AI Text-to-Speech API (bulbul:v3 with speaker 'ritu')...")
try:
    response = client.text_to_speech.convert(
        text="नमस्ते, AI सेल्समैन में आपका स्वागत है। आपका ऑर्डर क्या है?",
        language_code="hi-IN",
        speaker="ritu",
        model="bulbul:v3"
    )
    print("[SUCCESS] Sarvam TTS Call Succeeded!")
    if hasattr(response, 'audios') and response.audios:
        audio_b64 = response.audios[0]
        audio_bytes = base64.b64decode(audio_b64)
        output_filename = "first_call_output.wav"
        with open(output_filename, "wb") as f:
            f.write(audio_bytes)
        print(f"[SUCCESS] Audio saved successfully to '{output_filename}' ({len(audio_bytes)} bytes)")
except Exception as e:
    print(f"[ERROR] Sarvam TTS Call failed: {e}")

print("\n[INFO] Testing Sarvam Chat / Text API (model: sarvam-105b)...")
try:
    chat_resp = client.chat.completions(
        model="sarvam-105b",
        messages=[
            {"role": "user", "content": "Reply with a one-sentence greeting for an Indian FMCG distributor."}
        ]
    )
    content = chat_resp.choices[0].message.content
    print(f"[SUCCESS] Sarvam Chat Call Succeeded: {content.strip()}")
except Exception as e:
    print(f"[NOTICE] Sarvam Chat call note: {e}")
