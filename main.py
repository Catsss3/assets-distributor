import requests, re, os

print("🔄 Загрузка основного движка AvenCores...")
base_url = "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/main/main.py"
code = requests.get(base_url).text

# 1. Вживляем SNI-фикс Пятерочки
sni_fix = """
def apply_sni_fix(link):
    white_sni = "ads.x5.ru"
    if any(p in link for p in ["vless://", "vmess://", "trojan://"]):
        if "sni=" in link: link = re.sub(r"sni=[^&?#]+", f"sni={white_sni}", link)
        else: link += f"{'&' if '?' in link else '?' }sni={white_sni}&fp=chrome"
    return link
"""
code = re.sub(r"(import .*?\n)", r"\1" + sni_fix + "\n", code, count=1)
code = code.replace("all_proxies.append(line)", "all_proxies.append(apply_sni_fix(line.strip()))")

# 2. Вставляем твои ссылки
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

# 3. Сохраняем и запускаем
with open("engine.py", "w", encoding="utf-8") as f:
    f.write(code)

print("🚀 Движок собран. Запуск...")
os.system("python3 engine.py")
