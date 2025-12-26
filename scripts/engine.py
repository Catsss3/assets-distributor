
import requests
import re
import base64
import os
import socket
from concurrent.futures import ThreadPoolExecutor

def decode_if_base64(text):
    # Попытка декодировать, если весь файл зашифрован
    try:
        # Простая проверка на b64
        if re.match(r'^[A-Za-z0-9+/]*={0,2}$', text.strip()):
            return base64.b64decode(text.strip()).decode('utf-8')
    except: pass
    return text

def verify_proxy(proxy_link):
    try:
        # Извлекаем хост и порт
        server_info = proxy_link.split('@')[1].split('?')[0].split('#')[0]
        host, port = server_info.split(':')
        
        # TCP чек с хорошим тайм-аутом
        socket.setdefaulttimeout(5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, int(port))) == 0:
                return server_info
    except: pass
    return None

def run():
    if not os.path.exists('sources.txt'): return
    with open('sources.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    found = []
    print(f"📡 Сбор из {len(urls)} источников...")
    
    for url in urls:
        try:
            res = requests.get(url, timeout=15).text
            content = decode_if_base64(res)
            # Ищем vless и hy2 (более гибкая регулярка)
            matches = re.findall(r'(vless://|hysteria2://)[^\\s\\n\\r\\<\\>\"\']+', content)
            found.extend(matches)
        except: continue
    
    unique_links = list(set(found))
    print(f"🧐 Найдено ссылок в сыром виде: {len(unique_links)}")
    
    final_proxies = []
    seen_addresses = set()

    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(verify_proxy, unique_links))
        for i, server_addr in enumerate(results):
            if server_addr and server_addr not in seen_addresses:
                seen_addresses.add(server_addr)
                final_proxies.append(unique_links[i])

    with open('distributor.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_proxies))
    
    with open('distributor.64', 'w', encoding='utf-8') as f:
        content_bytes = '\n'.join(final_proxies).encode('utf-8')
        f.write(base64.b64encode(content_bytes).decode('utf-8'))

    print(f"✨ Итог: Живых и уникальных: {len(final_proxies)}")

if __name__ == "__main__":
    run()
