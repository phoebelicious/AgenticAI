import os
import json
import pandas as pd
import requests

def call_ollama(prompt: str, model: str = "gemma4:31b-cloud") -> str:
    # (Existing implementation of call_ollama remains the same)
    api_key = os.environ.get("OLLAMA_API_KEY")
    # ... rest of the function ...
    return response.json().get("response", "")

def get_recommendation(preferences: str, history_ids: list[int] = [], history_titles: list[str] = []) -> dict:
    # Load dataset
    df = pd.read_csv('tmdb_top_1000_movies.csv')
    
    # Exclude watched movies by ID
    available_movies = df[~df['id'].isin(history_ids)]
    
    # 2. Exclude watched movies by matching TITLES (new!)
    if history_titles:
        # Normalize titles for matching (lowercase and strip spaces)
        history_titles_norm = [t.lower().strip() for t in history_titles if t]
        available_movies = available_movies[~available_movies['title'].str.lower().str.strip().isin(history_titles_norm)]

    # Sample movies for context
    sample_movies = available_movies.sample(min(15, len(available_movies))).to_json(orient='records')

    # 3. Enhance Prompt (new!)
    prompt = f"""
        You are an expert AI Movie Recommender Agent. 
        User Mood/Preferences: "{preferences}"
        Watched Movies (by title): {history_titles}

        Based on these preferences, select the single best movie from this subset of the top 1000 movies:
        {sample_movies}

        **Constraints:**
        1. Select a movie that is MOST relevant to the user's mood and does NOT appear in their watched list.
        2. Respond ONLY with a plain JSON object. No markdown, no extra text.

        **Expected JSON Output Format:**
        {{
            "tmdb_id": <integer, the 'id' field>,
            "movie_name": "<string, the 'title' field>",
            "year": <integer, the 'year' field>,
            "description": "<string, convincing recommendation reason under 400 characters>"
        }}
    """

    raw_response = call_ollama(prompt)
    
    # 4. Enhanced JSON Parsing with more fields (new!)
    try:
        clean_json = raw_response.strip()
        # Handle markdown blocks if any
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
        if clean_json.lower().startswith("json"):
            clean_json = clean_json[4:].strip()

        rec = json.loads(clean_json)
        
        return {
            "tmdb_id": int(rec["tmdb_id"]),
            "movie_name": str(rec["movie_name"]), # new!
            "year": int(rec["year"]),             # new!
            "description": str(rec["description"])[:500]
        }
    except Exception as e:
        # Emergency fallback if LLM parsing fails
        # Ensure ID 157336 (Interstellar) is correct in CSV
        return {
            "tmdb_id": 157336, 
            "movie_name": "Interstellar", # new!
            "year": 2014,                  # new!
            "description": "Based on your taste, we highly recommend this cosmic masterpiece for your next watch."
        }
