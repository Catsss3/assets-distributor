import os, json, subprocess, time, socket, logging, concurrent.futures, uuid
from urllib.parse import urlparse, parse_qs

def is_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5); return s.connect_ex(("127.0.0.1", port)) == 0
    except: return False

def parse_link(link):
    try:
        u = urlparse(link); qs = parse_qs(u.query)
        d = {"proto": u.scheme, "id": u.username, "addr": u.hostname, "port": int(u.port),
             "sni": qs.get("sni", [""])[0], "net": qs.get("type", ["tcp"])[0], "sec": qs.get("security", ["none"])[0]}
        if u.scheme == "vless":
            d.update({"pbk": qs.get("pbk", [""])[0], "sid": qs.get("sid", [""])[0], "flow": qs.get("flow", [""])[0], "fp": qs.get("fp", [""])[0]})
        return d
    except: return None

def test_worker(link, task_id):
    data = parse_link(link)
    if not data or data["proto"] != "vless": return None
    l_port = 10000 + (task_id % 20000)
    config = {
        "log": {"loglevel": "none"},
        "inbounds": [{"port": l_port, "protocol": "socks", "settings": {"udp": True}}],
        "outbounds": [{
            "protocol": data["proto"],
            "settings": {"vnext": [{"address": data["addr"], "port": data["port"], "users": [{"id": data["id"], "encryption": "none", "flow": data["flow"]}]}]},
            "streamSettings": {
                "network": data["net"], "security": data["sec"],
                "tlsSettings": {"serverName": data["sni"], "fingerprint": data["fp"]} if data["sec"] == "tls" else {},
                "realitySettings": {"serverName": data["sni"], "fingerprint": data["fp"], "publicKey": data["pbk"], "shortId": data["sid"]} if data["sec"] == "reality" else {}
            }
        }]
    }
    cfg_name = f"cfg_{uuid.uuid4().hex[:6]}.json"
    proc = None
    try:
        with open(cfg_name, "w") as f: json.dump(config, f)
        proc = subprocess.Popen(["./xray", "-c", cfg_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(15):
            if is_port_open(l_port): break
            time.sleep(0.1)
        else: return None
        res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--proxy", f"socks5://127.0.0.1:{l_port}", "http://cp.cloudflare.com/", "--max-time", "5"], capture_output=True, text=True, timeout=7)
        if res.stdout.strip() in {"200", "204"}: return link
    except: pass
    finally:
        if proc: proc.terminate()
        try: os.remove(cfg_name)
        except: pass
    return None

def main():
    if not os.path.exists("distributor.txt"): return
    with open("distributor.txt", "r") as f: proxies = [l.strip() for l in f if l.strip()]
    valid = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futs = [ex.submit(test_worker, proxies[i], i) for i in range(len(proxies))]
        for fu in concurrent.futures.as_completed(futs):
            r = fu.result()
            if r: valid.append(r)
    with open("distributor.txt", "w") as f: f.write("\n".join(valid))

if __name__ == "__main__": main()