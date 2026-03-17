import asyncio, aiohttp, re, base64, os

async def fetch(session, url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with session.get(url, headers=headers, timeout=15) as res:
            if res.status == 200: return await res.text()
    except: pass
    return ""

async def main():
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    pattern = r"(vless|tuic|hy2|hysteria2|vmess|ss|trojan)://[^\s'\"<>\n#]+"
    all_nodes = []
    for text in results:
        if not text: continue
        all_nodes.extend(re.findall(pattern, text))
        try:
            # Пытаемся декодировать, если там Base64
            decoded = base64.b64decode(text).decode('utf-8', errors='ignore')
            all_nodes.extend(re.findall(pattern, decoded))
        except: pass
            
    nodes = list(set([n.strip() for n in all_nodes]))
    with open("distributor.txt", "w") as f:
        f.write("\n".join(nodes))
    print(f"💎 ИТОГ: Найдено {len(nodes)} нод.")

if __name__ == "__main__":
    asyncio.run(main())