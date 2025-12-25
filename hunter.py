
import requests, base64, os, socket, concurrent.futures
GITHUB_TOKEN = os.getenv('WORKFLOW_TOKEN')
REPO_NAME = "Catsss3/assets-distributor"

def check_proxy(proxy):
    try:
        host_port = proxy.split('@')[1].split('?')[0].split('#')[0]
        host, port = host_port.split(':')
        with socket.create_connection((host, int(port)), timeout=2):
            return proxy
    except: return None

def main():
    # Качаем источники
    s_res = requests.get(f"https://api.github.com/repos/{REPO_NAME}/contents/sources.txt", 
                         headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sources = base64.b64decode(s_res.json()['content']).decode().splitlines()
    
    raw_found = []
    for url in sources:
        try:
            r = requests.get(url.strip(), timeout=10)
            if r.status_code == 200:
                text = r.text
                if "vless://" not in text:
                    try: text = base64.b64decode(text).decode('utf-8')
                    except: pass
                raw_found.extend(text.splitlines())
        except: continue

    # Чистим и проверяем ВСЁ
    raw_list = list(set([p.strip() for p in raw_found if "vless://" in p or "hy2" in p]))
    print(f"Проверяю {len(raw_list)} штук...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as exec:
        valid = [r for r in list(exec.map(check_proxy, raw_list)) if r]
    
    # Сохраняем результат
    content = "\n".join(valid)
    p_url = f"https://api.github.com/repos/{REPO_NAME}/contents/collected_proxies.txt"
    p_res = requests.get(p_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = p_res.json().get('sha') if p_res.status_code == 200 else None
    requests.put(p_url, json={"message": "💅 Blondie: Validated Update", "content": base64.b64encode(content.encode()).decode(), "sha": sha}, 
                 headers={"Authorization": f"token {GITHUB_TOKEN}"})
if __name__ == "__main__": main()
