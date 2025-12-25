
import requests, base64, os, socket, concurrent.futures, re, time

GITHUB_TOKEN = os.getenv('WORKFLOW_TOKEN')
REPO_NAME = "Catsss3/assets-distributor"

def check_validity(proxy):
    try:
        pattern = r'@([^:/]+):(\d+)'
        match = re.search(pattern, proxy)
        if not match: return None
        host, port = match.group(1), int(match.group(2))
        start = time.time()
        with socket.create_connection((host, port), timeout=2.0):
            return (time.time() - start, proxy)
    except: return None

def push_to_github(filename, content_b64):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{filename}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"} )
    sha = r.json().get('sha') if r.status_code == 200 else None
    
    # Кодируем содержимое еще раз в b64 для API Гитхаба
    payload = {
        "message": f"💅 Update {filename}",
        "content": base64.b64encode(content_b64.encode()).decode(),
        "sha": sha
    }
    requests.put(url, json=payload, headers={"Authorization": f"token {GITHUB_TOKEN}"} )

def main():
    headers = {'User-Agent': 'Mozilla/5.0'}
    s_res = requests.get(f"https://api.github.com/repos/{REPO_NAME}/contents/sources.txt", 
                         headers={"Authorization": f"token {GITHUB_TOKEN}"} )
    if s_res.status_code != 200: return
    sources = base64.b64decode(s_res.json()['content']).decode().splitlines()
    
    raw_list = []
    for url in sources:
        try:
            r = requests.get(url.strip(), timeout=10, headers=headers)
            if r.status_code == 200:
                text = r.text
                if "://" not in text[:50]:
                    try: text = base64.b64decode(text).decode('utf-8')
                    except: pass
                raw_list.extend(text.splitlines())
        except: continue

    unique = list(set([p.strip() for p in raw_list if p.startswith(("vless://", "hy2://", "hysteria2://"))]))
    print(f"🔍 Проверяем {len(unique)} серверов...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as exec:
        results = [r for r in list(exec.map(check_validity, unique)) if r]
    
    # Сортируем по скорости
    results.sort(key=lambda x: x[0])
    all_valid = [r[1] for r in results]
    
    # Режем на куски по 500
    chunk_size = 500
    for i in range(0, len(all_valid), chunk_size):
        chunk = all_valid[i:i + chunk_size]
        filename = "sub.txt" if i == 0 else f"sub{i // chunk_size}.txt"
        
        # Делаем Base64 от списка прокси (Pawdroid style)
        chunk_str = "\n".join(chunk)
        chunk_b64 = base64.b64encode(chunk_str.encode()).decode()
        
        push_to_github(filename, chunk_b64)
        print(f"✅ Создан {filename} с {len(chunk)} серверами")
        if i // chunk_size >= 10: break # Ограничимся 10 файлами (5000 серверов), чтобы не спамить

if __name__ == "__main__": main()
