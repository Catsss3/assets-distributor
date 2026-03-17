import os
import asyncio
import aiohttp
import base64
import re
import logging
from typing import List, Optional, Dict

# ----------------------------------------------------------------------
# Настройки
# ----------------------------------------------------------------------
BLACKLIST = [
    "trash-proxy.com",
    "free-vpn.org",
    "badnode.net",
    "127.0.0.1",
    "0.0.0.0",
]

PROTOCOLS = [
    "vless://",
    "hysteria2://",
    "hy2://",
    "tuic://",
    "ss://",
    "trojan://",
]

MAX_CONCURRENT_PINGS = 120
HTTP_TIMEOUT = 15.0          # Увеличила для медленных источников
TCP_TIMEOUT = 0.8           # Увеличила для стабильности на МТС

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

# ----------------------------------------------------------------------
# Асинхронные функции
# ----------------------------------------------------------------------
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
                logging.warning(f"Status {resp.status} for {url}")
                return []

            text = await resp.text()

            # Декодирование base64 если нужно
            if not any(p in text.lower() for p in PROTOCOLS) and len(text) > 30:
                try:
                    # Чистим текст от возможных пробелов и переносов для b64
                    clean_text = re.sub(r'[^a-zA-Z0-9+/=]', '', text)
                    text = base64.b64decode(clean_text).decode(errors='ignore')
                except Exception as exc:
                    logging.debug(f"Base64 error for {url}: {exc}")

            return text.splitlines()
    except Exception as exc:
        logging.error(f"Fetch error {url}: {exc}")
        return []

# ----------------------------------------------------------------------
# Основная логика
# ----------------------------------------------------------------------
async def main() -> None:
    if not os.path.exists("sources.txt"):
        logging.error("sources.txt not found!")
        return

    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().lower().startswith("http")]

    if not urls:
        logging.error("No URLs in sources.txt")
        return

    async with aiohttp.ClientSession() as session:
        pages = await asyncio.gather(*[fetch(session, u) for u in urls])

    # Сбор всех ссылок
    raw_links = []
    for page in pages:
        for line in page:
            line = line.strip()
            if any(proto in line.lower() for proto in PROTOCOLS):
                raw_links.append(line)

    unique: Dict[str, str] = {}
    # Регулярка для извлечения host и port
    pattern = re.compile(r"@([^:/?#\s]+):(\d+)")

    for link in raw_links:
        if any(bad in link.lower() for bad in BLACKLIST):
            continue

        m = pattern.search(link)
        if not m:
            continue

        host, port = m.group(1), m.group(2)
        key = f"{host}:{port}"

        # Берем самый длинный конфиг (обычно там больше параметров обфускации)
        if key not in unique or len(link) > len(unique[key]):
            unique[key] = link

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PINGS)

    async def check(link: str) -> Optional[str]:
        async with semaphore:
            m = pattern.search(link)
            if not m: return None
            host, port = m.group(1), int(m.group(2))
            if await tcp_ping(host, port):
                return link
            return None

    results = await asyncio.gather(*[check(l) for l in unique.values()])
    alive = [r for r in results if r]

    # Всегда обновляем файлы (даже если список пустой, чтобы затереть старье)
    with open("distributor.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(alive))

    with open("distributor.64", "w", encoding="utf-8") as f:
        content = "\n".join(alive)
        f.write(base64.b64encode(content.encode()).decode())

    logging.info(f"💎 Stella Titan 4.0 Gold: {len(alive)} alive nodes.")

if __name__ == "__main__":
    asyncio.run(main())
