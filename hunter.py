
import requests, base64, os, socket, concurrent.futures, re

GITHUB_TOKEN = os.getenv('WORKFLOW_TOKEN')
REPO_NAME = "Catsss3/assets-distributor"

def check_validity(proxy):
    try:
        # Парсим хост и порт из ссылки
        pattern = r'@([^:/]+):(\d+)'
        match = re.search(pattern, proxy)
        if not match: return None
        
        host = match.group(1)
        port = int(match.group(2))
        
        # Пытаемся подключиться (таймаут 2.5 сек)
        with socket.create_connection((host, port), timeout=2.5):
            return proxy
    except:
        return None

def main():
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. Берем источники
    s_url = f"https://api.github.com/repos/{REPO_NAME}/contents/sources.txt"
    s_res = requests.get(s_url, headers={"Authorization": f"token {GITHUB_TOKEN}"} )
    if s_res.status_code != 200: return
    sources = base64.b64decode(s_res.json()['content']).decode().splitlines()
    
    found_proxies = []
    for url in sources:
        url = url.strip()
        if not url: continue
        try:
            r = requests.get(url, timeout=10, headers=headers)
            if r.status_code == 200:
                text = r.text
                # Декодируем, если источник в Base64
                if "://" not in text[:50]:
                    try: text = base64.b64decode(text).decode('utf-8')
                    except: pass
                found_proxies.extend(text.splitlines())
        except: continue

    # 2. Фильтруем протоколы (vless и hysteria2)
    target_proxies = [p.strip() for p in found_proxies if p.startswith(("vless://", "hy2://", "hysteria2://"))]
    unique_proxies = list(set(target_proxies))
    
    print(f"🔍 Найдено {len(unique_proxies)} кандидатов. Проверяем на валидность...")

    # 3. Проверка на выживаемость (в 100 потоков для скорости)
    valid_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(check_validity, unique_proxies))
        valid_list = [r for r in results if r]

    if not valid_list:
        print("❌ Ни один прокси не прошел проверку.")
        # Чтобы sub.txt не был совсем пустым и не ломал подписку, 
        # можно оставить старые или выдать ошибку. Но мы сделаем честно.
        final_str = ""
    else:
        final_str = "\n".join(valid_list)
        print(f"✅ Отобрано {len(valid_list)} рабочих конфигов.")

    # 4. Упаковка в Base64 (Pawdroid style)
    final_b64 = base64.b64encode(final_str.encode('utf-8')).decode('utf-8')
    
    # 5. Пушим в GitHub в файл sub.txt
    p_url = f"https://api.github.com/repos/{REPO_NAME}/contents/sub.txt"
    p_res = requests.get(p_url, headers={"Authorization": f"token {GITHUB_TOKEN}"} )
    sha = p_res.json().get('sha') if p_res.status_code == 200 else None
    
    payload = {
        "message": f"💅 Clean & Valid: {len(valid_list)} (VLESS/HY2)",
        "content": base64.b64encode(final_b64.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    requests.put(p_url, json=payload, headers={"Authorization": f"token {GITHUB_TOKEN}"} )
    print("🚀 Файл sub.txt успешно обновлен!")

if __name__ == "__main__":
    main()
