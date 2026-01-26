import os
import asyncio
import aiohttp
import base64
import re
from typing import List, Optional

TARGET_URL = "http://www.google.com/generate_204"
TIMEOUT = aiohttp.ClientTimeout(total=5)
CONCURRENT_LIMIT = 200
BLACKLIST = ["trash-proxy.com", "bad-provider.net"]
TXT_PATH = "distributor.txt"
B64_PATH = "distributor.64"

def deduplicate(links: List[str]) -> List[str]:
    """Убирает дубликаты, сравнивая только часть после '@'."""
    seen = set()
    unique = []
    for link in links:
        m = re.search(r'@([^?#\s]+)', link)
        addr = m.group(1) if m else link
        if addr not in seen:
            seen.add(addr)
            unique.append(link)
    return unique

async def check_url(session: aiohttp.ClientSession, link: str,
                    sem: asyncio.Semaphore) -> Optional[str]:
    """Возвращает link, если запрос прошёл с кодом 200/204."""
    if not re.match(r'^(vless|vmess|trojan|ss|http|https)://', link):
        return None
    async with sem:
        try:
            async with session.get(link, timeout=TIMEOUT) as resp:
                if resp.status in (200, 204):
                    return link
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None
        except Exception as e:
            # Остальные ошибки просто игнорируем, чтобы не спамить в лог
            return None
    return None

async def filter_engine():
    if not os.path.exists(TXT_PATH):
        print("⚠️ distributor.txt не найден.")
        return

    with open(TXT_PATH, "r", encoding="utf-8") as f:
        raw = [line.strip() for line in f if line.strip()]

    print(f"📥 Прочитано {len(raw)} строк.")
    cleaned = [l for l in raw if not any(b in l for b in BLACKLIST)]
    unique = deduplicate(cleaned)
    print(f"🔎 Уникальных ссылок: {len(unique)}")

    sem = asyncio.Semaphore(CONCURRENT_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONCURRENT_LIMIT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_url(session, link, sem) for link in unique]
        results = await asyncio.gather(*tasks)

    valid = [r for r in results if r]
    print(f"✅ Валидных ссылок: {len(valid)}")

    valid.sort(key=lambda x: 0 if x.startswith(("vless", "vmess")) else 1)

    with open(TXT_PATH, "w", encoding="utf-8") as f:
        f.write(os.linesep.join(valid))

    with open(B64_PATH, "w", encoding="utf-8") as f:
        b64 = base64.b64encode(os.linesep.join(valid).encode()).decode()
        f.write(b64)

if __name__ == "__main__":
    asyncio.run(filter_engine())
