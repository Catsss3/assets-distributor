import base64, re, os, random
from github import Github

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
MAX_PROXIES = 500  # Лимит, чтобы Nekobox не ругался 🎀

def smart_decode(content_bytes):
    try:
        text = content_bytes.decode('utf-8')
        if 'vless://' not in text and 'hysteria2://' not in text and 'hy2://' not in text:
            return base64.b64decode(text.strip()).decode('utf-8')
        return text
    except:
        try: return base64.b64decode(content_bytes.strip()).decode('utf-8')
        except: return ""

def is_elite(line):
    line = line.strip()
    if not line or not any(line.startswith(p) for p in ['vless://', 'hysteria2://', 'hy2://']):
        return False
    if '@' not in line or not re.search(r':[0-9]+', line):
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
        # Перемешиваем, чтобы список был разнообразным 🎲
        random.shuffle(all_proxies)
        # Ограничиваем количество, чтобы файл был легким 🕊️
        limited_proxies = all_proxies[:MAX_PROXIES]
        
        final_data = "\n".join(limited_proxies)
        encoded = base64.b64encode(final_data.encode('utf-8')).decode('utf-8')
        main_f = repo.get_contents("sub_list.txt")
        repo.update_file(main_f.path, f"💅🏼 Lite Update: {len(limited_proxies)} Elite Proxies", encoded, main_f.sha)
        print(f"✅ Готово! Сохранила {len(limited_proxies)} лучших штук.")

if __name__ == "__main__":
    main()
