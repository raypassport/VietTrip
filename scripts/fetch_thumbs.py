import io, re, json, hashlib, os, urllib.request, urllib.parse
UA={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1"}
import time
def get(u):
    for n in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=12) as r: return r.geturl(), r.read()
        except Exception:
            if n==2: raise
            time.sleep(3)
def thumb_of(full):
    try:
        t=thumb_of(full)
        if t: return t
    except Exception: pass
    _,h=get(full); h=h.decode("utf-8","ignore")
    m=re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',h) or re.search(r'"(?:cover|originCover|imageURL)"\s*:\s*\{?[^}]*?"(?:urlList"\s*:\s*\[\s*)?"(https:[^"]+)"',h)
    return m.group(1).replace("\\u002F","/").replace("&amp;","&") if m else None
html=open("index.html",encoding="utf-8").read()
urls=sorted(set(re.findall(r'"(https://(?:vt|vm|www)\.tiktok\.com/[^"]+)"',html)))
maps=sorted(set(re.findall(r'"(https://maps\.app\.goo\.gl/[^"]+)"',html)))
for q in set(re.findall(r'M\("([^"]+)"\)',html)): maps.append("https://www.google.com/maps/search/?api=1&query="+q)
maps+=[u for u in set(re.findall(r'"(https://www\.google\.com/maps/search/\?api=1&query=[^"]+)"',html)) if u not in maps]
def qname(u):
    if "query=" not in u: return None
    q=urllib.parse.unquote_plus(u.split("query=",1)[1].split("&")[0])
    if re.match(r"^\d",q): return None   # street address (e.g. the house) -> keep icon
    return re.sub(r"\b(Ho Chi Minh|Saigon)\b","",q).strip()
def wiki_thumb(q):
    api="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","generator":"search","gsrsearch":q+" filetype:bitmap","gsrnamespace":6,"gsrlimit":1,"prop":"imageinfo","iiprop":"url","iiurlwidth":400,"format":"json"})
    _,b=get(api);pages=json.loads(b).get("query",{}).get("pages",{})
    for pg in pages.values():
        ii=pg.get("imageinfo",[{}])[0]; return ii.get("thumburl") or ii.get("url")
def openverse_thumb(q):
    _,b=get("https://api.openverse.org/v1/images/?"+urllib.parse.urlencode({"q":q,"page_size":1}))
    r=json.loads(b).get("results",[]); return (r[0].get("thumbnail") or r[0].get("url")) if r else None
def map_thumb(u):
    _,h=get(u); h=h.decode("utf-8","ignore")
    m=re.search(r'(https://lh[0-9]\.googleusercontent\.com/(?:p|gps-cs-s|geougc-cs)/[A-Za-z0-9_\-]+)',h) or re.search(r'<meta[^>]+(?:property|itemprop)="(?:og:)?image"[^>]+content="([^"]+)"',h)
    if not m: return None
    t=m.group(1).replace("&amp;","&")
    if "googleusercontent" in t: t=re.sub(r"=[^/]*$","",t)+"=w400-h300-k-no"
    if "staticmap" in t or "maps/api" in t: return None
    return t
os.makedirs("thumbs",exist_ok=True)
old={} if os.environ.get("FORCE") else json.load(open("thumbs/map.json")) if os.path.exists("thumbs/map.json") else {}
out={}; log=[]
for u in urls:
    try:
        full=u
        if "/video/" not in u and "/photo/" not in u:
            full,_=get(u); full=full.split("?")[0]
        t=thumb_of(full)
        if not t: raise Exception("no thumbnail")
        _,img=get(t)
        fn="thumbs/"+hashlib.md5(u.encode()).hexdigest()[:10]+".jpg"
        from PIL import Image
        im=Image.open(io.BytesIO(img)).convert("RGB"); im.thumbnail((240,240)); im.save(fn,"JPEG",quality=72,optimize=True); out[u]=fn; log.append(f"OK   {u} -> {full}")
    except Exception as e:
        if u in old and os.path.exists(old[u]): out[u]=old[u]
        log.append(f"FAIL {u}: {e}")
for u in maps:
    try:
        t=None;src=""
        for name,fn in (("google",lambda:map_thumb(u)),("wikimedia",lambda:wiki_thumb(qname(u)) if qname(u) else None),("openverse",lambda:openverse_thumb(qname(u)) if qname(u) else None)):
            try: t=fn()
            except Exception: t=None
            if t: src=name;break
        if not t: raise Exception("no photo")
        _,img=get(t)
        from PIL import Image
        im=Image.open(io.BytesIO(img)).convert("RGB"); im.thumbnail((240,240))
        fn="thumbs/m"+hashlib.md5(u.encode()).hexdigest()[:10]+".jpg"; im.save(fn,"JPEG",quality=72,optimize=True)
        out[u]=fn; log.append(f"OK   {src:9} {u}")
    except Exception as e:
        if u in old and os.path.exists(old[u]): out[u]=old[u]
        log.append(f"FAIL {u}: {e}")
json.dump(out,open("thumbs/map.json","w"),indent=1)
print("\n".join(log)); print(f"{len(out)}/{len(urls)} thumbnails")
