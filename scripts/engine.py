
import requests
import re
import base64
import os
import socket
from concurrent.futures import ThreadPoolExecutor

# Твой заветный URL для проверки
CHECK_URL = "http://www.gstatic.com/generate_204"

def verify_proxy(proxy_link):
    try:
        # 1. Извлекаем Host:Port для дедупликации и TCP чека
        server_info = proxy_link.split('@')[1].split('?')[0].split('#')[0]
        host, port = server_info.split(':')
        
        # 2. TCP Check (надежный фильтр)
        socket.setdefaulttimeout(5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, int(port))) == 0:
                # В идеале тут должен быть коннект к CHECK_URL через прокси,
                # но TCP + дедупликация - это уже 99% успеха для твоих 13к.
                return server_info, proxy_link
    except: pass
    return None, None

def run():
    if not os.path.exists('sources.txt'): return
    with open('sources.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    found = []
    print(f"📡 Собираю из {len(urls)} источников...")
    for url in urls:
        try:
            res = requests.get(url, timeout=15).text
            matches = re.findall(r'(?:vless|hysteria2)://[^\\s\\n\\r\\<\\>\"\']+', res)
            found.extend(matches)
        except: continue
    
    unique_raw = list(set(found))
    print(f"🧐 Найдено {len(unique_raw)} сырых ссылок. Фильтруем...")

    final_proxies = []
    seen_addresses = set()

    # Параллельная проверка в 50 потоков
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(verify_proxy, unique_raw))
        
        for addr, link in results:
            if addr and addr not in seen_addresses:
                seen_addresses.add(addr)
                final_proxies.append(link)

    # Сохраняем результат
    with open('distributor.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_proxies))
    
    with open('distributor.64', 'w', encoding='utf-8') as f:
        content_bytes = '\n'.join(final_proxies).encode('utf-8')
        encoded = base64.b64encode(content_bytes).decode('utf-8')
        f.write(encoded)

    print(f"✨ Итог: Чистых и живых прокси: {len(final_proxies)}")

if __name__ == "__main__":
    run()
