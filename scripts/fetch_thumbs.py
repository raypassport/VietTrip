import io, re, json, hashlib, os, urllib.request, urllib.parse
UA={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20) as r: return r.geturl(), r.read()
html=open("index.html",encoding="utf-8").read()
urls=sorted(set(re.findall(r'"(https://(?:vt|vm|www)\.tiktok\.com/[^"]+)"',html)))
os.makedirs("thumbs",exist_ok=True)
old={} if os.environ.get("FORCE") else json.load(open("thumbs/map.json")) if os.path.exists("thumbs/map.json") else {}
out={}; log=[]
for u in urls:
    try:
        full=u
        if "/video/" not in u and "/photo/" not in u:
            full,_=get(u); full=full.split("?")[0]
        _,b=get("https://www.tiktok.com/oembed?url="+urllib.parse.quote(full,safe=""))
        t=json.loads(b).get("thumbnail_url")
        if not t: raise Exception("no thumbnail")
        _,img=get(t)
        fn="thumbs/"+hashlib.md5(u.encode()).hexdigest()[:10]+".jpg"
        from PIL import Image
        im=Image.open(io.BytesIO(img)).convert("RGB"); im.thumbnail((240,240)); im.save(fn,"JPEG",quality=72,optimize=True); out[u]=fn; log.append(f"OK   {u} -> {full}")
    except Exception as e:
        if u in old and os.path.exists(old[u]): out[u]=old[u]
        log.append(f"FAIL {u}: {e}")
json.dump(out,open("thumbs/map.json","w"),indent=1)
print("\n".join(log)); print(f"{len(out)}/{len(urls)} thumbnails")
