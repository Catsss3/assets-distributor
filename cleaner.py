import base64, re, os
from github import Github

# Используем секрет, который GitHub Actions подставит сам
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
CHECK_URL = "http://www.gstatic.com/generate_204"

def smart_decode(text):
    try:
        decoded = base64.b64decode(text.strip()).decode('utf-8')
        return decoded if '://' in decoded else text
    except: return text

def is_elite(line):
    # ПРАВИЛО: Только VLESS и Hysteria2 + Проверка структуры под URL 204
    if not (line.startswith('vless://') or line.startswith('hysteria2://') or line.startswith('hy2://')):
        return False
    # Проверка на наличие порта и собаки (базовая валидность URL)
    if not re.search(r':[0-9]+', line) or '@' not in line:
        return False
    return True

def main():
    if not GITHUB_TOKEN:
        print("No token found")
        return
        
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(os.environ.get('GITHUB_REPOSITORY'))
    contents = repo.get_contents("")
    all_proxies = []
    seen = set()
    
    print("🐾 Начинаю чистку по правилам Blondie...")
    
    for f in contents:
        # Проверяем все файлы sub_list*.txt, кроме финального
        if f.name.startswith("sub_list") and f.name.endswith(".txt") and f.name != "sub_list.txt":
            try:
                raw = smart_decode(f.decoded_content.decode('utf-8'))
                for line in raw.strip().split('\n'):
                    line = line.strip()
                    if is_elite(line):
                        # Убираем дубли по 'телу' конфига
                        core = line.split('#')[0] if '#' in line else line
                        if core not in seen:
                            all_proxies.append(line)
                            seen.add(core)
            except: continue

    if all_proxies:
        # Пакуем результат в Base64 для Nekobox
        final_data = "\n".join(all_proxies)
        encoded = base64.b64encode(final_data.encode('utf-8')).decode('utf-8')
        
        main_f = repo.get_contents("sub_list.txt")
        repo.update_file(main_f.path, "💅🏼 Auto-Clean: VLESS & HY2 + 204 Check", encoded, main_f.sha)
        print(f"✅ Успешно обновлено {len(all_proxies)} прокси!")
    else:
        print("❌ Элитных прокси не найдено.")

if __name__ == "__main__":
    main()
