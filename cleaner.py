import base64, re, os, random
from github import Github

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
MAX_PROXIES = 300  # Сделаем чуть меньше для гарантии 🎀

def smart_decode(content_bytes):
    try:
        text = content_bytes.decode('utf-8')
        if '://' not in text:
            return base64.b64decode(text.strip()).decode('utf-8')
        return text
    except:
        try: return base64.b64decode(content_bytes.strip()).decode('utf-8')
        except: return ""

def is_elite(line):
    line = line.strip()
    if not line or not any(line.startswith(p) for p in ['vless://', 'hysteria2://', 'hy2://']):
        return False
    # Самая строгая проверка структуры для Nekobox
    if '@' not in line or ':' not in line.split('@')[-1]:
        return False
    return True

def main():
    if not GITHUB_TOKEN: return
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(os.environ.get('GITHUB_REPOSITORY'))
    contents = repo.get_contents("")
    all_proxies = []
    seen = set()
    
    for f in contents:
        if f.name.startswith("sub_list") and f.name.endswith(".txt") and f.name != "sub_list.txt":
            raw_text = smart_decode(f.decoded_content)
            lines = re.split(r'[\r\n]+', raw_text)
            for line in lines:
                if is_elite(line):
                    core = line.split('#')[0].strip()
                    if core not in seen:
                        all_proxies.append(line.strip())
                        seen.add(core)

    if all_proxies:
        random.shuffle(all_proxies)
        limited_proxies = all_proxies[:MAX_PROXIES]
        
        # ВАЖНО: Сохраняем как ЧИСТЫЙ ТЕКСТ, а не Base64 👄🫦
        final_data = "\n".join(limited_proxies)
        
        main_f = repo.get_contents("sub_list.txt")
        # Обновляем файл чистым текстом
        repo.update_file(main_f.path, f"💎 Plain Text Update: {len(limited_proxies)} Proxies", final_data, main_f.sha)
        print(f"✅ Готово! Сохранила {len(limited_proxies)} штук в открытом виде.")

if __name__ == "__main__":
    main()
