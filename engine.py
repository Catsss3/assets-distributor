import os, asyncio, aiohttp, base64, re, logging
from typing import List, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

async def tcp_ping(host, port):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=2.0)
        writer.close()
        await writer.wait_closed()
        return True
    except: return False

async def fetch(session, url):
    try:
        async with session.get(url, timeout=15.0) as resp:
            if resp.status != 200: return []
            text = await resp.text()
            if "vless://" not in text.lower() and len(text) > 30:
                try: text = base64.b64decode(re.sub(r'[^a-zA-Z0-9+/=]', '', text)).decode(errors='ignore')
                except: pass
            return text.splitlines()
    except: return []

async def main():
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [l.strip() for l in f if l.strip().lower().startswith("http")]
    async with aiohttp.ClientSession() as session:
        pages = await asyncio.gather(*[fetch(session, u) for u in urls])
    source_stats, all_raw = {}, []
    for url, lines in zip(urls, pages):
        valid = [ln.strip() for ln in lines if "vless://" in ln.lower()]
        source_stats[url] = {"total": len(valid), "alive": 0}
        all_raw.extend([(ln, url) for ln in valid])
    unique, pattern = {}, re.compile(r"@([^:/?#\s]+):(\d+)")
    for link, src in all_raw:
        m = pattern.search(link)
        if m:
            key = f"{m.group(1)}:{m.group(2)}"
            if key not in unique or len(link) > len(unique[key][0]): unique[key] = (link, src)
    async def check(data):
        link, src = data
        m = pattern.search(link)
        if m and await tcp_ping(m.group(1), int(m.group(2))): return (link, src)
        return None
    results = await asyncio.gather(*[check(d) for d in unique.values()])
    alive = []
    for r in results:
        if r:
            alive.append(r[0]); source_stats[r[1]]["alive"] += 1
    with open("distributor.txt", "w", encoding="utf-8") as f: f.write("\n".join(alive))
    print(f"💎 Найдено {len(alive)} потенциальных нод.")

if __name__ == "__main__": asyncio.run(main())