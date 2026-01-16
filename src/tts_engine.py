"""
tts_engine.py - Moduł syntezy mowy z użyciem Silero TTS (Direct Load + Normalization)
"""

import os
import threading
import torch
import sounddevice as sd
import numpy as np
from typing import Optional, Callable
from pathlib import Path
import urllib.request
import re
from num2words import num2words


class SileroTTS:
    """Silnik TTS wykorzystujący model Silero (ładowany bezpośrednio z pliku .pt) z normalizacją tekstu."""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Inicjalizacja."""
        self.model = None
        self.device = torch.device('cpu')
        self.progress_callback = progress_callback or (lambda x: None)
        self.sample_rate = 48000
        # Zmiana głosu na en_117 (Męski, bardzo dobry do komunikatów)
        self.speaker = 'en_117' 
        self._playback_active = False
        
        # Konfiguracja ścieżek
        self.model_dir = Path(__file__).parent.parent / "models" / "silero"
        self.model_path = self.model_dir / "v3_en.pt"
        self.model_url = "https://models.silero.ai/models/tts/en/v3_en.pt"
        
    def _report_progress(self, message: str):
        self.progress_callback(message)
        print(f"[TTS] {message}")
    
    def download_model(self) -> bool:
        """Pobiera plik modelu .pt bezpośrednio."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        if self.model_path.exists():
            return True
            
        self._report_progress("Downloading Silero TTS v3_en.pt (~100MB)...")
        try:
            urllib.request.urlretrieve(self.model_url, self.model_path)
            self._report_progress("Model downloaded.")
            return True
        except Exception as e:
            self._report_progress(f"Download error: {e}")
            if self.model_path.exists():
                self.model_path.unlink()
            return False

    def load_model(self) -> bool:
        """Ładuje model z pliku .pt."""
        if self.model is not None:
            return True
        
        if not self.download_model():
            return False
            
        self._report_progress("Loading TTS model...")
        try:
            importer = torch.package.PackageImporter(self.model_path)
            self.model = importer.load_pickle("tts_models", "model")
            self.model.to(self.device)
            
            self._report_progress("TTS Ready!")
            return True
        except Exception as e:
            self._report_progress(f"Load error (torch.package): {e}")
            return False
    
    def _normalize_text(self, text: str) -> str:
        """
        Zamienia liczby na słowa (Text Normalization).
        Silero v3 nie radzi sobie z cyframi, więc musimy je przekonwertować.
        """
        try:
            # 1. Obsługa godzin (HH:MM -> HH MM)
            # np. 21:00 -> twenty one zero zero (lub hundred)
            def replace_time(match):
                h, m = int(match.group(1)), int(match.group(2))
                return f"{num2words(h)} {num2words(m)}"
            
            text = re.sub(r"(\d{1,2}):(\d{2})", replace_time, text)
            
            # 2. Obsługa pozostałych liczb (np. pociąg 2426)
            def replace_number(match):
                return num2words(int(match.group(0)))
            
            text = re.sub(r"\d+", replace_number, text)
            
            # Oczyszczanie ze znaków specjalnych których TTS nie lubi
            text = text.replace("-", " ")
            
            return text
        except Exception as e:
            print(f"Normalization error: {e}")
            return text

    def speak(self, text: str, blocking: bool = True):
        """Syntezuje i odtwarza."""
        if not self.model and not self.load_model():
            self._report_progress("No model.")
            return

        try:
            # NORMALIZACJA TEKSTU dla TTS
            normalized_text = self._normalize_text(text)
            self._report_progress(f"Reading: '{normalized_text[:50]}...'")
            
            audio = self.model.apply_tts(text=normalized_text,
                                       speaker=self.speaker,
                                       sample_rate=self.sample_rate)
            
            audio_np = audio.numpy()
            
            # Add 0.5s of silence at the end to prevent cutoff
            silence_samples = int(self.sample_rate * 0.5)
            silence = np.zeros(silence_samples, dtype=np.float32)
            audio_np = np.concatenate([audio_np, silence])
            
            self._playback_active = True
            sd.play(audio_np, self.sample_rate)
            
            if blocking:
                sd.wait()
                self._playback_active = False
            
        except Exception as e:
            self._report_progress(f"TTS Error: {e}")
            self._playback_active = False

    def stop(self):
        if self._playback_active:
            sd.stop()
            self._playback_active = False


# Alias
PiperTTS = SileroTTS
