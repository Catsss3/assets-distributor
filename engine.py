import os, asyncio, aiohttp, base64, re
from typing import List, Optional

BLACKLIST = ["trash-proxy.com", "free-vpn.org", "badnode.net", "127.0.0.1", "0.0.0.0"]

async def tcp_ping(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except: return False

async def fetch(session: aiohttp.ClientSession, url: str) -> List[str]:
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status != 200: return []
            text = await resp.text()
            if "vless://" not in text and len(text) > 50:
                try: text = base64.b64decode(text.strip()).decode()
                except: pass
            return text.splitlines()
    except: return []

async def main() -> None:
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().startswith("http")]
    if not urls: return
    async with aiohttp.ClientSession() as session:
        pages = await asyncio.gather(*[fetch(session, u) for u in urls])
    raw_links = [l.strip() for p in pages for l in p if "vless://" in l.lower()]
    unique = {}
    for link in raw_links:
        if any(bad in link.lower() for bad in BLACKLIST): continue
        try:
            m = re.search(r"@([^:]+):(\d+)", link)
            if not m: continue
            key = f"{m.group(1)}:{m.group(2)}"
            if key not in unique or len(link) > len(unique[key]): unique[key] = link
        except: continue
    semaphore = asyncio.Semaphore(100)
    async def check(link: str) -> Optional[str]:
        async with semaphore:
            m = re.search(r"@([^:]+):(\d+)", link)
            if m and await tcp_ping(m.group(1), int(m.group(2))): return link
            return None
    results = await asyncio.gather(*[check(l) for l in unique.values()])
    alive = [r for r in results if r]
    with open("distributor.txt", "w", encoding="utf-8") as f: f.write("\n".join(alive))
    with open("distributor.64", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(alive).encode()).decode())
    print(f"💎 Titan 3.0 Sync: {len(alive)} links.")

if __name__ == '__main__':
    asyncio.run(main())
