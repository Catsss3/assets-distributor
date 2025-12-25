
import os, base64, requests, socket, threading
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai

genai.configure(api_key="AIzaSyAU35Hh59Kx-x4Cd3F7PplJXXG9SaFJNCM")
model = genai.GenerativeModel('gemini-1.5-flash')
valid_configs = []
lock = threading.Lock()

def check_server(config):
    try:
        if not config.startswith(('vless://', 'hysteria2://')): return
        addr = config.split('@')[1].split('?')[0].split('#')[0]
        host, port = addr.split(':')
        with socket.create_connection((host, int(port)), timeout=2):
            with lock:
                if config not in valid_configs: valid_configs.append(config)
    except: pass

def main():
    # Gemini ищет ДОПОЛНИТЕЛЬНЫЕ источники
    try:
        prompt = "Provide 5 new RAW direct URLs for vless/hysteria2 configs. Only URLs."
        resp = model.generate_content(prompt)
        new_urls = [u for u in resp.text.split() if u.startswith('http')]
        with open("sources.txt", "a+") as fs:
            fs.seek(0); existing = fs.read()
            for u in new_urls:
                if u not in existing: fs.write(f"\n{u}")
    except: pass

    with open("sources.txt", "r") as fs:
        urls = [l.strip() for l in fs if l.strip() and not l.startswith("#")]
    
    all_raw = []
    for url in urls:
        try:
            r = requests.get(url, timeout=10).text
            try:
                data = base64.b64decode(r).decode('utf-8')
                all_raw.extend(data.splitlines())
            except: all_raw.extend(r.splitlines())
        except: continue

    configs = list(set([c.strip() for c in all_raw if c.startswith(('vless://', 'hysteria2://'))]))
    
    if configs:
        with ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(check_server, configs)
        
        # Удаляем старые sub*.txt перед записью
        for f in os.listdir('.'):
            if f.startswith("sub") and f.endswith(".txt"): os.remove(f)

        # Нарезка по 500 в Base64
        for i in range(0, len(valid_configs), 500):
            chunk = valid_configs[i:i+500]
            name = "sub.txt" if i == 0 else f"sub{i//500}.txt"
            with open(name, "w") as out:
                out.write(base64.b64encode("\n".join(chunk).encode()).decode())

if __name__ == "__main__":
    main()
