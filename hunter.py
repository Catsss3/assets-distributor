import requests
import re
import os
from github import Github

def hunt():
    token = os.getenv('WORKFLOW_TOKEN')
    repo_name = "Catsss3/assets-distributor"
    channels = ["Evay_vpn", "v2rayng_org", "v2ray_free_conf", "V2Ray_VLESS_Reality", "Shadowsocks_Unit"]
    
    all_configs = []
    for channel in channels:
        try:
            res = requests.get(f"https://t.me/s/{channel}", timeout=10)
            found = re.findall(r'(?:vless|hysteria2|hy2|vmess|ss)://[^\s<"]+', res.text)
            all_configs.extend([c.replace('&amp;', '&').split('<')[0] for c in found])
        except: pass
    
    unique_configs = "\n".join(list(dict.fromkeys(all_configs)))
    if not unique_configs: return

    g = Github(token)
    repo = g.get_repo(repo_name)
    file_path = "collected_proxies.txt"
    
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, "🤖 Авто-охота: обновление базы", unique_configs, contents.sha)
    except:
        repo.create_file(file_path, "🚀 Авто-охота: создание базы", unique_configs)

if __name__ == "__main__":
    hunt()
