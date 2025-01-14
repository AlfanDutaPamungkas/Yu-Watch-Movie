import numpy as np
import pandas as pd
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import re

def clean_text(text):
    if pd.isna(text):
        return ""
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text

# Fungsi buat ekstrak name dari suatu kolom
def extract_names(params):
    if pd.isna(params):
        return ""
    if not isinstance(params, str):
        return ""
    try:
        params_list = ast.literal_eval(params)
        names = [name['name'].lower() for name in params_list if 'name' in name]
        return ' '.join(names)
    except (ValueError, SyntaxError, TypeError):
        return ""

# Fungsi buat ekstrak name dari suatu kolom
def extract_names_with_comma(params):
    if pd.isna(params):
        return ""
    if not isinstance(params, str):
        return ""
    try:
        params_list = ast.literal_eval(params)
        names = [name['name'].lower() for name in params_list if 'name' in name]
        return ', '.join(names)
    except (ValueError, SyntaxError, TypeError):
        return ""

def find_closest_match_tfidf(movie_name, movie_titles):
    combined_titles = [movie_name] + movie_titles
    
    title_vectorizer = TfidfVectorizer(stop_words="english")
    title_vectors = title_vectorizer.fit_transform(combined_titles)
    
    similarity_scores = cosine_similarity(title_vectors[0], title_vectors[1:]).flatten()
    
    closest_idx = similarity_scores.argmax()
    return movie_titles[closest_idx], similarity_scores[closest_idx]

# Muat data dari dataset
movies_data = pd.read_csv("Movie_Dataset.csv", low_memory=False)

# Isi nilai kosong
selected_features = ["genres", "keywords", "production_companies", "tagline"]
for feature in selected_features:
    movies_data[feature] = movies_data[feature].fillna("")

# Cleaning kolom original_title
movies_data["original_title"] = movies_data["original_title"].str.lower().str.strip()

# Cleaning kolom genre
movies_data["genres"] = movies_data["genres"].apply(extract_names)

# Cleaning kolom keywords
movies_data["keywords"] = movies_data["keywords"].apply(extract_names_with_comma)

# Cleaning kolom production_companies
movies_data["production_companies"] = movies_data["production_companies"].apply(extract_names_with_comma)

movies_data["tagline"] = movies_data["tagline"].apply(clean_text)

# Gabung selected features
combined_features =movies_data["original_title"] + " " + movies_data["genres"] + " " + movies_data["keywords"] + " " + movies_data["production_companies"] + " " + movies_data["tagline"]

# Ubah text data jadi feature vectors
vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1,2),
    min_df=3
)
feature_vectors = vectorizer.fit_transform(combined_features)

# Gunakan representasi sparse untuk menghitung cosine similarity
feature_vectors_sparse = csr_matrix(feature_vectors)

# Function to compute cosine similarity in batches
def batch_cosine_similarity(feature_vectors, target_idx, batch_size=1000):
    num_batches = int(np.ceil(feature_vectors.shape[0] / batch_size))
    similarity_scores = []

    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, feature_vectors.shape[0])
        batch_vectors = feature_vectors[start_idx:end_idx]

        # Hitung similarity hanya untuk batch ini
        batch_similarity = cosine_similarity(feature_vectors[target_idx], batch_vectors)

        # Tambahkan hasil similarity ke dalam list
        similarity_scores.extend(
            [(start_idx + idx, score) for idx, score in enumerate(batch_similarity[0])]
        )

    # Urutkan berdasarkan skor similarity (descending)
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    return similarity_scores

# Function to get movie recommendations
def get_movie_recommendations(movie_name):
    all_titles = movies_data["original_title"].str.lower().tolist()
    closest_match, similarity_score = find_closest_match_tfidf(movie_name, all_titles)
    
    if similarity_score < 0.2:  # Threshold to ensure quality match
        print("No close matches found")
        return []

    index_of_the_movie = movies_data[movies_data.original_title == closest_match].index[0]

    # Hitung similarity dalam batch
    similarity_scores = batch_cosine_similarity(
        feature_vectors_sparse, target_idx=index_of_the_movie
    )
    
    sorted_similar_movies = sorted(similarity_scores, key=lambda x: x[1], reverse=True)[:30]

    recommended_movies = []
    for movie in sorted_similar_movies:
        index, score = movie
        poster_path = movies_data.loc[index, 'poster_path']
        poster_url = f"https://image.tmdb.org/t/p/original/{poster_path}"
        
        recommended_movies.append({
            "title": movies_data.loc[index, 'original_title'],
            "poster_url": poster_url,
            "vote_average": movies_data.loc[index, 'vote_average'] if movies_data.loc[index, 'vote_average'] else 0,
            "vote_count": movies_data.loc[index, 'vote_count'] if movies_data.loc[index, 'vote_count'] else 0,
            "popularity": movies_data.loc[index, 'popularity'] if movies_data.loc[index, 'popularity'] else 0,
            "genres": movies_data.loc[index, 'genres'] if movies_data.loc[index, 'genres'] else 'unknown genres',
            "production_companies": movies_data.loc[index, 'production_companies'] if movies_data.loc[index, 'production_companies'] else 'unknown production companies',
            "overview": movies_data.loc[index, 'overview'] if movies_data.loc[index, 'overview'] else 'unknown overview',
            "release_date": movies_data.loc[index, 'release_date'] if movies_data.loc[index, 'release_date'] else 'unknown release date',
            "keywords": movies_data.loc[index, 'keywords'] if movies_data.loc[index, 'keywords'] else 'unknown keywords',
            "tagline": movies_data.loc[index, 'tagline'] if movies_data.loc[index, 'tagline'] else 'unknown tagline',
        })
    
    return recommended_movies
