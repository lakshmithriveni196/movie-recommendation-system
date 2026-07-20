import streamlit as st
import pandas as pd
import difflib
import os
import base64
import uuid
from datetime import datetime
import plotly.express as px

# ================= BACKGROUND IMAGE =================
def get_base64_of_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_base64 = get_base64_of_image("background.jpg")

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_base64}");
        background-size: cover;
        background-attachment: fixed;
    }}
    .block-container {{
        background-color: rgba(255,255,255,0.90);
        padding: 2rem;
        border-radius: 15px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ================= LOAD DATA =================
movies_data = pd.read_csv("Movies.csv")

st.title("🎬 Movie Recommendation System")

# ================= METRICS =================
col1, col2, col3 = st.columns(3)
col1.metric("🎥 Total Movies", len(movies_data))
col2.metric("🎭 Unique Genres", movies_data['genre'].nunique())
col3.metric("🎬 Unique Directors", movies_data['director'].nunique())

st.divider()

# ================= USER PROFILE =================
st.subheader("👤 User Profile")
username = st.text_input("Enter your name")

# ================= SMART SEARCH =================
st.subheader("🔍 Smart Movie Search")
search_movie = st.text_input("Type a movie name")

if search_movie:
    matches = difflib.get_close_matches(search_movie, movies_data['title'], n=10)
    result = movies_data[movies_data['title'].isin(matches)]
    st.dataframe(result[['title','genre','director','vote_avg']])

# ================= GENRE CHART =================
st.subheader("📊 Genre Distribution")
genre_count = movies_data['genre'].value_counts().head(10)
fig = px.bar(genre_count, title="Top Genres", labels={"value":"Count","index":"Genre"})
st.plotly_chart(fig, width='stretch')

# ================= FAVORITES SYSTEM =================
FAV_FILE = "favorites.csv"
if not os.path.exists(FAV_FILE):
    pd.DataFrame(columns=["id","user","movie","genre","time"]).to_csv(FAV_FILE, index=False)

fav_df = pd.read_csv(FAV_FILE)

st.subheader("❤️ Add to Favorites")
fav_movie = st.selectbox("Select a movie", movies_data['title'].unique())

if st.button("Add Favorite"):
    if username.strip() == "":
        st.warning("Enter your name first")
    else:
        genre = movies_data[movies_data['title'] == fav_movie]['genre'].iloc[0]
        fav_df = pd.concat([fav_df, pd.DataFrame([{
            "id": str(uuid.uuid4()),
            "user": username,
            "movie": fav_movie,
            "genre": genre,
            "time": datetime.now()
        }])])
        fav_df.to_csv(FAV_FILE, index=False)
        st.success("❤️ Added to favorites")

# ================= VIEW FAVORITES =================
st.subheader("📌 My Favorite Movies")
if username.strip() != "":
    user_fav = fav_df[fav_df['user'] == username]
    if user_fav.empty:
        st.info("No favorites yet")
    else:
        st.dataframe(user_fav[['movie','genre','time']])

        remove_movie = st.selectbox("Remove favorite", user_fav['movie'].unique())
        if st.button("Remove"):
            fav_df = fav_df[~((fav_df['user'] == username) & (fav_df['movie'] == remove_movie))]
            fav_df.to_csv(FAV_FILE, index=False)
            st.success("❌ Removed from favorites")

# ================= FILTER OPTIONS =================
director_list = sorted(movies_data['director'].dropna().unique())
title_list = sorted(movies_data['title'].dropna().unique())

cast_list = sorted(
    set(c.strip() for casts in movies_data['cast'].dropna() for c in casts.split(','))
)

def get_close_matches(text, column, n=5):
    return difflib.get_close_matches(text, column, n=n)

choice = st.radio("Do you know what you are looking for?", ["Nothing","Yes"])

if choice == "Nothing":
    st.subheader("🔥 Top 15 Popular Movies")
    st.dataframe(movies_data.sort_values("popularity", ascending=False)[
        ['title','genre','popularity']
    ].head(15))
else:
    option = st.selectbox("Filter by", ["Rating","Popularity","Runtime","Genre","Title","Cast","Director"])

    if option == "Rating":
        movies_data['vote_avg'] = pd.to_numeric(movies_data['vote_avg'], errors='coerce')
        st.subheader("Top 5 Movies by Rating")
        st.dataframe(movies_data.sort_values('vote_avg', ascending=False)[['title', 'vote_avg']].head(10))
    elif option == "Popularity":
        movies_data['popularity'] = pd.to_numeric(movies_data['popularity'], errors='coerce')
        st.subheader("Top 5 Popular Movies")
        st.dataframe(movies_data.sort_values('popularity', ascending=False)[['title', 'popularity']].head(10))
    elif option == "Runtime":
        runtime = st.number_input("Enter runtime (minutes)", min_value=0)
        preference = st.selectbox("Preference", ["Greater", "Equal"])

        movies_data['runtime'] = pd.to_numeric(movies_data['runtime'], errors='coerce')

        if preference == "Greater":
            result = movies_data[movies_data['runtime'] > runtime]
        else:
            result = movies_data[movies_data['runtime'] == runtime]

        st.dataframe(result[['title', 'runtime']].head(10))
    elif option == "Genre":
        g = st.text_input("Genre")
        if g:
            matches = get_close_matches(g, movies_data['genre'])
            st.dataframe(movies_data[movies_data['genre'].isin(matches)][['title','genre']])
    elif option == "Title":
        t = st.selectbox("Title", title_list)
        st.dataframe(movies_data[movies_data['title'] == t])
    elif option == "Cast":
        c = st.selectbox("Cast", cast_list)
        st.dataframe(movies_data[movies_data['cast'].str.contains(c, case=False)][['title','cast']])
    elif option == "Director":
        d = st.selectbox("Director", director_list)
        st.dataframe(movies_data[movies_data['director'].str.contains(d, case=False)][['title','director']])

# ================= REVIEWS SYSTEM =================
st.subheader("⭐ Add Review")

REV_FILE = "reviews.csv"
if not os.path.exists(REV_FILE):
    pd.DataFrame(columns=["movie","user","rating","review","time"]).to_csv(REV_FILE, index=False)

reviews_df = pd.read_csv(REV_FILE)

movie = st.text_input("Movie Name")
rating = st.slider("Rating",1,5)
review = st.text_area("Review")

if st.button("Submit Review"):
    reviews_df = pd.concat([reviews_df, pd.DataFrame([{
        "movie": movie,
        "user": username,
        "rating": rating,
        "review": review,
        "time": datetime.now()
    }])])
    reviews_df.to_csv(REV_FILE, index=False)
    st.success("✅ Review submitted")

st.subheader("📢 All Reviews")
st.dataframe(reviews_df)
