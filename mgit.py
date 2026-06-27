import os
import sys
import json
import shutil
import hashlib
import time
from datetime import datetime
from rich.console import Console, ColorSystem
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich import box

console = Console(color_system="truecolor", force_terminal=True)

MGIT_DIR = ".mgit"
SNAPSHOTS_DIR = os.path.join(MGIT_DIR, "snapshots")
INDEX_FILE = os.path.join(MGIT_DIR, "index.json")

def init():
    if os.path.exists(MGIT_DIR):
        console.print("[bold #FFFF00]⚠ Попередження: mGit репозиторій вже існує.[/bold #FFFF00]")
        return
    
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump({"snapshots": [], "latest_id": 0}, f, ensure_ascii=False, indent=4)
        
    with open(os.path.join(MGIT_DIR, ".gitignore"), "w", encoding="utf-8") as f:
        f.write("*\n")
            
    console.print("[bold #00FF00]✔ Успіх: Створено порожній ізольований репозиторій mGit.[/bold #00FF00]")

def get_index():
    if not os.path.exists(INDEX_FILE):
        console.print("[bold #FF0000]✖ Помилка: Репозиторій не ініціалізовано. Запустіть 'python mgit.py init'[/bold #FF0000]")
        return None
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        console.print("[bold #FFFF00]⚠ Попередження: Файл індексу пошкоджено. Автоматичне відновлення структури...[/bold #FFFF00]")
        default_index = {"snapshots": [], "latest_id": 0}
        save_index(default_index)
        return default_index

def save_index(index):
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=4)
    except IOError as e:
        console.print(f"[bold #FF0000]✖ Помилка запису: Не вдалося зберегти індекс. Деталі: {e}[/bold #FF0000]")

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def snapshot(file_path, comment):
    if not os.path.exists(file_path):
        console.print(f"[bold #FF0000]✖ Помилка: Файл '{file_path}' не знайдено.[/bold #FF0000]")
        return
        
    index = get_index()
    if index is None: return

    current_hash = get_file_hash(file_path)
    abs_path = os.path.abspath(file_path)
    
    file_snapshots = [s for s in index["snapshots"] if s["original_path"] == abs_path]
    if file_snapshots:
        if file_snapshots[-1].get("file_hash") == current_hash:
            console.print("[bold #FFFF00]⚠ Зміни відсутні: Файл ідентичний до останнього знімка.[/bold #FFFF00]")
            return

    index["latest_id"] += 1
    snap_id = index["latest_id"]
    
    snap_filename = f"snap_{snap_id}_{os.path.basename(file_path)}"
    dest_path = os.path.join(SNAPSHOTS_DIR, snap_filename)
    
    try:
        shutil.copy2(file_path, dest_path)
    except IOError as e:
        console.print(f"[bold #FF0000]✖ Помилка копіювання: {e}[/bold #FF0000]")
        return
    
    final_comment = comment.strip() or "Без коментарів"
    
    new_snapshot = {
        "id": snap_id,
        "filename": snap_filename,
        "original_path": abs_path,
        "file_hash": current_hash,
        "comment": final_comment,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    index["snapshots"].append(new_snapshot)
    save_index(index)
        
    console.print(f"[bold #00FF00]✔ Знімок #{snap_id} успішно створено![/bold #00FF00] [#00FF00]({final_comment})[/#00FF00] [bold #A0A0A0](Хеш: {current_hash[:8]})[/bold #A0A0A0]")

def status(file_path):
    if not os.path.exists(file_path):
        console.print(f"[bold #FF0000]✖ Помилка: Файл '{file_path}' не знайдено на диску.[/bold #FF0000]")
        return
        
    index = get_index()
    if not index: return

    abs_path = os.path.abspath(file_path)
    file_snapshots = [s for s in index["snapshots"] if s["original_path"] == abs_path]
    
    if not file_snapshots:
        panel = Panel(f"Файл [bold #00FFFF]{file_path}[/bold #00FFFF] ще не відстежується.", title="[bold #00FFFF]ℹ Статус[/bold #00FFFF]", border_style="#00FFFF", expand=False)
        console.print(panel)
        return

    last_snap = file_snapshots[-1]
    current_hash = get_file_hash(file_path)

    if last_snap.get("file_hash") == current_hash:
        panel = Panel(f"Файл [bold #00FF00]{file_path}[/bold #00FF00] не має незбережених змін.", title="[bold #00FF00]✔ Чисто[/bold #00FF00]", border_style="#00FF00", expand=False)
        console.print(panel)
    else:
        panel = Panel(f"Файл [bold #FFFF00]{file_path}[/bold #FFFF00] було змінено!\nРекомендується зробити новий snapshot.", title="[bold #FFFF00]⚠ Є зміни[/bold #FFFF00]", border_style="#FFFF00", expand=False)
        console.print(panel)

def log():
    index = get_index()
    if not index: return
    if not index.get("snapshots"):
        console.print("[bold #FFFF00]⚠ Історія знімків порожня.[/bold #FFFF00]")
        return
    
    table = Table(title="📜 Історія знімків mGit", border_style="#00FFFF", box=box.ROUNDED)
    table.add_column("ID", justify="center", style="bold #00FFFF")
    table.add_column("Дата/Час", style="#00FF00")
    table.add_column("Файл", style="#FF00FF")
    table.add_column("Коментар", style="#FFFFFF")
    
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
    stats_text.append("📊 Статистика mGit\n\n", style="bold #00FFFF")
    stats_text.append("Всього знімків: ", style="#FFFFFF")
    stats_text.append(f"{num_snapshots}\n", style="bold #00FF00")
    stats_text.append("Останній ID: ", style="#FFFFFF")
    stats_text.append(f"{index.get('latest_id', 0)}\n", style="bold #FFFF00")
    stats_text.append("Загальний розмір архіву: ", style="#FFFFFF")
    stats_text.append(f"{size_kb:.2f} KB\n", style="bold #FF00FF")
    
    panel = Panel(stats_text, title="[bold #0000FF]Аналітика репозиторію[/bold #0000FF]", expand=False, border_style="#0000FF")
    console.print(panel)

def diff(id1, id2):
    if id1 == id2:
        console.print("[bold #FFFF00]⚠ Попередження: Ви намагаєтесь порівняти знімок сам із собою.[/bold #FFFF00]")
        return
        
    index = get_index()
    if not index: return
    
    snap1 = next((s for s in index["snapshots"] if s["id"] == id1), None)
    snap2 = next((s for s in index["snapshots"] if s["id"] == id2), None)
    
    if not snap1 or not snap2:
        console.print("[bold #FF0000]✖ Помилка: Один або обидва ID знімків не знайдено в базі.[/bold #FF0000]")
        return
        
    path1 = os.path.join(SNAPSHOTS_DIR, snap1["filename"])
    path2 = os.path.join(SNAPSHOTS_DIR, snap2["filename"])
    
    try:
        with open(path1, "r", encoding="utf-8", errors="ignore") as f: lines1 = f.readlines()
        with open(path2, "r", encoding="utf-8", errors="ignore") as f: lines2 = f.readlines()
    except IOError as e:
        console.print(f"[bold #FF0000]✖ Помилка доступу до файлів знімків: {e}[/bold #FF0000]")
        return
    
    console.print(f"[bold #00FFFF]Порівняння знімка #{id1} та знімка #{id2}:[/bold #00FFFF]\n")
    
    import difflib
    d = difflib.Differ()
    diff_result = list(d.compare(lines1, lines2))
    
    for line in diff_result:
        if line.startswith("+ "):
            console.print(f"[#00FF00]{line.strip()}[/#00FF00]")
        elif line.startswith("- "):
            console.print(f"[#FF0000]{line.strip()}[/#FF0000]")
        elif line.startswith("  "):
            console.print(f"[#808080]{line.strip()}[/#808080]")

def rollback(snap_id):
    index = get_index()
    if not index: return
    
    snap = next((s for s in index["snapshots"] if s["id"] == snap_id), None)
    if not snap:
        console.print(f"[bold #FF0000]✖ Помилка: Знімок з ID {snap_id} не знайдено.[/bold #FF0000]")
        return
        
    console.print(f"\n[bold #00FFFF]=== Підготовка до відновлення файлу ===[/bold #00FFFF]")
    
    table = Table(title=f"📋 Деталі знімка #{snap_id} для відкату", border_style="#FFFF00", box=box.ROUNDED)
    table.add_column("ID", justify="center", style="bold #00FFFF")
    table.add_column("Дата/Час", style="#00FF00")
    table.add_column("Файл", style="#FF00FF")
    table.add_column("Коментар", style="#FFFFFF")
    table.add_row(str(snap["id"]), snap["timestamp"], os.path.basename(snap["original_path"]), snap["comment"])
    console.print(table)
    
    console.print(f"[bold #FFFF00]⚠ УВАГА: Оригінальний файл за шляхом [magenta]{snap['original_path']}[/magenta] буде примусово замінено.[/bold #FFFF00]")
    
    console.print("[bold #FF0000]Ви впевнені, що хочете виконати rollback? (y/n): [/bold #FF0000]", end="")
    confirm = input().strip().lower()
    
    if confirm not in ['y', 'yes', 'так']:
        console.print("[bold #0000FF]ℹ Операцію скасовано користувачем. Структуру файлів збережено без змін.[/bold #0000FF]")
        return

    src = os.path.join(SNAPSHOTS_DIR, snap["filename"])
    dest = snap["original_path"]
    
    try:
        shutil.copy2(src, dest)
    except IOError as e:
        console.print(f"[bold #FF0000]✖ Помилка відновлення: Не вдалося перезаписати цільовий файл. Деталі: {e}[/bold #FF0000]")
        return
            
    console.print(f"[bold #00FF00]✔ Успіх: Файл відновлено до стану знімка #{snap_id}![/bold #00FF00]")

def interactive_mode():
    while True:
        menu_content = (
            "[#00FF00]1.[/#00FF00] Ініціалізувати репозиторій (init)\n"
            "[#00FF00]2.[/#00FF00] Створити знімок файлу (snapshot)\n"
            "[#00FF00]3.[/#00FF00] Перевірити статус файлу (status)\n"
            "[#00FF00]4.[/#00FF00] Переглянути історію версій (log)\n"
            "[#00FF00]5.[/#00FF00] Порівняти дві версії (diff)\n"
            "[#00FF00]6.[/#00FF00] Відновити файл до версії (rollback)\n"
            "[#00FF00]7.[/#00FF00] [bold #FF00FF]Показати статистику (stats)[/bold #FF00FF]\n"
            "[#FF0000]0.[/#FF0000] Вихід"
        )
        
        console.print(Panel(
            menu_content, 
            title="[bold #00FFFF]=== 📦 mGit Інтерактивне меню ===[/bold #00FFFF]", 
            border_style="#00FFFF",
            box=box.ROUNDED,
            expand=False
        ))
        
        console.print("\n[bold #FFFF00]Ваш вибір:[/bold #FFFF00] ", end="")
        choice = input().strip()
        
        if choice == "1":
            init()
        elif choice == "2":
            console.print("[bold #00FFFF]Шлях до файлу:[/bold #00FFFF] ", end="")
            filepath = input().strip()
            console.print("[bold #00FFFF]Коментар до знімка:[/bold #00FFFF] ", end="")
            comment = input().strip()
            snapshot(filepath, comment)
        elif choice == "3":
            console.print("[bold #00FFFF]Шлях до файлу:[/bold #00FFFF] ", end="")
            filepath = input().strip()
            status(filepath)
        elif choice == "4":
            log()
        elif choice == "5":
            try:
                console.print("[bold #00FFFF]Введіть ID першого знімка:[/bold #00FFFF] ", end="")
                id1 = int(input().strip())
                console.print("[bold #00FFFF]Введіть ID другого знімка:[/bold #00FFFF] ", end="")
                id2 = int(input().strip())
                diff(id1, id2)
            except ValueError:
                console.print("[bold #FF0000]Помилка: ID мають бути цілими числами.[/bold #FF0000]")
        elif choice == "6":
            try:
                console.print("[bold #00FFFF]Введіть ID знімка для відновлення:[/bold #00FFFF] ", end="")
                snap_id = int(input().strip())
                rollback(snap_id) 
            except ValueError:
                console.print("[bold #FF0000]Помилка: ID має бути цілим числом.[/bold #FF0000]")
        elif choice == "7":
            stats()
        elif choice == "0":
            console.print("[bold #00FF00]Вихід із mGit. Роботу завершено.[/bold #00FF00]")
            break
        else:
            console.print("[bold #FF0000]Невідома команда, спробуйте ще раз.[/bold #FF0000]")
        
        time.sleep(0.5)

def main():
    if len(sys.argv) < 2:
        help_text = (
            "Ви запустили mGit без аргументів.\n\n"
            "[bold #00FF00]Формат використання з консолі:[/bold #00FF00]\n"
            "  python mgit.py <команда> [аргументи]\n\n"
            "[bold #00FF00]Доступні команди:[/bold #00FF00]\n"
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
            title="[bold #00FFFF]mGit - Мінімальна система контролю версій[/bold #00FFFF]", 
            subtitle="[#808080]v1.1 | Practice Edition[/#808080]",
            expand=False,
            border_style="#00FFFF"
        )
        console.print(panel)
        
        console.print("\n[bold #FFFF00]Бажаєте перейти в Інтерактивне меню? (Y/n): [/bold #FFFF00]", end="")
        choice = input().strip().lower()
        if choice != 'n':
            interactive_mode()
        else:
            console.print("[bold #808080]Роботу завершено. Використовуйте аргументи командного рядка![/bold #808080]")
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
        else: console.print("[bold #FF0000]Невідома команда! Запустіть mgit.py без аргументів для довідки.[/bold #FF0000]")
    except IndexError:
        console.print("[bold #FF0000]Помилка вводу: Перевірте правильність та кількість аргументів команди.[/bold #FF0000]")
    except ValueError:
        console.print("[bold #FF0000]Помилка типу даних: ID знімків мають бути цілими числами.[/bold #FF0000]")

if __name__ == "__main__":
    main()