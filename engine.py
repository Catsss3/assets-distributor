import asyncio, aiohttp, re, base64, os

async def fetch(session, url):
    try:
        # Ставим короткий тайм-аут: 5 секунд на коннект, 10 на чтение
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with session.get(url, headers=headers, timeout=timeout) as res:
            if res.status == 200:
                return await res.text()
    except: pass
    return ""

async def main():
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    # Ограничиваем количество одновременных соединений до 20
    connector = aiohttp.TCPConnector(limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(*[fetch(session, u) for u in urls])
    
    # Регулярка для быстрого поиска
    raw_pattern = r"(?:vless|vmess|trojan|ss|ssr|tuic|hysteria2|hy2)://[^\s\"'<>#]+"
    all_found = []
    
    for text in results:
        if not text or len(text) < 10: continue
        
        # 1. Быстрый поиск в чистом тексте
        all_found.extend(re.findall(raw_pattern, text, re.IGNORECASE))
        
        # 2. Умный поиск Base64 (только если текст похож на него)
        if len(text) > 20 and "=" in text[-3:] or len(text) % 4 == 0:
            try:
                decoded = base64.b64decode(text.strip()).decode('utf-8', errors='ignore')
                all_found.extend(re.findall(raw_pattern, decoded, re.IGNORECASE))
            except: pass

    # Фильтруем дубли и мусор
    nodes = list(set([n.strip() for n in all_found if len(n) > 15]))
    
    with open("distributor.txt", "w") as f:
        f.write("\n".join(nodes))
    
    print(f"💎 ИТОГ: Найдено {len(nodes)} нод.")

if __name__ == "__main__":
    asyncio.run(main())