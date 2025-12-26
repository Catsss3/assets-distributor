
import requests
import re
import base64
import os

def force_decode(text):
    # Пытаемся декодировать Base64, даже если там есть мусор
    try:
        # Убираем пробелы и переносы, которые часто ломают b64
        cleaned = re.sub(r'[^a-zA-Z0-9+/=]', '', text.strip())
        return base64.b64decode(cleaned + "===").decode('utf-8', errors='ignore')
    except:
        return text

def run():
    if not os.path.exists('sources.txt'): return
    with open('sources.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    found = []
    print(f"📡 Начинаю агрессивный сбор из {len(urls)} источников...")
    
    for url in urls:
        try:
            # Добавляем User-Agent, чтобы сайты не блокировали нас
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            res = requests.get(url, headers=headers, timeout=20).text
            
            # Ищем ключи в сыром тексте
            raw_matches = re.findall(r'(?:vless|hysteria2)://[^\\s\\n\\r\\<\\>\"\']+', res)
            found.extend(raw_matches)
            
            # А теперь пробуем декодировать и искать внутри
            decoded = force_decode(res)
            decoded_matches = re.findall(r'(?:vless|hysteria2)://[^\\s\\n\\r\\<\\>\"\']+', decoded)
            found.extend(decoded_matches)
            
        except Exception as e:
            print(f"⚠️ Ошибка на {url}: {e}")
            continue
    
    # Убираем дубликаты строк (простая дедупликация)
    final_proxies = list(set(found))
    print(f"💎 Улов: Найдено {len(final_proxies)} уникальных ссылок!")

    # Сохраняем всё как есть (пока без жестких проверок портов)
    with open('distributor.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_proxies))
    
    with open('distributor.64', 'w', encoding='utf-8') as f:
        content_bytes = '\n'.join(final_proxies).encode('utf-8')
        f.write(base64.b64encode(content_bytes).decode('utf-8'))

if __name__ == "__main__":
    run()
