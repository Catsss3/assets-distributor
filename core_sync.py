
import os, base64, requests, socket, threading
from concurrent.futures import ThreadPoolExecutor

valid_configs = []
lock = threading.Lock()

def check_server(config):
    try:
        addr = config.split('@')[1].split('?')[0].split('#')[0]
        host, port = addr.split(':')
        with socket.create_connection((host, int(port)), timeout=2):
            with lock:
                if config not in valid_configs: valid_configs.append(config)
    except: pass

def main():
    # Проверяем наличие файла
    if not os.path.exists("sources.txt"):
        print("❌ ОШИБКА: sources.txt не найден в папке!")
        return

    with open("sources.txt", "r") as fs:
        urls = [l.strip() for l in fs if l.strip() and not l.startswith("#")]
    
    print(f"📡 Найдено источников: {len(urls)}")

    all_raw = []
    for url in urls:
        try:
            r = requests.get(url, timeout=10).text
            # Проверка на base64
            try:
                data = base64.b64decode(r).decode('utf-8')
                all_raw.extend(data.splitlines())
            except:
                all_raw.extend(r.splitlines())
        except Exception as e:
            print(f"⚠️ Ошибка загрузки {url}: {e}")

    configs = list(set([c.strip() for c in all_raw if c.startswith(('vless://', 'hysteria2://'))]))
    print(f"🔍 Найдено уникальных конфигов: {len(configs)}")
    
    if not configs:
        print("❌ Нет конфигов для проверки!")
        return

    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(check_server, configs)

    print(f"✅ Валидных серверов: {len(valid_configs)}")

    # Запись
    for i in range(0, len(valid_configs), 500):
        chunk = valid_configs[i:i+500]
        name = "sub.txt" if i == 0 else f"sub{i//500}.txt"
        with open(name, "w") as out:
            out.write(base64.b64encode("\n".join(chunk).encode()).decode())
        print(f"💾 Создан файл: {name}")

if __name__ == "__main__":
    main()
