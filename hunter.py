
import requests, base64, os, socket, concurrent.futures

GITHUB_TOKEN = os.getenv('WORKFLOW_TOKEN')
REPO_NAME = "Catsss3/assets-distributor"

def check_proxy(proxy):
    try:
        host_port = proxy.split('@')[1].split('?')[0].split('#')[0]
        host, port = host_port.split(':')
        with socket.create_connection((host, int(port)), timeout=1.5): return proxy
    except: return None

def push_to_github(path, content, message):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{path}"
    res = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"} )
    sha = res.json().get('sha') if res.status_code == 200 else None
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    requests.put(url, json=payload, headers={"Authorization": f"token {GITHUB_TOKEN}"} )

def main():
    headers = {'User-Agent': 'Mozilla/5.0'}
    # 1. Поиск источников
    s_res = requests.get(f"https://api.github.com/repos/{REPO_NAME}/contents/sources.txt", 
                         headers={"Authorization": f"token {GITHUB_TOKEN}"} )
    if s_res.status_code != 200: return
    sources = base64.b64decode(s_res.json()['content']).decode().splitlines()
    
    raw_found = []
    for url in sources:
        try:
            r = requests.get(url.strip(), timeout=7, headers=headers)
            if r.status_code == 200:
                text = r.text
                if "vless://" not in text and "hy2://" not in text:
                    try: text = base64.b64decode(text).decode('utf-8')
                    except: pass
                raw_found.extend(text.splitlines())
        except: continue

    # 2. Валидация и чистка
    valid = list(set([p.strip() for p in raw_found if p.startswith(("vless://", "hy2://", "hysteria2://"))]))
    
    checked_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as exec:
        for result in exec.map(check_proxy, valid):
            if result: checked_list.append(result)

    if not checked_list: return

    # 3. Разбивка по 1000 и пуш
    chunk_size = 1000
    chunks = [checked_list[i:i + chunk_size] for i in range(0, len(checked_list), chunk_size)]
    
    for idx, chunk in enumerate(chunks):
        filename = "sub.txt" if idx == 0 else f"sub{idx}.txt"
        content = "\n".join(chunk)
        push_to_github(filename, content, f"💅 Blondie: {len(chunk)} proxies in {filename}")
        print(f"✅ Обновлен {filename} ({len(chunk)} шт.)")

if __name__ == "__main__": main()
