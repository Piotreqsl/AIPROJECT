"""
llm_generator.py - Moduł generowania komunikatów (Llama/Qwen)
"""

import os
from pathlib import Path
from typing import Dict, Optional, Callable

# Ścieżka do modelu
MODEL_DIR = Path(__file__).parent.parent / "models" / "llm"
# Qwen2.5-7B
MODEL_FILENAME = "Qwen2.5-7B-Instruct-Q4_K_M.gguf"
MODEL_URL = "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf"

# System Prompt - ENGLISH
SYSTEM_PROMPT = """You are a professional railway station announcer.
Your task is to generate CLEAR, POLITE, and SHORT announcements for passengers in ENGLISH.

Rules:
1. Speak ONLY in ENGLISH.
2. Use a formal, announcer style ("Attention please", "We inform you").
3. If a train is delayed, always apologize for the inconvenience.
4. Include key info: Train number, Destination, Departure time, Platform.
5. Keep it concise (max 2-3 sentences).
6. NO markdown, emojis, or special characters.

Examples:
- "Attention please. The Intercity train number 1234 to London will depart from platform 3. It is delayed by approximately 10 minutes. We apologize for the delay."
- "The train to Berlin is now arriving at platform 2. Please stand back from the platform edge."
"""


class AnnouncementGenerator:
    """Generator komunikatów głosowych (LLM)."""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Inicjalizacja."""
        self.llm = None
        self.progress_callback = progress_callback or (lambda x: None)
        
    def _report_progress(self, message: str):
        self.progress_callback(message)
        print(f"[LLM] {message}")
        
    def is_model_downloaded(self) -> bool:
        model_path = MODEL_DIR / MODEL_FILENAME
        return model_path.exists()
    
    def download_model(self) -> bool:
        """Pobiera model z HF."""
        import urllib.request
        
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODEL_DIR / MODEL_FILENAME
        
        # Usuń inne modele (cleanup)
        for old_model in MODEL_DIR.glob("*.gguf"):
            if old_model.name != MODEL_FILENAME:
                try:
                    self._report_progress(f"Removing old model: {old_model.name}")
                    old_model.unlink()
                except: pass
        
        if model_path.exists():
            return True
            
        self._report_progress(f"Downloading model (~4.7 GB)... Please wait.")
        try:
            def reporthook(block_num, block_size, total_size):
                if block_num % 100 == 0 and total_size > 0:
                    percent = block_num * block_size * 100 // total_size
                    mb_dl = (block_num * block_size) / (1024*1024)
                    mb_tot = total_size / (1024*1024)
                    self._report_progress(f"Downloading: {percent}% ({mb_dl:.0f}/{mb_tot:.0f} MB)")
            
            urllib.request.urlretrieve(MODEL_URL, model_path, reporthook)
            self._report_progress("Model downloaded successfully!")
            return True
        except Exception as e:
            self._report_progress(f"Download error: {e}")
            return False
            
    def load_model(self) -> bool:
        """Ładuje model."""
        if self.llm: return True
        if not self.is_model_downloaded():
             if not self.download_model(): return False
             
        self._report_progress("Loading LLM model...")
        try:
            from llama_cpp import Llama
            model_path = str(MODEL_DIR / MODEL_FILENAME)
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
            self._report_progress("LLM Loaded!")
            return True
        except Exception as e:
            self._report_progress(f"Load error: {e}")
            return False

    def generate_announcement(self, train_data: Dict, stop_check_callback: Callable[[], bool] = None) -> str:
        """
        Generuje komunikat (English).
        Obsługuje przerywanie (stop_check_callback).
        """
        if not self.llm and not self.load_model():
            return "System unavailable."
            
        # Format danych dla modelu
        info = (
            f"Train Number: {train_data['train_number']}\n"
            f"Operator: {train_data['operator']}\n"
            f"Destination: {train_data['destination']}\n"
            f"Origin: {train_data['origin']}\n"
            f"Time: {train_data['scheduled_time']}\n"
            f"Platform: {train_data['platform']}\n"
        )
        if train_data['delay_minutes'] > 0:
            info += f"STATUS: DELAYED by {train_data['delay_minutes']} minutes"
        else:
            info += "STATUS: ON TIME"
            
        user_prompt = f"Data:\n{info}\n\nGenerate station announcement in English:"
        
        try:
            self._report_progress("Thinking...")
            
            # STREAMING dla obsługi przycisku STOP
            stream = self.llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.3,
                stream=True 
            )
            
            full_text = ""
            for chunk in stream:
                # Sprawdź czy użytkownik kliknął STOP
                if stop_check_callback and stop_check_callback():
                    self._report_progress("Generation interrupted.")
                    return "[Interrupted]"
                
                if 'content' in chunk['choices'][0]['delta']:
                    content = chunk['choices'][0]['delta']['content']
                    full_text += content
                    # Opcjonalnie: raportuj postęp generowania (np. kropki)
                    # self.progress_callback(".") 
            
            return full_text.strip()
            
        except Exception as e:
            self._report_progress(f"Generation error: {e}")
            return f"Attention. Train {train_data['train_number']} to {train_data['destination']} is delayed."

if __name__ == "__main__":
    gen = AnnouncementGenerator()
    # Test
