import os, asyncio, aiohttp, base64, re
async def f(s, u, m):
 async with m:
  try:
   async with s.get(u, timeout=10) as r:
    if r.status==200: return (await r.text()).splitlines()
  except: return []
 return []
async def c(s, l, m):
 if not re.match(r'^(vless|vmess|trojan|ss|http|https)://', l): return None
 async with m:
  try:
   async with s.get(l, timeout=10) as r:
    if r.status in (200, 204): return l
  except: return None
async def main():
 if not os.path.exists("sources.txt"): return
 with open("sources.txt", "r") as f_in:
  urls = [l.strip() for l in f_in if l.strip().startswith("http")]
 async with aiohttp.ClientSession() as s:
  m_f = asyncio.Semaphore(50)
  p = await asyncio.gather(*[f(s, u, m_f) for u in urls])
  all_l = list(set([i for sub in p for i in sub if len(i)>10]))
  print(f"📥 Собрано: {len(all_l)}")
  m_c = asyncio.Semaphore(200)
  res = await asyncio.gather(*[c(s, l, m_c) for l in all_l])
  v = [r for r in res if r]
 v.sort(key=lambda x: 0 if x.startswith(("vless","vmess","trojan")) else 1)
 with open("distributor.txt", "w") as f1: f1.write("\n".join(v))
 with open("distributor.64", "w") as f2: f2.write(base64.b64encode("\n".join(v).encode()).decode())
 print(f"✅ Живых: {len(v)}")
if __name__ == "__main__": asyncio.run(main())
