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

@app.get("/api/autocomplete")
async def autocomplete(q: str):
    if len(q.strip()) < 1:
        return []
    results = await youtube_service.search_videos(q)
    return results

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
