import os
import sys
import json
import shutil
import hashlib
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()
MGIT_DIR = ".mgit"
SNAPSHOTS_DIR = os.path.join(MGIT_DIR, "snapshots")
INDEX_FILE = os.path.join(MGIT_DIR, "index.json")

def init():
    if os.path.exists(MGIT_DIR):
        console.print("[yellow]Репозиторій mGit вже ініціалізовано![/yellow]")
        return
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump({"snapshots": [], "latest_id": 0}, f, ensure_ascii=False, indent=4)
    console.print("[green]Успішно ініціалізовано порожній репозиторій mGit[/green]")

def load_index():
    if not os.path.exists(INDEX_FILE):
        return None
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_index(index_data):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=4)