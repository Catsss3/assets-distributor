
import asyncio, aiohttp, re, base64, os

# Используем зеркала, чтобы обойти блокировку Google Colab со стороны GitHub
def fix_url(url):
    if "raw.githubusercontent.com" in url:
        # Пробуем альтернативный домен-зеркало для обхода 404/403 в Колабе
        return url.replace("raw.githubusercontent.com", "raw.fastgit.org") 
    return url

async def fetch(session, url):
    try:
        fixed_url = fix_url(url)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        async with session.get(fixed_url, headers=headers, timeout=15) as res:
            if res.status == 200:
                return await res.text()
            # Если зеркало не сработало, пробуем напрямую через jsDelivr
            elif "github" in url:
                alt_url = url.replace("raw.githubusercontent.com", "cdn.jsdelivr.net/gh").replace("/main/", "@main/")
                async with session.get(alt_url, headers=headers, timeout=10) as res2:
                    if res2.status == 200: return await res2.text()
    except: pass
    return ""

async def main():
    with open("sources.txt", "r") as f:
        urls = [l.strip() for l in f if l.strip().startswith("http")]
    
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[fetch(session, u) for u in urls])
    
    pattern = r"(vless|tuic|hy2|hysteria2|vmess|ss|trojan)://[^\s'\"<>\n#]+"
    all_nodes = []
    for text in results:
        all_nodes.extend(re.findall(pattern, text))
        try:
            decoded = base64.b64decode(text).decode('utf-8', errors='ignore')
            all_nodes.extend(re.findall(pattern, decoded))
        except: pass

    all_nodes = list(set(all_nodes))
    with open("distributor.txt", "w") as f:
        f.write("\n".join(all_nodes))
    print(f"💎 Stella Titan 4.1 Gold: {len(all_nodes)} чистопородных нод.")

if __name__ == "__main__":
    asyncio.run(main())
