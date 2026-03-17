import asyncio, aiohttp, re, base64, os

async def fetch(session, url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        async with session.get(url, headers=headers, timeout=20) as res:
            if res.status == 200:
                return await res.text()
    except: pass
    return ""

async def main():
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[fetch(session, u) for u in urls])
    
    # Максимально широкий поиск: ищем всё, что похоже на ссылку vmess/vless/etc
    # Добавляем захват всех символов до пробела или кавычки
    raw_pattern = r"(?:vless|vmess|trojan|ss|ssr|tuic|hysteria2|hy2)://[^\s\"'<>#]+"
    
    all_found = []
    for text in results:
        if not text: continue
        # Ищем в открытом тексте
        all_found.extend(re.findall(raw_pattern, text, re.IGNORECASE))
        
        # Пробуем декодировать всё подряд (вдруг там чистый Base64)
        try:
            # Чистим текст от пробелов для base64
            clean_text = "".join(text.split())
            decoded = base64.b64decode(clean_text).decode('utf-8', errors='ignore')
            all_found.extend(re.findall(raw_pattern, decoded, re.IGNORECASE))
        except: pass

    # Убираем дубли и пустые строки
    nodes = list(set([n.strip() for n in all_found if len(n) > 10]))
    
    with open("distributor.txt", "w") as f:
        f.write("\n".join(nodes))
    
    print(f"💎 ИТОГ: Найдено {len(nodes)} нод.")

if __name__ == "__main__":
    asyncio.run(main())