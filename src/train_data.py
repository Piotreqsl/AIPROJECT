"""
train_data.py - Module for generating random train data (US Localized)
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict


# US Train Stations
STATIONS = [
    "New York Penn Station", "Boston South Station", "Chicago Union Station", "Washington Union Station",
    "Philadelphia 30th Street", "Los Angeles Union Station", "San Francisco",
    "Seattle King Street", "Miami Central", "Dallas Union Station", "Atlanta Peachtree",
    "Denver Union Station", "New Orleans Union Passenger Terminal", "San Diego Santa Fe Depot",
    "Portland Union Station", "Houston", "Salt Lake City", "Las Vegas"
]

# US Rail Operators
OPERATORS = [
    "Amtrak", "Metrolink", "Caltrain", "MARC", "SEPTA", "NJ Transit", "Metro-North", "LIRR"
]

# Train Types
TRAIN_TYPES = [
    ("Acela", "Amtrak"),
    ("Regional", "Amtrak"),
    ("Silver Star", "Amtrak"),
    ("Sunset Ltd", "Amtrak"),
    ("Commuter", "Metrolink"),
    ("Express", "Caltrain"),
    ("Local", "NJ Transit"),
    ("LIRR", "LIRR"),
]


def generate_train_number(train_type: str) -> str:
    """Generates train number."""
    number = random.randint(10, 9999)
    if len(train_type) > 4:
         # For long names like "Regional", just use a prefix or simply the number
         return f"#{number}"
    return f"{train_type} {number}"


def generate_route() -> tuple:
    """Generates random route."""
    start, end = random.sample(STATIONS, 2)
    return start, end


def generate_delay() -> int:
    """Generates random delay."""
    # 60% on time
    if random.random() < 0.6:
        return 0
    # 25% small delay
    elif random.random() < 0.85:
        return random.randint(1, 15)
    # 15% large delay
    else:
        return random.randint(16, 60)


def generate_departure_time(base_time: datetime = None) -> datetime:
    if base_time is None:
        base_time = datetime.now()
    
    minutes_ahead = random.randint(5, 120)
    departure = base_time + timedelta(minutes=minutes_ahead)
    # Round to 5 mins
    departure = departure.replace(minute=(departure.minute // 5) * 5, second=0, microsecond=0)
    return departure


def generate_train_departures(count: int = 8) -> List[Dict]:
    departures = []
    base_time = datetime.now()
    
    for _ in range(count):
        train_type, operator = random.choice(TRAIN_TYPES)
        start, end = generate_route()
        departure_time = generate_departure_time(base_time)
        delay = generate_delay()
        platform = random.randint(1, 20)
        track = random.choice([None, random.randint(1, 4)])
        
        train_data = {
            "train_number": generate_train_number(train_type),
            "train_type": train_type,
            "operator": operator,
            "origin": start,
            "destination": end,
            "scheduled_time": departure_time.strftime("%H:%M"),
            "delay_minutes": delay,
            "platform": platform,
            "track": track,
            "is_delayed": delay > 0
        }
        departures.append(train_data)
    
    departures.sort(key=lambda x: x["scheduled_time"])
    
    return departures


def format_delay_text(delay_minutes: int) -> str:
    """Formats delay text in English."""
    if delay_minutes == 0:
        return "On Time"
    elif delay_minutes == 1:
        return "+1 min"
    else:
        return f"+{delay_minutes} mins"


if __name__ == "__main__":
    print("🚂 Generating US train data...\n")
    departures = generate_train_departures(5)
    
    for train in departures:
        delay_text = format_delay_text(train["delay_minutes"])
        platform_text = f"Track {train['platform']}" # In US usually Track is used for boarding
            
        print(f"{train['train_number']} | {train['origin']} → {train['destination']}")
        print(f"   Time: {train['scheduled_time']} | {delay_text} | {platform_text}")
        print()
