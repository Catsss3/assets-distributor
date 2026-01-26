import os, asyncio, aiohttp, base64, re
async def tcp_ping(h, p, t=2):
    try:
        c = asyncio.open_connection(h, p)
        r, w = await asyncio.wait_for(c, timeout=t)
        w.close()
        await w.wait_closed()
        return True
    except: return False
async def main():
    if not os.path.exists("sources.txt"): return
    with open("sources.txt", "r") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    async with aiohttp.ClientSession() as s:
        p = await asyncio.gather(*[s.get(u, timeout=15) for u in urls], return_exceptions=True)
        raw = []
        for r in p:
            if hasattr(r, 'status') and r.status == 200:
                raw.extend((await r.text()).splitlines())
    uniq = {}
    for l in raw:
        if "vless://" in l:
            m = re.search(r'@([^:/?#]+):(\d+)', l)
            if m:
                k = f"{m.group(1)}:{m.group(2)}"
                if k not in uniq: uniq[k] = {"l": l, "h": m.group(1), "p": int(m.group(2))}
    sem = asyncio.Semaphore(50)
    async def check(i):
        async with sem: return i['l'] if await tcp_ping(i['h'], i['p']) else None
    res = await asyncio.gather(*[check(i) for i in uniq.values()])
    v = [r for r in res if r]
    v.sort(key=lambda x: 0 if "reality" in x.lower() else 1)
    with open("distributor.txt", "w", encoding="utf-8") as f: f.write("\n".join(v))
    with open("distributor.64", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(v).encode()).decode())
if __name__ == "__main__": asyncio.run(main())
