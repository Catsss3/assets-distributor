import requests, re, os, random

print("🔄 Загрузка движка и применение мульти-SNI фикса...")
base_url = "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/main.py"
code = requests.get(base_url).text

# 1. Вживляем продвинутый SNI-фикс (рандомный выбор из белого списка)
sni_fix = """
def apply_sni_fix(link):
    # Список 'неприкасаемых' доменов
    white_lists = ["ads.x5.ru", "gosuslugi.ru", "vk.com", "ozon.ru", "tass.ru"]
    target_sni = random.choice(white_lists)
    
    if any(p in link for p in ["vless://", "vmess://", "trojan://"]):
        if "sni=" in link: 
            link = re.sub(r"sni=[^&?#]+", f"sni={target_sni}", link)
        else:
            sep = "&" if "?" in link else "?"
            link += f"{sep}sni={target_sni}&fp=chrome"
    return link
"""

# Вставляем импорт random и саму функцию
code = "import random\n" + code
code = re.sub(r"(import .*?\n)", r"\1" + sni_fix + "\n", code, count=1)
code = code.replace("all_proxies.append(line)", "all_proxies.append(apply_sni_fix(line.strip()))")

# 2. Твои ссылки (без изменений)
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
urls_str = "EXTRA_URLS_FOR_26 = " + str(my_urls)
code = re.sub(r"EXTRA_URLS_FOR_26\s*=\s*\[.*?\]", urls_str, code, flags=re.DOTALL)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(code)

print("🚀 Движок с Мульти-SNI собран. Поехали!")
os.system("python3 engine.py")
