import base64, re, os, random

# Весь код AvenCores + Твои фиксы уже здесь (внутри этой строки)
raw_data = "TOKEN_FOR_ENCODED_CODE" # Я заменю это на реальный блок ниже

def apply_sni_fix(link):
    white_lists = ["ads.x5.ru", "gosuslugi.ru", "vk.com", "ozon.ru", "tass.ru"]
    target_sni = random.choice(white_lists)
    if any(p in link for p in ["vless://", "vmess://", "trojan://"]):
        if "sni=" in link: 
            link = re.sub(r"sni=[^&?#]+", f"sni={target_sni}", link)
        else:
            sep = "&" if "?" in link else "?"
            link += f"{sep}sni={target_sni}&fp=chrome"
    return link

# Сборка движка
print("🛠 Сборка движка из локального бэкапа...")
engine_code = base64.b64decode(raw_data).decode('utf-8')

# Вставляем твои ссылки
my_urls = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/main/githubmirror/ru-sni/vless_ru.txt",
    "https://raw.githubusercontent.com/rachikop/mobile_whitelist/main/configs.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt",
    "https://raw.githubusercontent.com/LowiKLive/BypassWhitelistRu/refs/heads/main/WhiteList-Bypass_Ru.txt",
    "https://raw.githubusercontent.com/vlesscollector/vlesscollector/refs/heads/main/vless_configs.txt",
    "https://bp.wl.free.nf/confs/selected.txt"
]
engine_code = re.sub(r"EXTRA_URLS_FOR_26\s*=\s*\[.*?\]", f"EXTRA_URLS_FOR_26 = {str(my_urls)}", engine_code, flags=re.DOTALL)
engine_code = engine_code.replace("all_proxies.append(line)", "all_proxies.append(apply_sni_fix(line.strip()))")

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(engine_code)

print("🚀 Запуск полноценного движка...")
os.system("python3 engine.py")
