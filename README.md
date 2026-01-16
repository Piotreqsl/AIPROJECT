# Railway Station Announcer

Aplikacja symulująca lektora stacji kolejowej z wykorzystaniem AI.

## Technologie
- **TTS**: Piper TTS (głos: gosia-medium, polski żeński)
- **LLM**: Qwen3-8B GGUF (generowanie komunikatów)
- **GUI**: tkinter

## Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Pobierz modele (automatycznie przy pierwszym uruchomieniu)
python -m src.main
```

## Użycie

1. Uruchom aplikację: `python -m src.main`
2. Kliknij "Pobierz odjazdy" aby wygenerować dane pociągów
3. Kliknij "Odczytaj komunikaty" aby usłyszeć ogłoszenia

## Wymagania
- Python 3.10+
- 8 GB RAM (minimum)
- ~6 GB miejsca na dysku (modele AI)
