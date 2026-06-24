import os
import sys
import json
import shutil
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()
MGIT_DIR = ".mgit"
SNAPSHOTS_DIR = os.path.join(MGIT_DIR, "snapshots")
INDEX_FILE = os.path.join(MGIT_DIR, "index.json")

def init():
    if os.path.exists(MGIT_DIR):
        console.print("[bold yellow]Попередження:[/bold yellow] mGit репозиторій вже існує.")
        return
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump({"snapshots": [], "latest_id": 0}, f, ensure_ascii=False, indent=4)
    console.print("[bold green]Успіх:[/bold green] Створено порожній репозиторій mGit.")

def get_index():
    if not os.path.exists(INDEX_FILE):
        console.print("[bold red]Помилка:[/bold red] Репозиторій не ініціалізовано. Запустіть 'python mgit.py init'")
        return None
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_index(index):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=4)

def snapshot(file_path, comment):
    if not os.path.exists(file_path):
        console.print(f"[bold red]Помилка:[/bold red] Файл '{file_path}' не знайдено.")
        return
    index = get_index()
    if not index: return

    index["latest_id"] += 1
    snap_id = index["latest_id"]
    
    snap_filename = f"snap_{snap_id}_{os.path.basename(file_path)}"
    dest_path = os.path.join(SNAPSHOTS_DIR, snap_filename)
    shutil.copy2(file_path, dest_path)
    
    new_snapshot = {
        "id": snap_id,
        "filename": snap_filename,
        "original_path": os.path.abspath(file_path),
        "comment": comment,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    index["snapshots"].append(new_snapshot)
    save_index(index)
    console.print(f"[bold green]Знімок #{snap_id} успішно створено![/bold green] ({comment})")

def log():
    index = get_index()
    if not index or not index["snapshots"]:
        console.print("[yellow]Історія знімків порожня або репозиторій не знайдено.[/yellow]")
        return
    
    table = Table(title="📜 Історія знімків mGit")
    table.add_column("ID", justify="center", style="cyan")
    table.add_column("Дата/Час", style="green")
    table.add_column("Файл", style="magenta")
    table.add_column("Коментар", style="white")
    
    for s in index["snapshots"]:
        table.add_row(str(s["id"]), s["timestamp"], os.path.basename(s["original_path"]), s["comment"])
    console.print(table)

def diff(id1, id2):
    index = get_index()
    if not index: return
    
    snap1 = next((s for s in index["snapshots"] if s["id"] == id1), None)
    snap2 = next((s for s in index["snapshots"] if s["id"] == id2), None)
    
    if not snap1 or not snap2:
        console.print("[bold red]Помилка:[/bold red] Один або обидва ID знімків не знайдено в базі.")
        return
        
    path1 = os.path.join(SNAPSHOTS_DIR, snap1["filename"])
    path2 = os.path.join(SNAPSHOTS_DIR, snap2["filename"])
    
    with open(path1, "r", encoding="utf-8", errors="ignore") as f: lines1 = f.readlines()
    with open(path2, "r", encoding="utf-8", errors="ignore") as f: lines2 = f.readlines()
    
    console.print(f"[bold cyan]Порівняння знімка #{id1} та знімка #{id2}:[/bold cyan]\n")
    
    # Спрощений та наочний алгоритм порівняння рядків для CLI
    import difflib
    d = difflib.Differ()
    diff_result = list(d.compare(lines1, lines2))
    
    for line in diff_result:
        if line.startswith("+ "):
            console.print(f"[green]{line.strip()}[/green]")
        elif line.startswith("- "):
            console.print(f"[red]{line.strip()}[/red]")
        elif line.startswith("  "):
            console.print(f"[grey50]{line.strip()}[/grey50]")

def rollback(snap_id):
    index = get_index()
    if not index: return
    snap = next((s for s in index["snapshots"] if s["id"] == snap_id), None)
    if not snap:
        console.print(f"[bold red]Помилка:[/bold red] Знімок з ID {snap_id} не знайдено.")
        return
    src = os.path.join(SNAPSHOTS_DIR, snap["filename"])
    dest = snap["original_path"]
    shutil.copy2(src, dest)
    console.print(f"[bold green]Успіх:[/bold green] Файл відновлено до стану знімка #{snap_id}!")

def main():
    if len(sys.argv) < 2:
        console.print("[bold yellow]Використання mGit:[/bold yellow]")
        console.print("  python mgit.py init")
        console.print("  python mgit.py snapshot <file_path> '<коментар>'")
        console.print("  python mgit.py log")
        console.print("  python mgit.py diff <id1> <id2>")
        console.print("  python mgit.py rollback <id>")
        return

    cmd = sys.argv[1].lower()
    try:
        if cmd == "init": init()
        elif cmd == "snapshot": snapshot(sys.argv[2], sys.argv[3])
        elif cmd == "log": log()
        elif cmd == "diff": diff(int(sys.argv[2]), int(sys.argv[3]))
        elif cmd == "rollback": rollback(int(sys.argv[2]))
        else: console.print("[bold red]Невідома команда![/bold red]")
    except IndexError:
        console.print("[bold red]Помилка вводу:[/bold red] Перевірте правильність та кількість аргументів команди.")
    except ValueError:
        console.print("[bold red]Помилка типу даних:[/bold red] ID знімків мають бути цілими числами.")

if __name__ == "__main__":
    main()