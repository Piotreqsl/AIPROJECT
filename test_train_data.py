"""Test modułu train_data"""
from src.train_data import generate_train_departures, format_delay_text

print("Test generowania danych pociągów:")
print("-" * 50)

trains = generate_train_departures(5)
for t in trains:
    delay = format_delay_text(t["delay_minutes"])
    print(f"{t['train_number']}: {t['origin']} -> {t['destination']}")
    print(f"   Godz: {t['scheduled_time']}, Peron: {t['platform']}, {delay}")
    print()

print("Test zakończony pomyślnie!")
