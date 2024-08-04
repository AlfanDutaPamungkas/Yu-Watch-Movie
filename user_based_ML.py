import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
print("Libraries imported successfully")

print("\n#Data Loading and Preprocessing")
print("================================================")
ratings_data = [
    ('Fariz', 'Batman', 5),
    ('Fariz', 'Spider-Man', 4),
    ('Drian', 'Batman', 5),
    ('Drian', 'InterStellar', 4),\
    ('Drian', 'Iron Man', 5),
    ('Sultan', 'Spider-Man', 4),
    ('Sultan', 'Iron Man', 3),
    ('Sultan', 'Batman', 4),
    ('Sultan', 'Jurassic Park', 5),
    ('Shaqil', 'Spider-Man', 3),
    ('Shaqil', 'Jurassic Park', 4),
]
df = pd.DataFrame(ratings_data, columns=['user_id', 'film_id', 'rating'])
print("Ratings data:")
print(df)

print("\n# User-Item Matrix Creation")
print("================================================")
user_item_matrix = df.pivot(index='user_id', columns='film_id', values='rating').fillna(0)
print("User-Item Matrix:")
print(user_item_matrix)

print("\n# User Similarity Computation")
print("================================================")
user_similarity = cosine_similarity(user_item_matrix)
user_similarity_df = pd.DataFrame(user_similarity, index=user_item_matrix.index, columns=user_item_matrix.index)
print("User Similarity Matrix:")
print(user_similarity_df)

print("\n# Recommendation Function")
print("================================================")
def get_user_based_recommendations(user_id, n_recommendations=20, similarity_threshold=0.5):
    user_ratings = user_item_matrix.loc[user_id]
    print(f"User {user_id} ratings:")
    print(user_ratings)
    
    similar_users_based_on_ratings = set()
    
    print("\nFinding users with similar ratings...")
    for film_id, rating in user_ratings.items():
        if rating > 0:
            same_rating_users = df[(df['film_id'] == film_id) & (df['rating'] == rating) & (df['user_id'] != user_id)]['user_id']
            similar_users_based_on_ratings.update(same_rating_users)
    print(f"Users with similar ratings: {similar_users_based_on_ratings}")
    print("================================================")
    similar_users = user_similarity_df[user_id][user_similarity_df[user_id] > similarity_threshold].sort_values(ascending=False)[1:11]
    
    print("\nAdding users with similar ratings...")
    for similar_user in similar_users_based_on_ratings:
        if similar_user not in similar_users.index:
            similar_users.loc[similar_user] = 0.1

    print(f"Similar users for User {user_id}:")
    print("================================================")
    print(similar_users)
    
    print("\nCalculating recommendations...")
    recommendations = []
    for film in user_ratings[user_ratings == 0].index:
        weighted_sum = 0
        similarity_sum = 0
        for similar_user, similarity in similar_users.items():
            if user_item_matrix.loc[similar_user, film] >= 3:
                weighted_sum += similarity * user_item_matrix.loc[similar_user, film]
                similarity_sum += similarity
        
        if similarity_sum > 0:
            predicted_rating = weighted_sum / similarity_sum
            recommendations.append((film, predicted_rating))
    
    recommendations.sort(key=lambda x: x[1], reverse=True)
    top_recommendations = recommendations[:n_recommendations]
    
    return top_recommendations

user_id = 'Drian'
print(f"Getting recommendations for User {user_id}")
print("================================================")
recommendations = get_user_based_recommendations(user_id)
print(f"\nTop 5 recommendations for User {user_id}:")
for i, (film_id, predicted_rating) in enumerate(recommendations[:5], 1):
    print(f"{i}. Film ID: {film_id}, Predicted Rating: {predicted_rating:.2f}")