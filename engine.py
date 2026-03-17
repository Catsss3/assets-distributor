import os
import asyncio
import aiohttp
import base64
import re
import logging
from typing import List, Dict, Optional, Tuple

BLACKLIST = ["127.0.0.1", "0.0.0.0"]
PROTOCOLS = ["vless://", "hysteria2://", "hy2://", "tuic://"]
MAX_CONCURRENT_PINGS = 150
HTTP_TIMEOUT = 15.0
TCP_TIMEOUT = 2.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

async def tcp_ping(host: str, port: int) -> bool:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=TCP_TIMEOUT)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception: return False

async def fetch(session: aiohttp.ClientSession, url: str) -> List[str]:
    try:
        async with session.get(url, timeout=HTTP_TIMEOUT) as resp:
            if resp.status != 200: return []
            text = await resp.text()
            if not any(p in text.lower() for p in PROTOCOLS) and len(text) > 30:
                try:
                    cleaned = re.sub(r'[^a-zA-Z0-9+/=]', '', text)
                    text = base64.b64decode(cleaned).decode(errors="ignore")
                except Exception: pass
            return text.splitlines()
    except Exception: return []

async def main() -> None:
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().lower().startswith("http")]
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, u) for u in urls]
        pages = await asyncio.gather(*tasks)
    source_stats, all_raw = {}, []
    for url, lines in zip(urls, pages):
        valid = [ln.strip() for ln in lines if any(p in ln.lower() for p in PROTOCOLS)]
        source_stats[url] = {"total": len(valid), "alive": 0}
        all_raw.extend([(ln, url) for ln in valid])
    unique, pattern = {}, re.compile(r"@([^:/?#\s]+):(\d+)")
    for link, src in all_raw:
        m = pattern.search(link)
        if not m: continue
        key = f"{m.group(1)}:{m.group(2)}"
        if key not in unique or len(link) > len(unique[key][0]): unique[key] = (link, src)
    
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PINGS)
    
    # ИСПРАВЛЕНО: Убрали | и использовали Optional
    async def check(data: Tuple) -> Optional[Tuple]:
        link, src = data
        m = pattern.search(link)
        if m and await tcp_ping(m.group(1), int(m.group(2))): return (link, src)
        return None

    results = await asyncio.gather(*[check(d) for d in unique.values()])
    alive = []
    for r in results:
        if r:
            alive.append(r[0]); source_stats[r[1]]["alive"] += 1
    
    print("\n--- 📊 ОТЧЕТ ПО ИСТОЧНИКАМ ---")
    for url, stats in source_stats.items():
        if stats["total"] > 0:
            p = (stats["alive"] / stats["total"]) * 100
            print(f"{url.split('/')[-1]}: {stats['alive']}/{stats['total']} ({p:.1f}%)")
    
    with open("distributor.txt", "w", encoding="utf-8") as f: 
        f.write("\n".join(alive))
    print(f"💎 Найдено {len(alive)} потенциальных нод.")

if __name__ == "__main__": asyncio.run(main())