import os
import asyncio
import aiohttp
import base64
import re
import logging
from typing import List, Optional, Dict

# --- Настройки ---
BLACKLIST = ["trash-proxy.com", "free-vpn.org", "badnode.net", "127.0.0.1", "0.0.0.0"]

# Оставляем только элиту. Прощайте, трояны и швадовски!
PROTOCOLS = ["vless://", "hysteria2://", "hy2://", "tuic://"]

MAX_CONCURRENT_PINGS = 120
HTTP_TIMEOUT = 15.0          
TCP_TIMEOUT = 0.8            # Твой выбор: только быстрые ноды

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

async def tcp_ping(host: str, port: int, timeout: float = TCP_TIMEOUT) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except:
        return False

async def fetch(session: aiohttp.ClientSession, url: str) -> List[str]:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        async with session.get(url, timeout=HTTP_TIMEOUT, headers=headers) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
            if not any(p in text.lower() for p in PROTOCOLS) and len(text) > 30:
                try:
                    clean_text = re.sub(r'[^a-zA-Z0-9+/=]', '', text)
                    text = base64.b64decode(clean_text).decode(errors='ignore')
                except:
                    pass
            return text.splitlines()
    except:
        return []

async def main() -> None:
    if not os.path.exists("sources.txt"):
        logging.error("sources.txt не найден!")
        return

    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().lower().startswith("http")]

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, u) for u in urls]
        pages = await asyncio.gather(*tasks)
        
        source_stats = {}
        all_raw_links = []

        for url, lines in zip(urls, pages):
            valid_lines = [l.strip() for l in lines if any(p in l.lower() for p in PROTOCOLS)]
            source_stats[url] = {"total": len(valid_lines), "alive": 0}
            for l in valid_lines:
                all_raw_links.append((l, url))

    unique: Dict[str, tuple] = {}
    pattern = re.compile(r"@([^:/?#\s]+):(\d+)")

    for link, source_url in all_raw_links:
        if any(bad in link.lower() for bad in BLACKLIST): continue
        m = pattern.search(link)
        if not m: continue
        key = f"{m.group(1)}:{m.group(2)}"
        if key not in unique or len(link) > len(unique[key][0]):
            unique[key] = (link, source_url)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PINGS)

    async def check(link_data: tuple) -> Optional[tuple]:
        link, source_url = link_data
        async with semaphore:
            m = pattern.search(link)
            if not m: return None
            host, port = m.group(1), int(m.group(2))
            if await tcp_ping(host, port):
                return (link, source_url)
            return None

    results = await asyncio.gather(*[check(data) for data in unique.values()])
    
    alive_links = []
    for r in results:
        if r:
            link, source_url = r
            alive_links.append(link)
            source_stats[source_url]["alive"] += 1

    logging.info("--- 📊 ОТЧЕТ ПО ИСТОЧНИКАМ (КПД) ---")
    for url, stat in source_stats.items():
        short_url = url.split('/')[-1]
        if stat["total"] > 0:
            kpd = (stat["alive"] / stat["total"]) * 100
            logging.info(f"{short_url}: Найдено {stat['total']}, Живых {stat['alive']} ({kpd:.1f}%)")

    with open("distributor.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(alive_links))

    with open("distributor.64", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(alive_links).encode()).decode())

    logging.info(f"💎 Stella Titan 4.1 Gold: {len(alive_links)} чистопородных нод.")

if __name__ == "__main__":
    asyncio.run(main())
