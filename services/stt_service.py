import os
import sys
import time
import queue
import msvcrt
import speech_recognition as sr
from faster_whisper import WhisperModel
from rich.console import Console

console = Console()

# We load the model lazily to avoid delay on startup
_model = None

def get_whisper_model() -> WhisperModel:
    global _model
    if _model is None:
        console.print("[dim]Loading Whisper base model (this might take a second)...[/dim]")
        # Using "base.en" for maximum speed and good accuracy in English C1
        _model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _model

def get_hybrid_input(prompt_text: str = "You (Speak or type): ") -> str:
    """
    Listens to the microphone while simultaneously allowing the user to type.
    Returns the spoken text if speech is detected, or the typed text if they press Enter.
    """
    r = sr.Recognizer()
    # Tweaks to prevent cutting off too early and ignoring static
    r.pause_threshold = 1.5  # Wait 1.5s of silence before considering a phrase finished
    r.non_speaking_duration = 0.5
    
    m = sr.Microphone()
    
    # Adjust for ambient noise briefly
    with m as source:
        r.adjust_for_ambient_noise(source, duration=1.5)
        
    q = queue.Queue()
    
    def callback(recognizer, audio):
        """Called by the background thread when speech finishes."""
        q.put(("audio", audio))
        
    # Start listening in a background thread
    stop_listening = r.listen_in_background(m, callback, phrase_time_limit=30)
    
    # Render the prompt
    sys.stdout.write(prompt_text)
    sys.stdout.flush()
    
    typed_text = ""
    
    try:
        while True:
            # Check if background thread captured speech
            try:
                audio_type, audio_data = q.get_nowait()
                if audio_type == "audio":
                    # If user started typing, clear the line for the transcribe message
                    if typed_text:
                        sys.stdout.write('\r' + ' ' * (len(prompt_text) + len(typed_text) + 20) + '\r')
                        sys.stdout.flush()
                        
                    console.print("\n[dim]🎤 Processing speech...[/dim]", end="")
                    # wait_for_stop=True is critical to prevent "already inside context manager" error
                    stop_listening(wait_for_stop=True)
                    
                    # Save to temp file for Whisper
                    temp_wav = "temp_speech.wav"
                    with open(temp_wav, "wb") as f:
                        f.write(audio_data.get_wav_data())
                        
                    model = get_whisper_model()
                    # Using condition_on_previous_text=False prevents hallucinations looping
                    # vad_filter=True completely blocks audio that doesn't contain human voice
                    segments, _ = model.transcribe(
                        temp_wav, 
                        beam_size=5, 
                        condition_on_previous_text=False,
                        vad_filter=True,
                        vad_parameters=dict(min_silence_duration_ms=500)
                    )
                    
                    # Filter out hallucinations and silence
                    valid_text = []
                    for s in segments:
                        if s.no_speech_prob < 0.6:
                            valid_text.append(s.text)
                            
                    text = "".join(valid_text).strip()
                    
                    # Common whisper hallucinations on absolute silence
                    hallucinations = ["Thank you.", "Thank you", "Subscribe.", "Subscribe", "Obrigado.", "Bye."]
                    if text in hallucinations or not text:
                        # It was just silence or noise, go back to listening
                        console.print("\r" + " " * 30 + "\r", end="") # Clear processing message
                        
                        # We must restart the listener because we stopped it above
                        if os.path.exists(temp_wav):
                            os.remove(temp_wav)
                            
                        # If user typed something in the meantime, reprint it
                        if typed_text:
                            sys.stdout.write('\r' + prompt_text + typed_text)
                            sys.stdout.flush()
                            
                        stop_listening = r.listen_in_background(m, callback, phrase_time_limit=30)
                        continue
                        
                    if not prompt_text:
                        # If prompt_text is empty, we likely printed the prompt outside this function.
                        # We just print the spoken text here.
                        console.print(f"[dim](Spoken)[/dim] {text}")
                    else:
                        console.print(f"[bold green]You (Spoken)[/bold green]: {text}")
                    
                    # Cleanup
                    if os.path.exists(temp_wav):
                        os.remove(temp_wav)
                        
                    return text
            except queue.Empty:
                pass
                
            # Check if user typed anything on the keyboard (Windows only)
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char in ('\r', '\n'):
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    stop_listening(wait_for_stop=True)
                    return typed_text.strip()
                elif char == '\x08': # Backspace
                    if len(typed_text) > 0:
                        typed_text = typed_text[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                else:
                    typed_text += char
                    sys.stdout.write(char)
                    sys.stdout.flush()
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        stop_listening(wait_for_stop=True)
        return "exit"
