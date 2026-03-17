import aiohttp, asyncio, os, re, base64

def decode_base64(data):
    try:
        # Убираем лишние пробелы и добавляем padding если надо
        data = data.strip().replace("\n", "").replace("\r", "")
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except:
        return ""

async def fetch(session, url):
    try:
        async with session.get(url, timeout=15) as res:
            return await res.text()
    except: return ""

async def main():
    if not os.path.exists("sources.txt"): return
    
    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    print(f"🚀 ТИТАН: Потрошим {len(urls)} источников...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    pattern = r"(vless|tuic|hy2|hysteria2)://[^\s|'|\"|<|>|#]+"
    all_nodes = []
    
    for text in results:
        if not text: continue
        # 1. Ищем в чистом виде
        all_nodes.extend(re.findall(pattern, text))
        
        # 2. Пробуем декодировать (вдруг там Base64 конфиг)
        decoded = decode_base64(text)
        if decoded:
            all_nodes.extend(re.findall(pattern, decoded))
            
    # Очистка и дедупликация
    all_nodes = list(set([n.strip() for n in all_nodes]))
    
    with open("distributor.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_nodes))
    
    print(f"💎 УЛОВ: Найдено {len(all_nodes)} потенциальных нод.")

if __name__ == "__main__":
    asyncio.run(main())