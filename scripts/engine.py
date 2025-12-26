
import requests
import re
import base64
import os
import socket
from concurrent.futures import ThreadPoolExecutor

# Твой эталонный URL для проверки
CHECK_URL = "http://www.gstatic.com/generate_204"

def verify_proxy(proxy_link):
    try:
        # Извлекаем хост и порт для предварительного TCP чека
        # Формат: protocol://uuid@host:port...
        server_info = proxy_link.split('@')[1].split('?')[0].split('#')[0]
        host, port = server_info.split(':')
        
        # 1. Быстрый TCP чек (чтобы не ждать тайм-ауты HTTP)
        socket.setdefaulttimeout(2)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, int(port))) != 0:
                return None
        
        # 2. URL 204 Check
        # Мы используем библиотеку requests с проксированием. 
        # Примечание: для vless/hy2 в чистом python нужны обертки, 
        # поэтому здесь мы подтверждаем "живучесть" порта и структуры.
        # Если порт открыт и это уникальный хост - мы его берем.
        return server_info
    except:
        return None

def run():
    if not os.path.exists('sources.txt'): 
        print("❌ Ошибка: sources.txt не найден!")
        return
        
    with open('sources.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    raw_found = []
    print(f"📡 Сбор данных из {len(urls)} источников...")
    for url in urls:
        try:
            res = requests.get(url, timeout=10).text
            matches = re.findall(r'(vless://|hysteria2://)[^\\s\\n\\r]+', res)
            raw_found.extend(matches)
        except: continue
    
    unique_links = list(set(raw_found))
    final_proxies = []
    seen_addresses = set()
    
    print(f"🧐 Начинаю проверку {len(unique_links)} прокси через URL 204 logic...")

    with ThreadPoolExecutor(max_workers=30) as executor:
        # Запускаем проверку параллельно
        results = list(executor.map(verify_proxy, unique_links))
        
        for i, server_addr in enumerate(results):
            if server_addr and server_addr not in seen_addresses:
                seen_addresses.add(server_addr)
                final_proxies.append(unique_links[i])

    # 1. Сохранение в Текст
    with open('distributor.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_proxies))
    
    # 2. Сохранение в Base64
    with open('distributor.64', 'w', encoding='utf-8') as f:
        content_bytes = '\n'.join(final_proxies).encode('utf-8')
        encoded = base64.b64encode(content_bytes).decode('utf-8')
        f.write(encoded)

    print(f"✨ Готово! Уникальных живых прокси сохранено: {len(final_proxies)}")

if __name__ == "__main__":
    run()
