import os
import shutil
import time
import mgit
from rich.console import Console

console = Console()
TEST_FILE = "fighter_analytics.py"
TEST_MGIT_DIR = ".mgit"

def reset_env():
    """Очищає середовище перед початком тестування."""
    if os.path.exists(TEST_MGIT_DIR):
        shutil.rmtree(TEST_MGIT_DIR)
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

def run_comprehensive_test():
    console.print("\n[bold magenta]🚀 Запуск комплексного генератора тестів mGit...[/bold magenta]\n")
    reset_env()

    # --- КРОК 1: Ініціалізація ---
    console.print("[bold blue]► Крок 1: Ініціалізація порожнього репозиторію[/bold blue]")
    mgit.init()
    time.sleep(1)

    # --- КРОК 2: Базова версія коду ---
    console.print("\n[bold blue]► Крок 2: Створення V1 (Базова математична функція)[/bold blue]")
    v1_code = '''def calculate_win_rate(wins, losses):
    total = wins + losses
    if total == 0:
        return 0
    return (wins / total) * 100
'''
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write(v1_code)

    mgit.snapshot(TEST_FILE, "feat: додано базовий розрахунок вінрейту")
    time.sleep(1)

    # --- КРОК 3: Статус ---
    console.print("\n[bold blue]► Крок 3: Перевірка статусу чистого робочого дерева[/bold blue]")
    mgit.status(TEST_FILE)
    time.sleep(1)

    # --- КРОК 4: Складна модифікація коду ---
    console.print("\n[bold blue]► Крок 4: Створення V2 (Зміна існуючого коду та додавання нового)[/bold blue]")
    v2_code = '''def calculate_win_rate(wins, losses, draws=0):
    total = wins + losses + draws
    if total == 0:
        return 0.0
    return round((wins / total) * 100, 2)

def calculate_stamina_drain(rounds, cardio_base):
    return max(0, (rounds * 5) - cardio_base)
'''
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write(v2_code)
        
    mgit.status(TEST_FILE) # Має показати жовте попередження про зміни
    mgit.snapshot(TEST_FILE, "refactor: змінено логіку вінрейту (додано draws) та stamina_drain")
    time.sleep(1)

    # --- КРОК 5: Видалення та додавання ООП ---
    console.print("\n[bold blue]► Крок 5: Створення V3 (Видалення функції та додавання ООП класу)[/bold blue]")
    v3_code = '''def calculate_win_rate(wins, losses, draws=0):
    total = wins + losses + draws
    if total == 0:
        return 0.0
    return round((wins / total) * 100, 2)

class Fighter:
    def __init__(self, name, weight_kg):
        self.name = name
        self.weight_kg = weight_kg
        self.record = {"W": 0, "L": 0, "D": 0}
'''
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write(v3_code)

    mgit.snapshot(TEST_FILE, "feat: видалено функцію витривалості, додано клас Fighter")
    time.sleep(1)

    # --- КРОК 6: Історія та Аналітика ---
    console.print("\n[bold blue]► Крок 6: Генерація історії (log) та статистики (stats)[/bold blue]")
    mgit.log()
    print("\n")
    mgit.stats()
    time.sleep(1)

    # --- КРОК 7: Демонстрація роботи Diff ---
    console.print("\n[bold blue]► Крок 7: Аналіз змін (Diff)[/bold blue]")
    console.print("[grey50]Різниця між V1 та V2 (Зміна сигнатури функції та нові рядки):[/grey50]")
    mgit.diff(1, 2)
    
    console.print("\n[grey50]Різниця між V2 та V3 (Видалення функції та додавання класу):[/grey50]")
    mgit.diff(2, 3)
    time.sleep(1)

    # --- КРОК 8: Відкат ---
    console.print("\n[bold blue]► Крок 8: Перевірка безпеки - відкат до V2[/bold blue]")
    mgit.rollback(2)

    console.print("\n[bold green]🏁 Тестування успішно завершено![/bold green]")
    console.print("[bold yellow]ℹ Згенерований тестовий файл 'fighter_analytics.py' та база '.mgit' залишені на диску для ручної перевірки.[/bold yellow]")

if __name__ == "__main__":
    run_comprehensive_test()