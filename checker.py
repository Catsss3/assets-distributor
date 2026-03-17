import os, json, subprocess, time, socket, logging, concurrent.futures, uuid
from urllib.parse import urlparse, parse_qs
from typing import List, Optional, Dict

TEST_URL = "http://cp.cloudflare.com/"
TIMEOUT, THREADS, XRAY_PATH = 5, 250, "./xray"
logging.basicConfig(level=logging.INFO, format="%(message)s")

def is_port_open(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except: return False

def wait_for_port(port: int, timeout: float = 3.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if is_port_open(port): return True
        time.sleep(0.1)
    return False

def parse_link(link: str) -> Optional[Dict]:
    try:
        u = urlparse(link); qs = parse_qs(u.query)
        d = {"proto": u.scheme, "id": u.username, "addr": u.hostname, "port": int(u.port or 443),
             "sni": qs.get("sni", [""])[0], "net": qs.get("type", ["tcp"])[0], 
             "sec": qs.get("security", ["none"])[0], "fp": qs.get("fp", ["chrome"])[0]}
        
        pwd = u.password if u.password else qs.get("pass", [qs.get("password", [""])[0]])[0]
        
        if u.scheme == "vless":
            d.update({"pbk": qs.get("pbk", [""])[0], "sid": qs.get("sid", [""])[0], "flow": qs.get("flow", [""])[0]})
        elif u.scheme in ["tuic", "hy2", "hysteria2"]:
            # Для этих протоколов ID и пароль критичны
            d.update({"pass": pwd, "alpn": qs.get("alpn", ["h3"])[0]})
        return d
    except: return None

def test_worker(link: str, task_id: int) -> Optional[str]:
    data = parse_link(link)
    if not data: return None
    l_port = 11000 + (task_id % 15000)
    
    # ФОРМИРУЕМ CONFIG ПОД ПРОТОКОЛ
    outbound = {"protocol": data["proto"], "settings": {}}
    
    if data["proto"] == "vless":
        outbound["settings"] = {"vnext": [{"address": data["addr"], "port": data["port"], "users": [{"id": data["id"], "encryption": "none", "flow": data["flow"]}]}]}
        outbound["streamSettings"] = {
            "network": data["net"], "security": data["sec"],
            "tlsSettings": {"serverName": data["sni"], "fingerprint": data["fp"]} if data["sec"] == "tls" else {},
            "realitySettings": {"serverName": data["sni"], "fingerprint": data["fp"], "publicKey": data["pbk"], "shortId": data["sid"]} if data["sec"] == "reality" else {}
        }
    elif data["proto"] in ["hy2", "hysteria2"]:
        outbound["protocol"] = "hysteria2" # В Xray это hysteria2
        outbound["settings"] = {"servers": [{"address": data["addr"], "port": data["port"], "password": data["pass"]}]}
        outbound["streamSettings"] = {"network": "udp", "security": "tls", "tlsSettings": {"serverName": data["sni"], "alpn": [data["alpn"]]}}
    elif data["proto"] == "tuic":
        outbound["settings"] = {"servers": [{"address": data["addr"], "port": data["port"], "uuid": data["id"], "password": data["pass"]}]}
        outbound["streamSettings"] = {"network": "udp", "security": "tls", "tlsSettings": {"serverName": data["sni"], "alpn": [data["alpn"]]}}
    else:
        return None # Остальные пока мимо

    config = {"log": {"loglevel": "none"}, "inbounds": [{"port": l_port, "protocol": "socks", "settings": {"udp": True}}], "outbounds": [outbound]}
    cfg_name = f"cfg_{uuid.uuid4().hex[:8]}.json"
    proc = None
    try:
        with open(cfg_name, "w") as f: json.dump(config, f)
        proc = subprocess.Popen([XRAY_PATH, "-c", cfg_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not wait_for_port(l_port): return None
        
        # Тестим через curl
        res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--proxy", f"socks5://127.0.0.1:{l_port}", TEST_URL, "--max-time", "5"], capture_output=True, text=True, timeout=8)
        if res.stdout.strip() in {"200", "204"}:
            return link
    except: pass
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(timeout=1); 
            except: proc.kill()
        if os.path.exists(cfg_name): os.remove(cfg_name)
    return None

def main():
    if not os.path.exists("distributor.txt"): return
    with open("distributor.txt", "r") as f: 
        proxies = list({ln.strip() for ln in f if ln.strip()})
    
    total = len(proxies)
    logging.info(f"🚀 STELLA TITAN: Checking {total} nodes (VLESS/HY2/TUIC)...")
    valid = []
    count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as ex:
        futs = [ex.submit(test_worker, proxies[i], i) for i in range(total)]
        for fu in concurrent.futures.as_completed(futs):
            count += 1
            r = fu.result()
            if r: valid.append(r)
            if count % 1000 == 0:
                logging.info(f"⏳ Checked: {count}/{total} | Alive: {len(valid)}")
            
    with open("distributor.txt", "w") as f: 
        f.write("\n".join(valid))
    logging.info(f"💎 Result: {len(valid)} nodes (All Protocols) are ALIVE.")

if __name__ == "__main__":
    main()