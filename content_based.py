import numpy as np
import pandas as pd
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import difflib

# Fungsi buat ekstrak name dari suatu kolom
def extract_names(params):
    if pd.isna(params):
        return ""
    if not isinstance(params, str):
        return ""
    try:
        params_list = ast.literal_eval(params)
        names = [name['name'] for name in params_list if 'name' in name]
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
        names = [name['name'] for name in params_list if 'name' in name]
        return ', '.join(names)
    except (ValueError, SyntaxError, TypeError):
        return ""

# Muat data dari dataset
movies_data = pd.read_csv("Movie_Dataset.csv", low_memory=False)

# Isi nilai kosong
selected_features = ["genres", "keywords", "production_companies", "tagline"]
for feature in selected_features:
    movies_data[feature] = movies_data[feature].fillna("")

# Cleaning kolom genre
movies_data["genres"] = movies_data["genres"].apply(extract_names)

# Cleaning kolom keywords
movies_data["keywords"] = movies_data["keywords"].apply(extract_names_with_comma)

# Cleaning kolom production_companies
movies_data["production_companies"] = movies_data["production_companies"].apply(extract_names_with_comma)

# Gabung selected features
combined_features =movies_data["original_title"] + " " + movies_data["genres"] + " " + movies_data["keywords"] + " " + movies_data["production_companies"] + " " + movies_data["tagline"]

# Ubah text data jadi feature vectors
vectorizer = TfidfVectorizer()
feature_vectors = vectorizer.fit_transform(combined_features)

# Gunakan representasi sparse untuk menghitung cosine similarity
feature_vectors_sparse = csr_matrix(feature_vectors)

# Function to compute cosine similarity in batches
def batch_cosine_similarity(feature_vectors, batch_size=1000):
    num_batches = int(np.ceil(feature_vectors.shape[0] / batch_size))
    similarity_matrix = np.zeros((feature_vectors.shape[0], feature_vectors.shape[0]))
    
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, feature_vectors.shape[0])
        batch_vectors = feature_vectors[start_idx:end_idx]
        batch_similarity = cosine_similarity(batch_vectors, feature_vectors)
        similarity_matrix[start_idx:end_idx] = batch_similarity
    
    return similarity_matrix

# Compute similarity in batches
similarity_matrix = batch_cosine_similarity(feature_vectors_sparse)

# Function to get movie recommendations
def get_movie_recommendations(movie_name):
    all_titles = movies_data["original_title"].tolist()
    find_close_match = difflib.get_close_matches(movie_name, all_titles)
    if not find_close_match:
        return []

    close_match = find_close_match[0]
    index_of_the_movie = movies_data[movies_data.original_title == close_match].index[0]
    similarity_score = list(enumerate(similarity_matrix[index_of_the_movie]))
    sorted_similar_movies = sorted(similarity_score, key=lambda x: x[1], reverse=True)
    
    recommended_movies = []
    for movie in sorted_similar_movies[:30]:
        index = movie[0]
        poster_path = movies_data.loc[index, 'poster_path']
        # Constructing poster path URL
        poster_url = f"https://image.tmdb.org/t/p/original/{poster_path}"
        
        recommended_movies.append({
            "title": movies_data.loc[index, 'original_title'],
            "poster_url": poster_url,
            "vote_average": movies_data.loc[index, 'vote_average'],
            "vote_count": movies_data.loc[index, 'vote_count'],
            "popularity": movies_data.loc[index, 'popularity'],
            "genres": movies_data.loc[index, 'genres'],
            "production_companies": movies_data.loc[index, 'production_companies'],
            "overview": movies_data.loc[index, 'overview'],
            "release_date": movies_data.loc[index, 'release_date']
        })
    
    return recommended_movies