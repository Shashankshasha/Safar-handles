from __future__ import annotations

from pathlib import Path

from gtts import gTTS


def generate_voiceover(text: str, output_path: Path, lang: str = "en") -> Path:
    """Free default TTS engine. Swap for ElevenLabs/PlayHT etc. later if you
    want a branded voice — same call signature, just a different implementation.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gTTS(text=text, lang=lang).save(str(output_path))
    return output_path
