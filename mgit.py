import os
import sys
import json
import shutil
import hashlib
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

console = Console()
MGIT_DIR = ".mgit"
SNAPSHOTS_DIR = os.path.join(MGIT_DIR, "snapshots")
INDEX_FILE = os.path.join(MGIT_DIR, "index.json")

def init():
    if os.path.exists(MGIT_DIR):
        console.print("[bold yellow]⚠ Попередження:[/bold yellow] mGit репозиторій вже існує.")
        return
    
    with console.status("[bold cyan]Ініціалізація репозиторію...[/bold cyan]", spinner="dots"):
        os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
        
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({"snapshots": [], "latest_id": 0}, f, ensure_ascii=False, indent=4)
            
        with open(os.path.join(MGIT_DIR, ".gitignore"), "w", encoding="utf-8") as f:
            f.write("*\n")
            
    console.print("[bold green]✔ Успіх:[/bold green] Створено порожній ізольований репозиторій mGit.")

def get_index():
    if not os.path.exists(INDEX_FILE):
        console.print("[bold red]✖ Помилка:[/bold red] Репозиторій не ініціалізовано. Запустіть 'python mgit.py init'")
        return None
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        console.print("[bold red]✖ Критична помилка:[/bold red] Файл індексу (index.json) пошкоджено. Неможливо прочитати дані.")
        return None

def save_index(index):
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=4)
    except IOError as e:
        console.print(f"[bold red]✖ Помилка запису:[/bold red] Не вдалося зберегти індекс. Деталі: {e}")

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def snapshot(file_path, comment):
    if not os.path.exists(file_path):
        console.print(f"[bold red]✖ Помилка:[/bold red] Файл '{file_path}' не знайдено.")
        return
        
    index = get_index()
    if index is None: return

    current_hash = get_file_hash(file_path)
    abs_path = os.path.abspath(file_path)
    
    file_snapshots = [s for s in index["snapshots"] if s["original_path"] == abs_path]
    if file_snapshots:
        if file_snapshots[-1].get("file_hash") == current_hash:
            console.print("[bold yellow]⚠ Зміни відсутні:[/bold yellow] Файл ідентичний до останнього знімка.")
            return

    with console.status("[bold cyan]Створення знімка...[/bold cyan]", spinner="bouncingBar"):
        index["latest_id"] += 1
        snap_id = index["latest_id"]
        
        snap_filename = f"snap_{snap_id}_{os.path.basename(file_path)}"
        dest_path = os.path.join(SNAPSHOTS_DIR, snap_filename)
        
        try:
            shutil.copy2(file_path, dest_path)
        except IOError as e:
            console.print(f"[bold red]✖ Помилка копіювання:[/bold red] {e}")
            return
        
        new_snapshot = {
            "id": snap_id,
            "filename": snap_filename,
            "original_path": abs_path,
            "file_hash": current_hash,
            "comment": comment,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        index["snapshots"].append(new_snapshot)
        save_index(index)
        
    console.print(f"[bold green]✔ Знімок #{snap_id} успішно створено![/bold green] ({comment})")


def status(file_path):
    if not os.path.exists(file_path):
        console.print(f"[bold red]✖ Помилка:[/bold red] Файл '{file_path}' не знайдено на диску.")
        return
        
    index = get_index()
    if not index: return

    abs_path = os.path.abspath(file_path)
    file_snapshots = [s for s in index["snapshots"] if s["original_path"] == abs_path]
    
    if not file_snapshots:
        panel = Panel(f"Файл [bold cyan]{file_path}[/bold cyan] ще не відстежується.", title="[bold cyan]ℹ Статус[/bold cyan]", border_style="cyan", expand=False)
        console.print(panel)
        return

    last_snap = file_snapshots[-1]
    current_hash = get_file_hash(file_path)

    if last_snap.get("file_hash") == current_hash:
        panel = Panel(f"Файл [bold green]{file_path}[/bold green] не має незбережених змін.", title="[bold green]✔ Чисто[/bold green]", border_style="green", expand=False)
        console.print(panel)
    else:
        panel = Panel(f"Файл [bold yellow]{file_path}[/bold yellow] було змінено!\nРекомендується зробити новий snapshot.", title="[bold yellow]⚠ Є зміни[/bold yellow]", border_style="yellow", expand=False)
        console.print(panel)

def log():
    index = get_index()
    if not index: return
    if not index.get("snapshots"):
        console.print("[bold yellow]⚠ Історія знімків порожня.[/bold yellow]")
        return
    
    table = Table(title="📜 Історія знімків mGit", border_style="cyan")
    table.add_column("ID", justify="center", style="bold cyan")
    table.add_column("Дата/Час", style="green")
    table.add_column("Файл", style="magenta")
    table.add_column("Коментар", style="white")
    
    for s in reversed(index["snapshots"]):
        table.add_row(str(s["id"]), s["timestamp"], os.path.basename(s["original_path"]), s["comment"])
    console.print(table)

def stats():
    index = get_index()
    if not index: return

    num_snapshots = len(index.get("snapshots", []))
    total_size_bytes = 0
    
    if os.path.exists(SNAPSHOTS_DIR):
        for dirpath, _, filenames in os.walk(SNAPSHOTS_DIR):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size_bytes += os.path.getsize(fp)
    
    size_kb = total_size_bytes / 1024
    
    stats_text = Text()
    stats_text.append("📊 Статистика mGit\n\n", style="bold cyan")
    stats_text.append("Всього знімків: ", style="white")
    stats_text.append(f"{num_snapshots}\n", style="bold green")
    stats_text.append("Останній ID: ", style="white")
    stats_text.append(f"{index.get('latest_id', 0)}\n", style="bold yellow")
    stats_text.append("Загальний розмір архіву: ", style="white")
    stats_text.append(f"{size_kb:.2f} KB\n", style="bold magenta")
    
    panel = Panel(stats_text, title="[bold blue]Аналітика репозиторію[/bold blue]", expand=False, border_style="blue")
    console.print(panel)

def diff(id1, id2):
    if id1 == id2:
        console.print("[bold yellow]⚠ Попередження:[/bold yellow] Ви намагаєтесь порівняти знімок сам із собою.")
        return
        
    index = get_index()
    if not index: return
    
    snap1 = next((s for s in index["snapshots"] if s["id"] == id1), None)
    snap2 = next((s for s in index["snapshots"] if s["id"] == id2), None)
    
    if not snap1 or not snap2:
        console.print("[bold red]✖ Помилка:[/bold red] Один або обидва ID знімків не знайдено в базі.")
        return
        
    path1 = os.path.join(SNAPSHOTS_DIR, snap1["filename"])
    path2 = os.path.join(SNAPSHOTS_DIR, snap2["filename"])
    
    try:
        with open(path1, "r", encoding="utf-8", errors="ignore") as f: lines1 = f.readlines()
        with open(path2, "r", encoding="utf-8", errors="ignore") as f: lines2 = f.readlines()
    except IOError as e:
        console.print(f"[bold red]✖ Помилка доступу до файлів знімків:[/bold red] {e}")
        return
    
    console.print(f"[bold cyan]Порівняння знімка #{id1} та знімка #{id2}:[/bold cyan]\n")
    
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
        console.print(f"[bold red]✖ Помилка:[/bold red] Знімок з ID {snap_id} не знайдено.")
        return
        
    src = os.path.join(SNAPSHOTS_DIR, snap["filename"])
    dest = snap["original_path"]
    
    with console.status(f"[bold cyan]Відновлення файлу до стану знімка #{snap_id}...[/bold cyan]", spinner="dots"):
        try:
            shutil.copy2(src, dest)
        except IOError as e:
            console.print(f"[bold red]✖ Помилка відновлення:[/bold red] Не вдалося перезаписати цільовий файл. Деталі: {e}")
            return
            
    console.print(f"[bold green]✔ Успіх:[/bold green] Файл відновлено до стану знімка #{snap_id}!")

def interactive_mode():
    import time
    while True:
        console.print("\n[bold cyan]=== 📦 mGit Інтерактивне меню ===[/bold cyan]")
        console.print("[green]1.[/green] Ініціалізувати репозиторій (init)")
        console.print("[green]2.[/green] Створити знімок файлу (snapshot)")
        console.print("[green]3.[/green] Перевірити статус файлу (status)")
        console.print("[green]4.[/green] Переглянути історію версій (log)")
        console.print("[green]5.[/green] Порівняти дві версії (diff)")
        console.print("[green]6.[/green] Відновити файл до версії (rollback)")
        console.print("[green]7.[/green] [bold magenta]Показати статистику (stats)[/bold magenta]")
        console.print("[red]0.[/red] Вихід")
        
        choice = console.input("\n[bold yellow]Ваш вибір:[/bold yellow] ").strip()
        
        if choice == "1":
            init()
        elif choice == "2":
            filepath = console.input("Шлях до файлу: ").strip()
            comment = console.input("Коментар до знімка: ").strip()
            snapshot(filepath, comment)
        elif choice == "3":
            filepath = console.input("Шлях до файлу: ").strip()
            status(filepath)
        elif choice == "4":
            log()
        elif choice == "5":
            try:
                id1 = int(console.input("Введіть ID першого знімка: ").strip())
                id2 = int(console.input("Введіть ID другого знімка: ").strip())
                diff(id1, id2)
            except ValueError:
                console.print("[bold red]Помилка:[/bold red] ID мають бути числами.")
        elif choice == "6":
            try:
                snap_id = int(console.input("Введіть ID знімка для відновлення: ").strip())
                rollback(snap_id)
            except ValueError:
                console.print("[bold red]Помилка:[/bold red] ID має бути числом.")
        elif choice == "7":
            stats()
        elif choice == "0":
            console.print("[bold green]Вихід із mGit. Роботу завершено.[/bold green]")
            break
        else:
            console.print("[bold red]Невідома команда, спробуйте ще раз.[/bold red]")
        
        time.sleep(0.5)

def main():
    if len(sys.argv) < 2:
        help_text = (
            "Ви запустили mGit без аргументів.\n\n"
            "[bold green]Формат використання з консолі:[/bold green]\n"
            "  python mgit.py <команда> [аргументи]\n\n"
            "[bold green]Доступні команди:[/bold green]\n"
            "  init      - Ініціалізувати новий репозиторій\n"
            "  snapshot  - Створити знімок (аргументи: <файл> '<коментар>')\n"
            "  status    - Перевірити наявність змін (аргументи: <файл>)\n"
            "  log       - Переглянути історію версій\n"
            "  diff      - Показати різницю між версіями (аргументи: <id1> <id2>)\n"
            "  rollback  - Відновити файл до версії (аргументи: <id>)\n"
            "  stats     - [Бонус] Показати статистику репозиторію"
        )
        panel = Panel(
            Align.center(help_text), 
            title="[bold cyan]mGit - Мінімальна система контролю версій[/bold cyan]", 
            subtitle="[grey50]v1.1 | Practice Edition[/grey50]",
            expand=False,
            border_style="cyan"
        )
        console.print(panel)
        
        choice = console.input("\n[bold yellow]Бажаєте перейти в Інтерактивне меню? (Y/n): [/bold yellow]").strip().lower()
        if choice != 'n':
            interactive_mode()
        else:
            console.print("[bold grey50]Роботу завершено. Використовуйте аргументи командного рядка![/bold grey50]")
        return

    cmd = sys.argv[1].lower()
    try:
        if cmd == "init": init()
        elif cmd == "snapshot": snapshot(sys.argv[2], sys.argv[3])
        elif cmd == "status": status(sys.argv[2])
        elif cmd == "log": log()
        elif cmd == "diff": diff(int(sys.argv[2]), int(sys.argv[3]))
        elif cmd == "rollback": rollback(int(sys.argv[2]))
        elif cmd == "stats": stats()
        else: console.print("[bold red]Невідома команда! Запустіть mgit.py без аргументів для довідки.[/bold red]")
    except IndexError:
        console.print("[bold red]Помилка вводу:[/bold red] Перевірте правильність та кількість аргументів команди.")
    except ValueError:
        console.print("[bold red]Помилка типу даних:[/bold red] ID знімків мають бути цілими числами.")

if __name__ == "__main__":
    main()