import aiohttp, asyncio, os, re, base64

# Представляемся как браузер, чтобы GitHub нас не банил
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def decode_base64(data):
    try:
        data = data.strip().replace("\n", "").replace("\r", "")
        while len(data) % 4: data += '='
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

async def fetch(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=15) as res:
            if res.status == 200:
                return await res.text()
            else:
                print(f"⚠️ Ошибка {res.status} на источнике: {url[:50]}...")
                return ""
    except Exception as e:
        print(f"❌ Ошибка соединения: {url[:50]}... ({e})")
        return ""

async def main():
    if not os.path.exists("sources.txt"): return
    
    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    print(f"🚀 ТИТАН-ШПИОН: Опрашиваем {len(urls)} источников под маскировкой...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    pattern = r"(vless|tuic|hy2|hysteria2|vmess|ss|trojan)://[^\s'\"<>\n#]+"
    all_nodes = []
    
    for text in results:
        if not text or len(text) < 10: continue
        
        # 1. Прямой поиск
        found = re.findall(pattern, text)
        all_nodes.extend(found)
        
        # 2. Поиск в Base64
        decoded = decode_base64(text)
        if len(decoded) > 10:
            found_dec = re.findall(pattern, decoded)
            all_nodes.extend(found_dec)
            
    all_nodes = list(set([n.strip() for n in all_nodes]))
    
    with open("distributor.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_nodes))
    
    print(f"\n💎 ИТОГОВЫЙ УЛОВ: {len(all_nodes)} нод!")

if __name__ == "__main__":
    asyncio.run(main())