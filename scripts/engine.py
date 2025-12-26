
import requests
import re
import base64
import os
import socket
from concurrent.futures import ThreadPoolExecutor

CHECK_URL = "http://www.gstatic.com/generate_204"

def verify_proxy(proxy_link):
    try:
        server_info = proxy_link.split('@')[1].split('?')[0].split('#')[0]
        host, port = server_info.split(':')
        socket.setdefaulttimeout(5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, int(port))) == 0:
                return server_info, proxy_link
    except: pass
    return None, None

def gemini_discovery():
    # Здесь мы будем вызывать Gemini API для поиска новых ссылок.
    # Пока добавим логику защиты: читаем текущие источники, чтобы не дублировать.
    print("🤖 Gemini AI начинает сканирование сети в поиске сокровищ...")
    # (В следующей итерации мы вставим сюда прямой вызов API через секрет)
    return []

def run():
    # 1. Сначала поиск нового через AI
    new_sources = gemini_discovery()
    if os.path.exists('sources.txt'):
        with open('sources.txt', 'r+') as f:
            current = f.read()
            for src in new_sources:
                if src not in current:
                    f.write(f"\n{src}")

    # 2. Сбор и фильтрация
    with open('sources.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    found = []
    for url in urls:
        try:
            res = requests.get(url, timeout=15).text
            matches = re.findall(r'(?:vless|hysteria2)://[^\\s\\n\\r\\<\\>\"\']+', res)
            found.extend(matches)
        except: continue
    
    unique_raw = list(set(found))
    final_proxies = []
    seen_addresses = set()

    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(verify_proxy, unique_raw))
        for addr, link in results:
            if addr and addr not in seen_addresses:
                seen_addresses.add(addr)
                final_proxies.append(link)

    with open('distributor.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_proxies))
    with open('distributor.64', 'w', encoding='utf-8') as f:
        content_bytes = '\n'.join(final_proxies).encode('utf-8')
        f.write(base64.b64encode(content_bytes).decode('utf-8'))

    print(f"✨ Операция завершена! Найдено живых: {len(final_proxies)}")

if __name__ == "__main__":
    run()
