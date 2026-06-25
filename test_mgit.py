import os
import shutil
import mgit

# Налаштування тестового середовища
TEST_FILE = "test_dummy.txt"
TEST_MGIT_DIR = ".mgit"

def setup():
    """Створює тестовий файл та ініціалізує чистий репозиторій."""
    if os.path.exists(TEST_MGIT_DIR):
        shutil.rmtree(TEST_MGIT_DIR)
    
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write("Line 1\nLine 2\n")
    
    mgit.init()

def teardown():
    """Прибирає за собою після тестування."""
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    if os.path.exists(TEST_MGIT_DIR):
        shutil.rmtree(TEST_MGIT_DIR)

def run_tests():
    print("🚀 Запуск тестів mGit...\n")
    setup()
    
    try:
        # Тест 1: Створення першого знімка
        mgit.snapshot(TEST_FILE, "Test commit 1")
        index = mgit.get_index()
        assert len(index["snapshots"]) == 1, "Помилка: Знімок не зберігся в індексі!"
        print("✅ Тест 1: Перший знімок створено успішно.")

        # Тест 2: Спроба створити дублікат (файл не мінявся)
        # Оскільки ми додали хешування, довжина списку знімків має лишитися = 1
        print("\nОчікується попередження про відсутність змін:")
        mgit.snapshot(TEST_FILE, "Test commit 2 - duplicate")
        index = mgit.get_index()
        assert len(index["snapshots"]) == 1, "Помилка: Створено дублікат знімка без змін файлу!"
        print("✅ Тест 2: Захист від дублікатів працює (через SHA-256).")
        
        # Тест 3: Зміна файлу і новий знімок
        with open(TEST_FILE, "a", encoding="utf-8") as f:
            f.write("Line 3 - new modifications\n")
        
        mgit.snapshot(TEST_FILE, "Test commit 3 - updated")
        index = mgit.get_index()
        assert len(index["snapshots"]) == 2, "Помилка: Змінений файл не зберігся як новий знімок!"
        print("✅ Тест 3: Змінений файл успішно розпізнано та збережено.")
        
    finally:
        teardown()
        print("\n🏁 Тестування завершено. Середовище очищено.")

if __name__ == "__main__":
    run_tests()