import os
import io
import wave
import math
import base64
from typing import Optional, Dict, Any, Tuple
from utils.config import (
    SARVAM_API_KEY,
    SARVAM_STT_MODEL,
    SARVAM_TTS_MODEL,
    SARVAM_CHAT_MODEL,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE
)

# Try importing Sarvam SDK
try:
    from sarvamai import SarvamAI
    SARVAM_AVAILABLE = True
except ImportError:
    SARVAM_AVAILABLE = False


class SarvamService:
    """Modular Sarvam AI client supporting Speech-to-Text, Text-to-Speech, and LLM Chat."""

    def __init__(self, api_key: Optional[str] = None, force_demo: bool = False):
        if force_demo:
            self.api_key = ""
            self.is_live = False
        else:
            self.api_key = api_key if api_key is not None else SARVAM_API_KEY
            self.is_live = bool(self.api_key and SARVAM_AVAILABLE)

        self.client = None
        if self.is_live:
            try:
                self.client = SarvamAI(api_subscription_key=self.api_key)
            except Exception as e:
                print(f"[WARN] Failed to initialize SarvamAI client: {e}")
                self.is_live = False

    def get_mode_label(self) -> str:
        """Returns LIVE MODE or DEMO MODE label with status badge."""
        return "LIVE MODE (Sarvam Cloud)" if self.is_live else "DEMO MODE (Simulated AI Engine)"

    def transcribe_audio(self, audio_data: Any, language_code: str = "hi-IN") -> Dict[str, Any]:
        """
        Transcribe speech audio file using Sarvam Saaras model.
        Accepts file path (str), file-like object, or bytes.
        """
        if self.is_live and self.client:
            try:
                # Prepare file parameter
                if isinstance(audio_data, str):
                    f = open(audio_data, "rb")
                    resp = self.client.speech_to_text.transcribe(
                        file=f,
                        model=SARVAM_STT_MODEL,
                        language_code=language_code if language_code != "unknown" else "hi-IN"
                    )
                    f.close()
                elif isinstance(audio_data, bytes):
                    bio = io.BytesIO(audio_data)
                    bio.name = "recording.wav"
                    resp = self.client.speech_to_text.transcribe(
                        file=bio,
                        model=SARVAM_STT_MODEL,
                        language_code=language_code if language_code != "unknown" else "hi-IN"
                    )
                else:
                    # Streamlit UploadedFile or file-like
                    resp = self.client.speech_to_text.transcribe(
                        file=audio_data,
                        model=SARVAM_STT_MODEL,
                        language_code=language_code if language_code != "unknown" else "hi-IN"
                    )

                transcript = getattr(resp, "transcript", "")
                return {
                    "success": True,
                    "mode": "LIVE",
                    "transcript": transcript,
                    "language_code": language_code,
                    "raw_response": str(resp)
                }
            except Exception as e:
                print(f"[ERROR] Sarvam STT failed: {e}. Falling back to deterministic demo response.")
                # Graceful fallback on live error
                return self._simulate_transcription(language_code, str(e))
        else:
            return self._simulate_transcription(language_code)

    def _simulate_transcription(self, language_code: str, error_note: Optional[str] = None) -> Dict[str, Any]:
        """Deterministic simulated transcript for Demo mode."""
        simulated_transcripts = {
            "hi-IN": "Namaste bhaiya, mujhe Colgate Strong Teeth ke 10 cartons, MaxFresh ke 5 cartons aur toothbrush ke 2 dozen bhej dena.",
            "mr-IN": "Aamhi 3 peti Surf Excel aani 2 box Dettol sabun magvat aahot, lavkar pathva.",
            "en-IN": "Please deliver 5 cartons of Parle-G biscuits and 3 cartons of Maggi noodles to our store today."
        }
        transcript = simulated_transcripts.get(language_code, simulated_transcripts["hi-IN"])
        return {
            "success": True,
            "mode": "DEMO",
            "transcript": transcript,
            "language_code": language_code,
            "note": f"Simulated audio transcript. Reason: {error_note or 'Running in Demo Mode without live API call'}"
        }

    def text_to_speech(self, text: str, language_code: str = "hi-IN", speaker: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert text response to spoken audio using Sarvam Bulbul model.
        Returns bytes of WAV audio and base64 string.
        """
        target_lang = language_code if language_code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        target_speaker = speaker or SUPPORTED_LANGUAGES[target_lang]["default_speaker"]

        if self.is_live and self.client:
            try:
                resp = self.client.text_to_speech.convert(
                    text=text,
                    language_code=target_lang,
                    speaker=target_speaker,
                    model=SARVAM_TTS_MODEL
                )
                if hasattr(resp, "audios") and resp.audios:
                    audio_b64 = resp.audios[0]
                    audio_bytes = base64.b64decode(audio_b64)
                    return {
                        "success": True,
                        "mode": "LIVE",
                        "audio_bytes": audio_bytes,
                        "audio_b64": audio_b64,
                        "speaker": target_speaker,
                        "model": SARVAM_TTS_MODEL
                    }
            except Exception as e:
                print(f"[ERROR] Sarvam TTS failed: {e}. Generating synthetic demo tone.")
                return self._generate_synthetic_tone(text, str(e))
        
        return self._generate_synthetic_tone(text)

    def _generate_synthetic_tone(self, text: str, error_note: Optional[str] = None) -> Dict[str, Any]:
        """Generates a pleasant synthetic audio chime/tone for Demo mode."""
        buf = io.BytesIO()
        sample_rate = 16000
        duration = 1.2
        num_samples = int(sample_rate * duration)
        
        with wave.open(buf, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = bytearray()
            for i in range(num_samples):
                t = float(i) / sample_rate
                # Dual chord frequency (C-major chime: 523Hz + 659Hz)
                val = 0.3 * math.sin(2 * math.pi * 523.25 * t) + 0.3 * math.sin(2 * math.pi * 659.25 * t)
                # Apply envelope decay
                decay = math.exp(-3.0 * t)
                sample = int(val * decay * 32767)
                sample = max(-32768, min(32767, sample))
                frames.extend(sample.to_bytes(2, byteorder='little', signed=True))
            wav.writeframes(frames)
            
        audio_bytes = buf.getvalue()
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        return {
            "success": True,
            "mode": "DEMO",
            "audio_bytes": audio_bytes,
            "audio_b64": audio_b64,
            "note": f"Demo audio indicator chime. Reason: {error_note or 'Demo Mode Active'}"
        }

    def chat_query(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Run an LLM chat completion query through Sarvam AI."""
        if self.is_live and self.client:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                resp = self.client.chat.completions(
                    model=SARVAM_CHAT_MODEL,
                    messages=messages,
                    temperature=0.2
                )
                content = resp.choices[0].message.content
                return {
                    "success": True,
                    "mode": "LIVE",
                    "content": content.strip()
                }
            except Exception as e:
                print(f"[WARN] Sarvam chat completion error: {e}")
                return {"success": False, "mode": "DEMO", "error": str(e)}

        return {"success": False, "mode": "DEMO", "error": "Not configured for live calls"}
