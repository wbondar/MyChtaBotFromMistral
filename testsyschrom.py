import platform
import subprocess
import sys

def get_os_info():
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
    }

def get_chromium_info():
    try:
        # Проверяем, установлен ли Chromium
        chromium_path = subprocess.check_output(["which", "chromium"], text=True).strip()
        # Получаем версию Chromium
        version = subprocess.check_output([chromium_path, "--version"], text=True).strip()
        return {
            "path": chromium_path,
            "version": version
        }
    except subprocess.CalledProcessError:
        return {
            "error": "Chromium не найден в системе."
        }

def main():
    print("=== Информация об ОС ===")
    os_info = get_os_info()
    for key, value in os_info.items():
        print(f"{key.capitalize()}: {value}")

    print("\n=== Информация о Chromium ===")
    chromium_info = get_chromium_info()
    if "error" in chromium_info:
        print(chromium_info["error"])
    else:
        print(f"Путь: {chromium_info['path']}")
        print(f"Версия: {chromium_info['version']}")

if __name__ == "__main__":
    main()
