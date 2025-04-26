import json
import os
import sqlite3

# Paths
DB_PATH = "cards.db"
METADATA_PATH = "card_metadata.json"  # assuming your file is named exactly this
IMAGE_DIR = "data"  # all images are here, named {id}.jpg

# Setup SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    description TEXT,
    attack INTEGER,
    defense INTEGER,
    level INTEGER,
    race TEXT,
    attribute TEXT,
    image_path TEXT
)
"""
)

conn.commit()

# Load Metadata
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

cards = data

# Insert cards
for card in cards:
    card_id = card["id"]
    name = card["name"]
    card_type = card.get("type")
    desc = card.get("desc")
    atk = card.get("atk")
    defe = card.get("def")
    level = card.get("level")
    race = card.get("race")
    attribute = card.get("attribute")

    # Assume image exists locally
    image_filename = f"{card_id}.jpg"
    image_path = os.path.join(IMAGE_DIR, image_filename)

    if not os.path.exists(image_path):
        print(f"Warning: Image file missing for card {name} ({card_id})")
        image_path = None  # Optional: store NULL if missing

    # Insert into DB
    cursor.execute(
        """
    INSERT OR REPLACE INTO cards (id, name, type, description, attack, defense, level, race, attribute, image_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (card_id, name, card_type, desc, atk, defe, level, race, attribute, image_path),
    )

conn.commit()
conn.close()

print("Card database successfully built.")
