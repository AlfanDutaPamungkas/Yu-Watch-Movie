import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from models import db, Film, FilmRating

def get_user_based_recommendations(user_id, n_recommendations=20, similarity_threshold=0.5):
    # Ambil semua rating
    ratings = db.session.query(FilmRating.user_id, FilmRating.film_id, FilmRating.rating).all()
    
    # Buat DataFrame dari rating
    df = pd.DataFrame(ratings, columns=['user_id', 'film_id', 'rating'])
    
    # Pivot table untuk mendapatkan matrix user-item
    user_item_matrix = df.pivot(index='user_id', columns='film_id', values='rating').fillna(0)
    
    # Hitung similarity antar user
    user_similarity = cosine_similarity(user_item_matrix)
    
    # Buat DataFrame similarity
    user_similarity_df = pd.DataFrame(user_similarity, index=user_item_matrix.index, columns=user_item_matrix.index)
    
    # Identifikasi film dengan rating sama
    user_ratings = user_item_matrix.loc[user_id]
    similar_users_based_on_ratings = set()

    for film_id, rating in user_ratings.items():
        if rating > 0:
            # Cari pengguna lain dengan rating sama untuk film yang sama
            same_rating_users = df[(df['film_id'] == film_id) & 
                                   (df['rating'] == rating) & 
                                   (df['user_id'] != user_id)]['user_id']
            similar_users_based_on_ratings.update(same_rating_users)
    
    # Filter pengguna dengan similarity di atas threshold
    similar_users = user_similarity_df[user_id][user_similarity_df[user_id] > similarity_threshold].sort_values(ascending=False)[1:11]  # 10 user paling mirip
    
    # Hapus pengguna dengan rating sama jika mereka tidak memiliki cosine similarity tinggi
    for user in similar_users_based_on_ratings:
        if user not in similar_users.index:
            continue  # Abaikan pengguna dengan rating sama jika mereka tidak memenuhi similarity_threshold
        elif user_similarity_df[user_id][user] <= similarity_threshold:
            similar_users = similar_users.drop(user, errors='ignore')  # Drop pengguna dengan cosine similarity rendah

    # Lanjutkan dengan rekomendasi seperti biasa
    recommendations = []
    for film in user_ratings[user_ratings == 0].index:
        weighted_sum = 0
        similarity_sum = 0
        for similar_user, similarity in similar_users.items():
            # Hanya pertimbangkan rating tinggi (misalnya, 4 atau lebih)
            if user_item_matrix.loc[similar_user, film] >= 4:
                weighted_sum += similarity * user_item_matrix.loc[similar_user, film]
                similarity_sum += similarity
        
        if similarity_sum > 0:
            predicted_rating = weighted_sum / similarity_sum
            recommendations.append((film, predicted_rating))
    
    # Urutkan rekomendasi berdasarkan predicted rating
    recommendations.sort(key=lambda x: x[1], reverse=True)
    
    # Ambil n_recommendations teratas
    top_recommendations = recommendations[:n_recommendations]
    
    # Ambil detail film untuk rekomendasi
    recommended_films = []
    for film_id, predicted_rating in top_recommendations:
        film = Film.query.get(film_id)
        if film:
            recommended_films.append({
                "title": film.name,
                "poster_url": "../static/assets/images/not_found.jpg",
                "predicted_rating": round(predicted_rating, 2)
            })
    
    return recommended_films
