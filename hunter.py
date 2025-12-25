
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
                # Если это уже base64 (часто бывает в сабах), декодим
                if "vless://" not in text and "hy2://" not in text:
                    try: text = base64.b64decode(text).decode('utf-8')
                    except: pass
                raw_found.extend(text.splitlines())
        except: continue

    # Фильтруем только протоколы и убираем дубли
    clean_list = []
    for p in raw_found:
        p = p.strip()
        if p.startswith(("vless://", "hysteria2://", "hy2://")):
            clean_list.append(p)
    
    unique_list = list(set(clean_list))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as exec:
        valid = [r for r in list(exec.map(check_proxy, unique_list)) if r]
    
    if not valid: return

    # Формируем финальную строку БЕЗ пустых строк
    content_str = "\n".join(valid)
    # Кодируем в Base64 один раз
    final_b64 = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
    
    # Пушим в GitHub
    p_url = f"https://api.github.com/repos/{REPO_NAME}/contents/collected_proxies.txt"
    p_res = requests.get(p_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = p_res.json().get('sha') if p_res.status_code == 200 else None
    
    payload = {
        "message": f"💅 Blondie Fix: {len(valid)} proxies",
        "content": base64.b64encode(final_b64.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    requests.put(p_url, json=payload, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    print(f"✅ Успешно! Живых: {len(valid)}")

if __name__ == "__main__": main()
