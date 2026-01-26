import os, asyncio, aiohttp, base64, re

BLACKLIST = ["trash-proxy.com", "free-vpn.org", "badnode.net", "127.0.0.1", "0.0.0.0"]

async def tcp_ping(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception: return False

async def fetch(session: aiohttp.ClientSession, url: str) -> list[str]:
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status == 200:
                return (await resp.text()).splitlines()
    except Exception: pass
    return []

async def main() -> None:
    if not os.path.exists("sources.txt"):
        print("❌ sources.txt not found")
        return

    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().startswith("http")]

    print(f"📡 Downloading from {len(urls)} sources...")
    async with aiohttp.ClientSession() as session:
        pages = await asyncio.gather(*[fetch(session, u) for u in urls], return_exceptions=True)
    
    raw_links = [line.strip() for page in pages if isinstance(page, list) for line in page if "vless://" in line.lower()]

    unique = {}
    for link in raw_links:
        if any(bad in link.lower() for bad in BLACKLIST): continue
        m = re.search(r"vless://([^@]+)@([^:/?#]+):(\d+)", link, re.IGNORECASE)
        if not m: continue

        host, port = m.group(2), int(m.group(3))
        key = f"{host}:{port}"
        params_count = link.count("&") + link.count("?")

        if key not in unique or params_count > unique[key]["p_count"]:
            unique[key] = {"link": link, "host": host, "port": port, "p_count": params_count}

    semaphore = asyncio.Semaphore(60)
    async def check(entry: dict) -> str | None:
        async with semaphore:
            alive = await tcp_ping(entry["host"], entry["port"])
            return entry["link"] if alive else None

    print(f"🔬 Pinging {len(unique)} unique servers...")
    results = await asyncio.gather(*[check(v) for v in unique.values()])
    alive_links = [r for r in results if r]
    
    alive_links.sort(key=lambda x: 0 if any(w in x.lower() for w in ("reality", "pbk", "security=reality")) else 1)

    with open("distributor.txt", "w", encoding="utf-8") as f: f.write("\n".join(alive_links))
    with open("distributor.64", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(alive_links).encode()).decode())
    print(f"✅ Success! Live servers: {len(alive_links)}")

if __name__ == "__main__":
    asyncio.run(main())
