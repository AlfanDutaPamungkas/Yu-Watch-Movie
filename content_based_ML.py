import numpy as np
import pandas as pd
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import difflib

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

print("Loading dataset...")
movies_data = pd.read_csv("Movie_Dataset.csv", low_memory=False)
print(f"Dataset loaded. Shape: {movies_data.shape}")
print("First 5 rows of the dataset:")
print("====================================================================================")
print(movies_data.head())

print("\nFilling missing values...")
selected_features = ["genres", "keywords", "production_companies", "tagline"]
for feature in selected_features:
    movies_data[feature] = movies_data[feature].fillna("")
    print(f"Filled missing values in {feature}")
print("First rows after filling missing values:")
print("====================================================================================")
print(movies_data[['original_title'] + selected_features].head())

print("\nCleaning columns...")
movies_data["genres"] = movies_data["genres"].apply(extract_names)
movies_data["keywords"] = movies_data["keywords"].apply(extract_names_with_comma)
movies_data["production_companies"] = movies_data["production_companies"].apply(extract_names_with_comma)
print("Columns cleaned")
print("First rows after cleaning columns:")
print("====================================================================================")
print(movies_data[['original_title', 'genres', 'keywords', 'production_companies']].head())

print("\nCombining features...")
combined_features = movies_data["genres"] + " " + movies_data["keywords"] + " " + movies_data["production_companies"] + " " + movies_data["tagline"]
print("Features combined")
print("4 combined features:")
print("====================================================================================")
print(combined_features.head())

print("\nVectorizing features...")
vectorizer = TfidfVectorizer()
feature_vectors = vectorizer.fit_transform(combined_features)
print(f"Features vectorized. Shape: {feature_vectors.shape}")
print("First 5 rows of feature vectors (sparse matrix):")
print("====================================================================================")
print(feature_vectors[:5].toarray())

feature_vectors_sparse = csr_matrix(feature_vectors)
print("Converted to sparse matrix")

def batch_cosine_similarity(feature_vectors, batch_size=1000):
    print("\nComputing cosine similarity in batches...")
    num_batches = int(np.ceil(feature_vectors.shape[0] / batch_size))
    similarity_matrix = np.zeros((feature_vectors.shape[0], feature_vectors.shape[0]))
    
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, feature_vectors.shape[0])
        batch_vectors = feature_vectors[start_idx:end_idx]
        print(f"\nProcessing Batch {i+1}/{num_batches}")
        print(f"  Batch range: {start_idx} to {end_idx}")
        print(f"  Batch shape: {batch_vectors.shape}")
        
        batch_similarity = cosine_similarity(batch_vectors, feature_vectors)
        similarity_matrix[start_idx:end_idx] = batch_similarity
        
        print(f"  Batch similarity shape: {batch_similarity.shape}")
        print(f"  Sample similarity scores :")
        print("====================================================================================")
        print(batch_similarity)
        
        print(f"Batch {i+1}/{num_batches} processed")
    
    return similarity_matrix

# Panggil fungsi
similarity_matrix = batch_cosine_similarity(feature_vectors_sparse)
print("Cosine similarity computation completed")
print("\nFirst 5x5 of similarity matrix:")
print(similarity_matrix[:5, :5])

def get_movie_recommendations(movie_name):
    print(f"\nGetting recommendations for '{movie_name}'...")
    all_titles = movies_data["original_title"].tolist()
    find_close_match = difflib.get_close_matches(movie_name, all_titles)
    if not find_close_match:
        print("No close matches found")
        return []

    close_match = find_close_match[0]
    print(f"Closest match found: '{close_match}'")
    index_of_the_movie = movies_data[movies_data.original_title == close_match].index[0]
    similarity_score = list(enumerate(similarity_matrix[index_of_the_movie]))
    sorted_similar_movies = sorted(similarity_score, key=lambda x: x[1], reverse=True)
    
    recommended_movies = []
    for movie in sorted_similar_movies[:30]:
        index = movie[0]
        poster_path = movies_data.loc[index, 'poster_path']
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
            "release_date": movies_data.loc[index, 'release_date'],
            "similarity_score": movie[1]
        })
    
    print(f"Found {len(recommended_movies)} recommendations")
    return recommended_movies

if __name__ == "__main__":
    print("\n\n\n ====================================================================================")
    user_movie = input("Enter the name of a movie you'd like recommendations for: ")
    print("====================================================================================")
    recommendations = get_movie_recommendations(user_movie)
    print("\nTop 30 recommendations:")
    for i, movie in enumerate(recommendations):
        print(f"{i}. {movie['title']} (Similarity: {movie['similarity_score']:.4f})")