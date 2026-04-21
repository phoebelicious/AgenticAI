import streamlit as st
import requests

# Set page configuration
st.set_page_config(page_title="My AI Movie Agent", page_icon="🎬")
st.title("🎬 Phoebe's AI Movie Recommender")

# User input section
user_prefs = st.text_area("What kind of movies are you in the mood for?", 
                         placeholder="e.g., I love mind-bending sci-fi with a touch of drama.")

# Mock watch history (you can enhance this to allow user selection later)
history = [{"tmdb_id": 24428, "name": "The Avengers"}]

if st.button("Get Recommendation"):
    if user_prefs:
        with st.spinner("Agent is thinking..."):
            # Call your live API endpoint deployed on Leapcell
            api_url = "https://gentic-ihuicho7164-0f9p4zeg.leapcell.dev/recommend"
            payload = {
                "user_id": 777,
                "preferences": user_prefs,
                "history": history
            }
            
            try:
                # Send the POST request to the backend agent
                response = requests.post(api_url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("✨ Your Agent Recommends:")
                    st.subheader(f"Movie ID: {data['tmdb_id']}")
                    st.write(data['description'])
                else:
                    st.error("Something went wrong with the Agent. Please check your Leapcell logs.")
            except Exception as e:
                st.error(f"Error connecting to the API: {e}")
    else:
        st.warning("Please enter your preferences first!")
