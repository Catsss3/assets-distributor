
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
    headers = {'User-Agent': 'Mozilla/5.0'}
    s_res = requests.get(f"https://api.github.com/repos/{REPO_NAME}/contents/sources.txt", 
                         headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if s_res.status_code != 200: return
    sources = base64.b64decode(s_res.json()['content']).decode().splitlines()
    
    raw_found = []
    for url in sources:
        try:
            r = requests.get(url.strip(), timeout=10, headers=headers)
            if r.status_code == 200:
                text = r.text
                if "vless://" not in text and "hy2://" not in text:
                    try: text = base64.b64decode(text).decode('utf-8')
                    except: pass
                raw_found.extend(text.splitlines())
        except: continue

    raw_list = list(set([p.strip() for p in raw_found if "vless://" in p or "hy2" in p]))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as exec:
        valid = [r for r in list(exec.map(check_proxy, raw_list)) if r]
    
    if not valid:
        print("❌ Нет живых прокси, файл не обновляю!")
        return

    # Упаковываем в ЧИСТЫЙ Base64 (без лишних переносов)
    plain_text = "\n".join(valid)
    b64_content = base64.b64encode(plain_text.encode('utf-8')).decode('utf-8')
    
    p_url = f"https://api.github.com/repos/{REPO_NAME}/contents/collected_proxies.txt"
    p_res = requests.get(p_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = p_res.json().get('sha') if p_res.status_code == 200 else None
    
    payload = {
        "message": f"💅 Blondie: {len(valid)} proxies (B64 Format)",
        "content": base64.b64encode(b64_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    requests.put(p_url, json=payload, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    print(f"🚀 Готово! Живых: {len(valid)}. Формат: Base64")

if __name__ == "__main__": main()
