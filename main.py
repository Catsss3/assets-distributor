
import requests, base64, socket, concurrent.futures, re
import google.generativeai as genai
from github import Github, Auth
import os

# Секреты из GitHub Secrets
GITHUB_TOKEN = os.getenv('WORKFLOW_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

def check_tcp(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=1.5):
            return True
    except: return False

def is_cloudflare(ip):
    try:
        host = socket.gethostbyaddr(ip)[0]
        return "cloudflare" in host.lower()
    except: return False

def validate_node(config):
    # Фильтр только VLESS и Hysteria2
    if not (config.startswith('vless://') or config.startswith('hysteria2://')):
        return None
    try:
        # Извлекаем IP и порт (упрощенно)
        data = config.split('@')[1].split('?')[0].split('#')[0]
        ip, port = data.split(':')
        if check_tcp(ip, int(port)):
            return config
    except: pass
    return None

def run():
    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    repo = g.get_repo("Catsss3/assets-distributor")
    
    # Сбор источников
    urls = ["https://raw.githubusercontent.com/yebekhe/TVProxy/main/sub/mix"] # Добавь сюда свои 27
    raw_nodes = []
    for u in urls:
        try: raw_nodes.extend(requests.get(u).text.splitlines())
        except: continue
        
    # Чистка (TCP + Дубликаты)
    unique_raw = list(set(raw_nodes))
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        valid_nodes = [n for n in ex.map(validate_node, unique_raw) if n]
    
    # Фасовка по 500
    for i in range(26):
        chunk = valid_nodes[i*500 : (i+1)*500]
        if not chunk: break
        content = base64.b64encode("\n".join(chunk).encode()).decode()
        f_name = f"sub_list{i+1}.txt"
        try:
            curr = repo.get_contents(f_name)
            repo.update_file(f_name, "💅 Elite Sync", content, curr.sha)
        except:
            repo.create_file(f_name, "✨ Elite Init", content)
    print("Done!")

if __name__ == '__main__':
    run()
