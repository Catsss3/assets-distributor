import asyncio, aiohttp, re, base64, os

async def fetch(session, url):
    try:
        timeout = aiohttp.ClientTimeout(total=20, connect=7)
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with session.get(url, headers=headers, timeout=timeout) as res:
            if res.status == 200: return await res.text()
    except: pass
    return ""

async def main():
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    connector = aiohttp.TCPConnector(limit_per_host=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(*[fetch(session, u) for u in urls])
    
    raw_pattern = r"(?:vless|vmess|trojan|ss|ssr|tuic|hysteria2|hy2)://[^\s\"'<>#]+"
    all_found = []
    
    for text in results:
        if not text: continue
        all_found.extend(re.findall(raw_pattern, text, re.IGNORECASE))
        try:
            decoded = base64.b64decode(text.strip()).decode('utf-8', errors='ignore')
            all_found.extend(re.findall(raw_pattern, decoded, re.IGNORECASE))
        except: pass

    nodes = list(set([n.strip() for n in all_found if len(n) > 15]))
    
    with open("distributor.txt", "w") as f:
        f.write("\n".join(nodes))
    
    print(f"💎 ИТОГ: Собрано {len(nodes)} нод. Полный список готов к чеку.")

if __name__ == "__main__":
    asyncio.run(main())