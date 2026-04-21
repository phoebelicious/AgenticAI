from fastapi import FastAPI
from pydantic import BaseModel
from llm import get_recommendation

app = FastAPI()

class MovieHistory(BaseModel):
    tmdb_id: int
    name: str

class RecommendRequest(BaseModel):
    user_id: int
    preferences: str
    history: list[MovieHistory]

@app.post("/recommend")
async def recommend(request: RecommendRequest):
    history_titles = [m.name for m in request.history]
    history_ids = [m.tmdb_id for m in request.history]
    
    result = get_recommendation(
        preferences=request.preferences, 
        history=history_titles, 
        history_ids=history_ids
    )
    
    return {
        "tmdb_id": result["tmdb_id"],
        "user_id": request.user_id,
        "description": result["description"]
    }
