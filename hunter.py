
import requests, base64, os, socket, concurrent.futures

GITHUB_TOKEN = os.getenv('WORKFLOW_TOKEN')
REPO_NAME = "Catsss3/assets-distributor"

def check_proxy(proxy):
    try:
        if not proxy or '@' not in proxy: return None
        host_port = proxy.split('@')[1].split('?')[0].split('#')[0]
        host, port = host_port.split(':')
        with socket.create_connection((host, int(port)), timeout=2):
            return proxy
    except: return None

def main():
    headers = {'User-Agent': 'Mozilla/5.0'}
    s_res = requests.get(f"https://api.github.com/repos/{REPO_NAME}/contents/sources.txt", 
                         headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if s_res.status_code != 200: return
    sources = base64.b64decode(s_res.json()['content']).decode().splitlines()
    
    raw_found = []
    for url in sources:
        url = url.strip()
        if not url: continue
        try:
            r = requests.get(url, timeout=10, headers=headers)
            if r.status_code == 200:
                text = r.text
                if "vless://" not in text and "hy2://" not in text:
                    try: text = base64.b64decode(text).decode('utf-8')
                    except: pass
                raw_found.extend(text.splitlines())
        except: continue

    valid_proxies = [p.strip() for p in raw_found if p.startswith(("vless://", "hy2://", "hysteria2://"))]
    unique_proxies = list(set(valid_proxies))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as exec:
        valid = [r for r in list(exec.map(check_proxy, unique_proxies)) if r]
    
    if not valid: 
        print("❌ Живых прокси не найдено!")
        return

    # ЧИСТЫЙ ТЕКСТ БЕЗ ОШИБОК
    content_str = "\n".join(valid)
    
    # ПУШИМ В GITHUB
    p_url = f"https://api.github.com/repos/{REPO_NAME}/contents/sub.txt"
    p_res = requests.get(p_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = p_res.json().get('sha') if p_res.status_code == 200 else None
    
    # Важно: кодируем строку в base64 для API GitHub
    encoded_content = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"💅 Blondie Fix: {len(valid)} proxies",
        "content": encoded_content,
        "sha": sha
    }
    
    final_res = requests.put(p_url, json=payload, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if final_res.status_code in [200, 201]:
        print(f"✅ Успешно! Файл sub.txt теперь содержит {len(valid)} строк.")
    else:
        print(f"❌ Ошибка пуша: {final_res.status_code}")

if __name__ == "__main__": main()
