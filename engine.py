import aiohttp, asyncio, os, re, base64

def decode_base64(data):
    try:
        data = data.strip().replace("\n", "").replace("\r", "")
        while len(data) % 4: data += '='
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

async def fetch(session, url):
    try:
        async with session.get(url, timeout=15) as res:
            return await res.text()
    except: return ""

async def main():
    if not os.path.exists("sources.txt"): 
        print("❌ НЕТ ФАЙЛА SOURCES.TXT")
        return
    
    with open("sources.txt", "r", encoding="utf-8") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    print(f"🚀 ТИТАН: Опрашиваем {len(urls)} источников...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    # СУПЕР-ЖАДНАЯ РЕГУЛЯРКА (хватает всё: vless, tuic, hy2, vmess, ss)
    # Ищем протокол, затем :// и всё до кавычки, пробела или конца строки
    pattern = r"(vless|tuic|hy2|hysteria2|vmess|ss|trojan)://[^\s'\"<>\n#]+"
    
    all_nodes = []
    for text in results:
        if not text: continue
        # Ищем в обычном тексте
        found_raw = re.findall(pattern, text)
        all_nodes.extend(found_raw)
        
        # Ищем в Base64 (некоторые файлы целиком зашифрованы)
        decoded = decode_base64(text)
        if decoded:
            found_decoded = re.findall(pattern, decoded)
            all_nodes.extend(found_decoded)
    
    # Чистка
    all_nodes = list(set([n.strip() for n in all_nodes]))
    
    with open("distributor.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_nodes))
    
    print(f"💎 ИТОГ: Найдено {len(all_nodes)} нод!")

if __name__ == "__main__":
    asyncio.run(main())