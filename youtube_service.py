import os
import json
import random
import urllib.request
from dotenv import load_dotenv
from youtubesearchpython import VideosSearch

load_dotenv()

API_KEY = os.environ.get("YOUTUBE_API_KEY")

if not API_KEY:
    print("ADVERTENCIA: No se encontró YOUTUBE_API_KEY en .env")

# Almacenamos visitorData para mantener sesión con YouTube
_visitor_data = None


def _innertube_next(video_id: str):
    """
    Llama al endpoint InnerTube /next para obtener las recomendaciones
    REALES que YouTube muestra en la barra lateral derecha.
    NO consume cuota de la API oficial.
    """
    global _visitor_data
    
    context = {
        "client": {
            "clientName": "WEB",
            "clientVersion": "2.20240601.00.00",
            "hl": "es",
            "gl": "ES"
        }
    }
    
    if _visitor_data:
        context["client"]["visitorData"] = _visitor_data
    
    payload = {
        "videoId": video_id,
        "context": context
    }
    
    url = f"https://www.youtube.com/youtubei/v1/next?key={API_KEY}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    })
    
    res = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
    jdata = json.loads(res)
    
    vd = jdata.get("responseContext", {}).get("visitorData")
    if vd:
        _visitor_data = vd
    
    return jdata


def _parse_recommendations(data: dict, current_video_id: str):
    """
    Extrae los videos de la barra lateral del response de InnerTube /next.
    Soporta lockupViewModel (nuevo) y compactVideoRenderer (viejo).
    """
    videos = []
    seen_ids = {current_video_id}
    
    try:
        secondary = (
            data.get("contents", {})
            .get("twoColumnWatchNextResults", {})
            .get("secondaryResults", {})
            .get("secondaryResults", {})
            .get("results", [])
        )
        
        for item in secondary:
            # Formato nuevo: lockupViewModel
            lvm = item.get("lockupViewModel")
            if lvm:
                vid = lvm.get("contentId")
                if not vid or vid in seen_ids:
                    continue
                seen_ids.add(vid)
                
                meta = lvm.get("metadata", {}).get("lockupMetadataViewModel", {})
                title = meta.get("title", {}).get("content", "")
                
                channel = ""
                date = ""
                rows = (meta.get("metadata", {})
                           .get("contentMetadataViewModel", {})
                           .get("metadataRows", []))
                if rows:
                    parts = rows[0].get("metadataParts", [])
                    if parts:
                        channel = parts[0].get("text", {}).get("content", "")
                        if len(parts) > 1:
                            date = parts[1].get("text", {}).get("content", "")
                
                thumb = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                ti = (lvm.get("contentImage", {})
                         .get("thumbnailViewModel", {})
                         .get("image", {})
                         .get("sources", []))
                if ti:
                    thumb = ti[-1].get("url", thumb)
                
                if title:
                    videos.append({
                        "id": vid,
                        "title": title,
                        "channel": channel,
                        "thumb": thumb,
                        "date": date
                    })
                continue
            
            # Formato viejo: compactVideoRenderer
            cvr = item.get("compactVideoRenderer")
            if cvr:
                vid = cvr.get("videoId")
                if not vid or vid in seen_ids:
                    continue
                seen_ids.add(vid)
                
                title = ""
                t = cvr.get("title", {})
                if "simpleText" in t:
                    title = t["simpleText"]
                elif "runs" in t:
                    title = t["runs"][0].get("text", "")
                
                channel = ""
                c = cvr.get("longBylineText", cvr.get("shortBylineText", {}))
                if "runs" in c:
                    channel = c["runs"][0].get("text", "")
                
                date = ""
                d = cvr.get("publishedTimeText", {})
                if "simpleText" in d:
                    date = d["simpleText"]
                elif "runs" in d:
                    date = d["runs"][0].get("text", "")
                
                thumb = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                thumbs = cvr.get("thumbnail", {}).get("thumbnails", [])
                if thumbs:
                    thumb = thumbs[-1].get("url", thumb)
                
                if title:
                    videos.append({
                        "id": vid,
                        "title": title,
                        "channel": channel,
                        "thumb": thumb,
                        "date": date
                    })
    except Exception as e:
        print(f"Error parseando recomendaciones: {e}")
    
    return videos


async def get_video_info(video_id: str):
    """Obtiene info de un video por su ID (para cargar semillas desde URL)."""
    try:
        from youtubesearchpython import Video
        info = Video.getInfo(f"https://www.youtube.com/watch?v={video_id}")
        if not info:
            return None
        thumb = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        thumbnails = info.get("thumbnails", [])
        if thumbnails:
            thumb = thumbnails[-1].get("url", thumb)
        return {
            "id": video_id,
            "title": info.get("title", ""),
            "channel": info.get("channel", {}).get("name", ""),
            "thumb": thumb,
            "date": info.get("publishedTime", "")
        }
    except Exception as e:
        print(f"Error getting video info for {video_id}: {e}")
        return None


async def search_videos(query: str, limit: int = 20):
    """
    Busca videos usando youtubesearchpython (NO consume cuota de API).
    Se usa para el autocomplete y el botón aleatorio.
    """
    try:
        search = VideosSearch(query, limit=limit, language="es", region="ES")
        result = search.result()
        
        videos = []
        for item in result.get("result", []):
            thumbs = item.get("thumbnails", [])
            thumb_url = thumbs[-1]["url"] if thumbs else f"https://img.youtube.com/vi/{item['id']}/hqdefault.jpg"
            
            channel_name = item.get("channel", {}).get("name", "YouTube")
            published = item.get("publishedTime", "")
            
            videos.append({
                "id": item["id"],
                "title": item["title"],
                "channel": channel_name,
                "thumb": thumb_url,
                "date": published
            })
        return videos
    except Exception as e:
        print(f"Error en search_videos: {e}")
        return []


async def get_recommended_videos(video_id: str, title: str, channel: str):
    """
    Obtiene las recomendaciones 100% REALES de YouTube.
    Usa InnerTube /next (NO consume cuota de la API oficial).
    """
    try:
        print(f"[RECS] Pidiendo recomendaciones reales para: {video_id} - {title[:40]}")
        data = _innertube_next(video_id)
        videos = _parse_recommendations(data, video_id)
        
        print(f"[RECS] InnerTube devolvió {len(videos)} recomendaciones reales")
        
        if videos:
            # Seleccionar las primeras 3 (muy relevantes)
            top_videos = videos[:3]
            # Mezclar el resto para que haya un poco de variedad y no parezca un bucle
            rest_videos = videos[3:]
            random.shuffle(rest_videos)
            
            final_recs = top_videos + rest_videos
            return final_recs[:20]
        
        print(f"[RECS] FALLBACK: InnerTube vacío, buscando por título")
        return await search_videos(title, limit=15)
        
    except Exception as e:
        print(f"[RECS] ERROR: {e}")
        return await search_videos(title, limit=15)


async def get_random_video():
    """Devuelve un video aleatorio para el destino."""
    topics = ["gaming", "musica español", "documental español", "vlog español", 
              "tecnologia", "ciencia", "deportes", "curiosidades", "minecraft",
              "fortnite", "tendencias", "comedia", "anime"]
    videos = await search_videos(random.choice(topics), limit=10)
    return random.choice(videos) if videos else None
