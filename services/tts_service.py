import os
import urllib.request
from rich.console import Console
import pyaudio

console = Console()

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx.json"

MODEL_PATH = "en_GB-alba-medium.onnx"
CONFIG_PATH = "en_GB-alba-medium.onnx.json"

_voice = None
_pyaudio = None

def download_model_if_needed():
    if not os.path.exists(MODEL_PATH):
        console.print("[dim]Downloading Alba (British English) voice model (~50MB)...[/dim]")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    if not os.path.exists(CONFIG_PATH):
        urllib.request.urlretrieve(CONFIG_URL, CONFIG_PATH)

def get_voice():
    global _voice
    if _voice is None:
        download_model_if_needed()
        from piper import PiperVoice
        _voice = PiperVoice.load(MODEL_PATH, config_path=CONFIG_PATH)
    return _voice

def get_pyaudio():
    global _pyaudio
    if _pyaudio is None:
        _pyaudio = pyaudio.PyAudio()
    return _pyaudio

def speak(text: str) -> None:
    """
    Converts text to speech using Piper TTS and streams it to the speakers.
    """
    if not text.strip():
        return
        
    voice = get_voice()
    p = get_pyaudio()
    
    # PiperConfig is a dataclass, so we access the attribute directly
    sample_rate = voice.config.sample_rate
    
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True)
                    
    try:
        # Piper synthesize yields AudioChunk objects. We need audio_int16_bytes.
        for chunk in voice.synthesize(text):
            stream.write(chunk.audio_int16_bytes)
    except Exception as e:
        console.print(f"[red]Error playing audio: {e}[/red]")
    finally:
        stream.stop_stream()
        stream.close()
