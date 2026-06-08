import json, urllib.request, os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.environ.get("YOUTUBE_API_KEY")

def get_recs_innertube(video_id):
    payload = {
        "videoId": video_id,
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240601.00.00",
                "hl": "es",
                "gl": "ES"
            }
        }
    }
    url = f"https://www.youtube.com/youtubei/v1/next?key={API_KEY}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    res = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
    return json.loads(res)

def parse(data, vid):
    sr = (data.get("contents", {})
              .get("twoColumnWatchNextResults", {})
              .get("secondaryResults", {})
              .get("secondaryResults", {})
              .get("results", []))
    ids = []
    for item in sr:
        lvm = item.get("lockupViewModel")
        if lvm:
            cid = lvm.get("contentId")
            if cid and cid != vid:
                ids.append(cid)
    return ids

# Hacer 3 cadenas de saltos simulando un juego real
print("=== SIMULANDO JUEGO: 3 saltos desde Rick Astley ===")
chain = "dQw4w9WgXcQ"
all_seen = set()
for hop in range(4):
    data = get_recs_innertube(chain)
    ids = parse(data, chain)
    overlap = len(set(ids) & all_seen)
    all_seen.update(ids)
    
    # Get titles for first few
    sr = data["contents"]["twoColumnWatchNextResults"]["secondaryResults"]["secondaryResults"]["results"]
    titles = []
    for item in sr[:3]:
        lvm = item.get("lockupViewModel")
        if lvm:
            t = lvm.get("metadata",{}).get("lockupMetadataViewModel",{}).get("title",{}).get("content","")
            titles.append(t[:50].encode('ascii','replace').decode())
    
    print(f"\nHop {hop}: video={chain}, recs={len(ids)}, overlap_con_anteriores={overlap}")
    for t in titles:
        print(f"  - {t}")
    
    if ids:
        chain = ids[0]  # saltar al primer recomendado
    else:
        print("  SIN RECOMENDACIONES!")
        break
