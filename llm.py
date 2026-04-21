import os
import json
import pandas as pd
import requests

def call_ollama(prompt: str, model: str = "gemma4:31b-cloud") -> str:
    api_key = os.environ.get("OLLAMA_API_KEY")
    
    # 🚨 This is the most critical fix! The original ollama.cloud has been replaced with your dedicated URL.
    # If your TA provided a different specific URL, replace the URL inside the quotes here.
    # Otherwise, please keep this MBAN server URL:
    url = "https://ollama-cloud.at.mban.ca/api/generate" 
    
    payload = {"model": model, "prompt": prompt, "stream": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        # Send the request with a timeout setting
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        response.raise_for_status() # Check if the server returned an error HTTP status code
        return response.json().get("response", "")
    except Exception as e:
        print(f"API Error: {e}")
        return "" # If connection fails, return an empty string to trigger the fallback movie below

def get_recommendation(preferences: str, history_ids: list[int] = [], history_titles: list[str] = []) -> dict:
    # 1. Load the dataset
    df = pd.read_csv('tmdb_top_1000_movies.csv')
    
    # 🚨 Fix the previous KeyError: 'id' issue
    if 'tmdb_id' in df.columns:
        df = df.rename(columns={'tmdb_id': 'id'})
    
    # 2. Exclude already watched movies (by ID)
    available_movies = df[~df['id'].isin(history_ids)]
    
    # 3. Exclude already watched movies (by Title)
    if history_titles:
        history_titles_norm = [t.lower().strip() for t in history_titles if t]
        available_movies = available_movies[~available_movies['title'].str.lower().str.strip().isin(history_titles_norm)]

    # 4. Sample movies for the LLM's context
    sample_movies = available_movies.sample(min(15, len(available_movies))).to_json(orient='records')

    # 5. Construct the Prompt
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

    # 6. Call the Large Language Model
    raw_response = call_ollama(prompt)
    
    # 7. Parse the returned JSON
    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
        if clean_json.lower().startswith("json"):
            clean_json = clean_json[4:].strip()

        rec = json.loads(clean_json)
        
        return {
            "tmdb_id": int(rec["tmdb_id"]),
            "movie_name": str(rec["movie_name"]),
            "year": int(rec["year"]),
            "description": str(rec["description"])[:500]
        }
    except Exception as e:
        # Fallback mechanism: If any previous step (including network disconnection) fails, always return this movie as a baseline
        return {
            "tmdb_id": 157336, 
            "movie_name": "Interstellar",
            "year": 2014,
            "description": "Based on your taste, we highly recommend this cosmic masterpiece for your next watch."
        }
