from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import youtube_service

app = FastAPI(title="YouTube Wiki Race — by Ugax")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin")
async def read_admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

class LoginRequest(BaseModel):
    password: str

@app.post("/api/admin/login")
async def admin_login(req: LoginRequest):
    if req.password == "311009":
        return {"token": "admin_ok_311009"}
    raise HTTPException(status_code=401, detail="Invalid password")

class DailyChallengeRequest(BaseModel):
    start_id: str
    target_id: str

@app.post("/api/admin/daily")
async def set_daily(req: DailyChallengeRequest, request: Request):
    auth = request.headers.get("Authorization")
    if not auth or auth != "Bearer admin_ok_311009":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    success = await youtube_service.set_daily_challenge(req.start_id, req.target_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save to KV")
    return {"status": "ok"}

@app.get("/api/daily")
async def get_daily():
    data = await youtube_service.get_daily_challenge()
    if not data:
        raise HTTPException(status_code=404, detail="No daily challenge set")
    return data

@app.get("/api/autocomplete")
async def autocomplete(q: str):
    if len(q.strip()) < 1:
        return []
    results = await youtube_service.search_videos(q)
    return results

@app.get("/api/video")
async def get_video_info(id: str):
    info = await youtube_service.get_video_info(id)
    if not info:
        raise HTTPException(status_code=404, detail="Video not found")
    return info

@app.get("/api/random")
async def get_random():
    for _ in range(3):  # retry up to 3 times
        start = await youtube_service.get_random_video()
        target = await youtube_service.get_random_video()
        if start and target and start["id"] != target["id"]:
            return {"start": start, "target": target}
    raise HTTPException(status_code=503, detail="No se pudo obtener videos aleatorios")

class RecommendationRequest(BaseModel):
    id: str
    title: str
    channel: str
    visited_ids: Optional[List[str]] = []

@app.post("/api/recommendations")
async def get_recommendations(req: RecommendationRequest):
    """Devuelve las recomendaciones reales de YouTube, filtrando las ya visitadas"""
    recommended = await youtube_service.get_recommended_videos(req.id, req.title, req.channel)
    
    # Filtrar videos ya visitados para evitar bucles
    visited = set(req.visited_ids or [])
    filtered = [v for v in recommended if v["id"] not in visited]
    
    return {"recommendations": filtered}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
