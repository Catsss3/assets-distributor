
import os, base64, requests, socket, threading
from concurrent.futures import ThreadPoolExecutor

valid_configs = []
lock = threading.Lock()

def check_server(config):
    try:
        # Быстрая проверка порта
        addr = config.split('@')[1].split('?')[0].split('#')[0]
        host, port = addr.split(':')
        with socket.create_connection((host, int(port)), timeout=2):
            with lock:
                if config not in valid_configs: valid_configs.append(config)
    except: pass

def main():
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r") as fs:
        urls = [l.strip() for l in fs if l.strip() and not l.startswith("#")]

    all_raw = []
    for url in urls:
        try:
            r = requests.get(url, timeout=10).text
            try:
                data = base64.b64decode(r).decode('utf-8')
                all_raw.extend(data.splitlines())
            except: all_raw.extend(r.splitlines())
        except: continue

    configs = list(set([c.strip() for c in all_raw if c.startswith(('vless://', 'hysteria2://'))]))
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(check_server, configs)

    # Запись файлов по 500 штук
    for i in range(0, len(valid_configs), 500):
        chunk = valid_configs[i:i+500]
        name = "sub.txt" if i == 0 else f"sub{i//500}.txt"
        with open(name, "w") as out:
            out.write(base64.b64encode("\n".join(chunk).encode()).decode())

if __name__ == "__main__":
    main()
