import streamlit as st
import pickle
import pandas as pd
import requests
import time

# ---------------- TMDB API Key ----------------
API_KEY = "6454dd15561c6d8c95db722e78e15766"

# ---------------- Get TMDB ID by Title ----------------
def get_tmdb_id(movie_title, retries=3, delay=2):
    """Search TMDB for a movie by title and return the first match's ID (with retries)."""
    for attempt in range(retries):
        try:
            url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_title}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data["results"]:
                return data["results"][0]["id"]  # return the first matched movie ID
            else:
                print(f"⚠️ No TMDB ID found for: {movie_title}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching TMDB ID (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
    return None

# ---------------- Fetch Poster Function ----------------
def fetch_poster(movie_id, retries=3, delay=2):
    """Fetch poster from TMDB with retry & fallback."""
    for attempt in range(retries):
        try:
            url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("poster_path"):
                return "https://image.tmdb.org/t/p/w500" + data["poster_path"]
            elif data.get("backdrop_path"):
                return "https://image.tmdb.org/t/p/w500" + data["backdrop_path"]
            else:
                return "https://via.placeholder.com/300x450.png?text=No+Poster"

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching poster for ID {movie_id} (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
    return "https://via.placeholder.com/300x450.png?text=Poster+Unavailable"

# ---------------- Recommendation Function ----------------
def refer(selected_movie):
    """Return top 5 recommended movies & posters."""
    movies_index = movies[movies['title'] == selected_movie].index[0] 
    distances = similarity[movies_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    refered_movies, refered_movies_posters = [], []

    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id   

        # ✅ Auto-fix wrong or missing IDs
        if pd.isna(movie_id) or movie_id == 0:
            movie_id = get_tmdb_id(movies.iloc[i[0]].title)
            movies.at[i[0], "movie_id"] = movie_id  # update in memory

        refered_movies.append(movies.iloc[i[0]].title)
        refered_movies_posters.append(fetch_poster(movie_id))
    
    return refered_movies, refered_movies_posters

# ---------------- Load Data ----------------
movies = pickle.load(open('movies.pkl','rb'))
similarity = pickle.load(open('similarity.pkl','rb'))
movies_list = movies['title'].values  

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="🎬 Movie Recommender", layout="wide")

st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🍿 Movie Recommender System 🎬</h1>", unsafe_allow_html=True)
st.write("Discover movies similar to your favorites! Choose a movie and get recommendations with posters.")

selected_movie_name = st.selectbox(
    '🎥 Select a movie:',
    movies_list
)

if st.button('✨ Get Recommendations'):
    with st.spinner("🔍 Finding the best matches..."):
        names, posters = refer(selected_movie_name)

    st.success("Here are your top picks! 👇")
    st.write("---")

    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.image(posters[idx], use_column_width=True)
            st.markdown(f"<p style='text-align:center; font-weight:bold;'>{names[idx]}</p>", unsafe_allow_html=True)

# ---------------- Optional: Save Updated Movies.pkl ----------------
with open("movies.pkl", "wb") as f:
    pickle.dump(movies, f)
