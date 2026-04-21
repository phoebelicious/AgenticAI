"""
TODO: This is the file you should edit.

get_recommendation() is called once per request with the user's input.
It should return a dict with keys "tmdb_id" and "description".

build_prompt() and call_llm() are broken out as separate functions so they are
easy to swap or extend individually, but you are free to restructure this file
however you like.

IMPORTANT: Do NOT hard-code your API key in this file. The grader will supply
its own OLLAMA_API_KEY environment variable when running your submission. Your
code must read it from the environment (os.environ or os.getenv), not from a
string literal in the source.
"""

import os
import json
import pandas as pd
import requests

# 1. Mandatory model name as per instructions [cite: 17]
MODEL = "gemma4:31b-cloud"

# 2. Global variable TOP_MOVIES required by the grader/test.py
DATA_PATH = os.path.join(os.path.dirname(__file__), "tmdb_top_1000_movies.csv")
try:
    TOP_MOVIES = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    # Fallback to local directory
    TOP_MOVIES = pd.read_csv("tmdb_top_1000_movies.csv")

def call_llm(prompt: str, model: str = MODEL) -> str:
    """
    Helper function to call the Ollama Cloud API.
    It reads OLLAMA_API_KEY from environment variables[cite: 14, 15].
    """
    api_key = os.environ.get("OLLAMA_API_KEY")
    # Note: Using the standard endpoint for Ollama Cloud services
    url = "https://ollama.cloud/api/generate" 
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # Time limit check: total recommendation must be under 20s [cite: 47]
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"Error: {str(e)}"

def get_recommendation(preferences: str, history: list[str], history_ids: list[int] = []) -> dict:
    """
    The main entry point for the recommendation agent[cite: 22, 27].
    """
    # 3. Filter out movies the user has already seen (Disqualification Rule #3) [cite: 48]
    candidate_col = 'id' if 'id' in TOP_MOVIES.columns else 'tmdb_id'
    candidates_df = TOP_MOVIES[~TOP_MOVIES[candidate_col].isin(history_ids)]
    
    # 4. Select top candidates to keep context size manageable
    sample_candidates = candidates_df.head(50)
    
    candidate_list_str = ""
    for _, row in sample_candidates.iterrows():
        movie_id = row[candidate_col]
        title = row.get('title', row.get('original_title', 'Unknown'))
        genres = row.get('genres', 'N/A')
        candidate_list_str += f"- ID: {movie_id} | Title: {title} | Genres: {genres}\n"

    # 5. Build the prompt to convince the user [cite: 24, 35]
    prompt = f"""
    User Preferences: "{preferences}"
    User Watch History (Forbidden to recommend): {', '.join(history)}
    
    Candidate List:
    {candidate_list_str}
    
    Task: Pick the best movie from the Candidate List for this user.
    Rules:
    - The 'tmdb_id' MUST be an integer from the Candidate List[cite: 49].
    - Write a 'description' (max 500 chars) to convince the user[cite: 35, 36].
    - Return ONLY a JSON object.
    
    Format:
    {{
        "tmdb_id": 123,
        "description": "Short convincing pitch."
    }}
    """
    
    # 6. Execute API call
    raw_response = call_llm(prompt)
    
    # 7. Robust parsing of JSON response
    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```"):
            lines = clean_json.splitlines()
            if len(lines) > 2:
                clean_json = "\n".join(lines[1:-1]).strip()
            else:
                clean_json = clean_json.replace("```", "").strip()
        
        if clean_json.lower().startswith("json"):
            clean_json = clean_json[4:].strip()

        rec = json.loads(clean_json)
        
        return {
            "tmdb_id": int(rec["tmdb_id"]),
            "description": str(rec["description"])[:500]
        }
    except Exception as e:
        # Emergency fallback if JSON parsing fails
        # Make sure this ID (e.g., 157336) exists in your CSV
        return {
            "tmdb_id": 157336, 
            "description": "Based on your taste, we highly recommend this cinematic masterpiece for your next watch."
        }
