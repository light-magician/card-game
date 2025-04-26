import os
import sqlite3

from PIL import Image as PILImage
from PIL import ImageFilter
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich_pixels import Pixels

# Paths
DB_PATH = "cards.db"
IMAGE_FOLDER = "data"

console = Console()


def find_card(name_query: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT id, name, description, image_path
    FROM cards
    WHERE name LIKE ?
    """,
        (f"%{name_query}%",),
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        card_id, name, description, image_path = result
        return {
            "id": card_id,
            "name": name,
            "description": description,
            "image_path": image_path,
        }
    else:
        return None


def preprocess_image(image_path, target_width=80):
    """Resize and optionally sharpen image for terminal clarity."""
    try:
        image = PILImage.open(image_path)

        # Calculate adjusted height keeping Yu-Gi-Oh card aspect ratio (400x580) and terminal cell squish (~0.5)
        card_aspect_ratio = 400 / 580  # width / height of Yugioh card
        terminal_squish_factor = 0.5  # terminals have tall cells
        adjusted_height = int(
            (target_width / card_aspect_ratio) * terminal_squish_factor
        )

        # Resize with high-quality filter
        image = image.resize((target_width, adjusted_height), PILImage.LANCZOS)

        # Sharpen slightly to counteract blur
        image = image.filter(ImageFilter.SHARPEN)

        return image
    except Exception as e:
        print(f"[red]Failed to preprocess image: {e}[/red]")
        return None


def display_card(card):
    name = card["name"]
    description = card["description"]
    image_path = card["image_path"]

    console.rule(f"[bold blue]{name}[/bold blue]")
    console.print(Panel(description, title="Description", border_style="purple"))

    if image_path and os.path.exists(image_path):
        try:
            image = preprocess_image(
                image_path, target_width=80
            )  # You can tweak width easily here
            if image:
                pixels = Pixels.from_image(image)
                console.print(pixels)
            else:
                console.print("[red]Could not process image.[/red]")
        except Exception as e:
            console.print(f"[red]Failed to render image: {e}[/red]")
    else:
        console.print("[red]No image available.[/red]")


def main():
    while True:
        name_query = console.input(
            "\n[bold green]Enter card name to search (or 'quit'):[/bold green]\n> "
        ).strip()
        if name_query.lower() == "quit":
            break

        card = find_card(name_query)
        if card:
            display_card(card)
        else:
            console.print("[red]Card not found.[/red]")


if __name__ == "__main__":
    main()
