from fastapi import FastAPI
from pydantic import BaseModel
from llm import get_recommendation
from typing import List, Optional

app = FastAPI()

# Data model for incoming request
class RecommendRequest(BaseModel):
    user_id: int
    preferences: str
    # accepting a list of strings for watched movie titles
    watched_movie_titles: Optional[List[str]] = []

@app.post("/recommend")
async def recommend(request: RecommendRequest):
    # Pass preferences and watched titles to llm.py
    result = get_recommendation(
        preferences=request.preferences,
        history_titles=request.watched_movie_titles
    )
    
    return {
        "tmdb_id": result["tmdb_id"],
        "user_id": request.user_id,
        "movie_name": result["movie_name"], # new field from llm.py
        "year": result["year"],             # new field from llm.py
        "description": result["description"]
    }
