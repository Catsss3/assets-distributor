import aiohttp, asyncio, os, re

async def fetch(session, url):
    try:
        async with session.get(url, timeout=15) as res:
            return await res.text()
    except: return ""

async def main():
    if not os.path.exists("sources.txt"):
        print("❌ sources.txt не найден!")
        return
    
    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    print(f"🚀 Загружаем из {len(urls)} источников...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    # Регулярка для поиска любых ссылок vless, tuic, hy2
    pattern = r"(vless|tuic|hy2|hysteria2)://[^\s]+"
    all_nodes = []
    for text in results:
        found = re.findall(pattern, text)
        all_nodes.extend(found)
    
    # Убираем дубликаты
    all_nodes = list(set(all_nodes))
    with open("distributor.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_nodes))
    
    print(f"💎 Найдено {len(all_nodes)} потенциальных нод.")

if __name__ == "__main__":
    asyncio.run(main())