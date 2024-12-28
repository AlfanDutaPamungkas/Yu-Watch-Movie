import cloudinary.uploader
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import cloudinary
from content_based import get_movie_recommendations
from forms import RegisterForm, LoginForm, EditProfileForm, EditAccForm
from user_based import get_user_based_recommendations
import logging
from models import db, User, Film, FilmRating

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE")
db.init_app(app)

with app.app_context():
    db.create_all()
    
@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    
    image = current_user.image
    name = current_user.name
    
    logger.info(f"Mencari rekomendasi untuk user {current_user.id}")
    try:
        user_based_recommendations = get_user_based_recommendations(current_user.id)
        logger.info(f"Ditemukan {len(user_based_recommendations)} rekomendasi")
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat mendapatkan rekomendasi: {e}")
        user_based_recommendations = []
    
    # Ambil film yang telah diberi rating oleh pengguna
    user_ratings = FilmRating.query.filter_by(user_id=current_user.id).all()
    liked_movies = []
    for rating in user_ratings:
        film = Film.query.get(rating.film_id)
        if film:
            liked_movies.append({
                "title": film.name,
                "rating": rating.rating
            })

    return render_template("index.html", image=image, name=name, liked_movies=liked_movies, recommendations=user_based_recommendations)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        result = db.session.execute(db.select(User).where(User.email==email))
        user = result.scalar()
        
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login')) 
        
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        
        new_user = User(
            email = form.email.data,
            name = form.name.data,
            password = hash_and_salted_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash('Email or Password incorrect, please try again.')
            return redirect(url_for('login'))
    return render_template("login.html", form=form)

@app.route("/edit-profile", methods=["GET","POST"])
def edit_profile():
    form = EditProfileForm()
    
    if form.validate_on_submit():
        image = form.image.data 
        image_url = cloudinary.uploader.upload(image)["url"] if image else current_user.image
        current_user.image = image_url
        
        current_user.name = form.name.data if form.name.data else current_user.name
        db.session.commit()
        
        return redirect(url_for("home"))
    
    return render_template("upload.html", form=form)

@app.route('/edit-acc', methods=["GET","POST"])
def edit_acc():
    form = EditAccForm()
    if form.validate_on_submit():
        if form.email.data:
            result = db.session.execute(db.select(User).where(User.email==form.email.data))
            user = result.scalar()
            
            if user:
                flash("Email is exist")
                return redirect(url_for('edit_acc')) 
            
            current_user.email = form.email.data

        current_user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8) if form.password.data else current_user.password
            
        db.session.commit()
        
        return redirect(url_for("logout"))
        
    return render_template("edit_acc.html", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/recommend", methods=["POST"])
def recommend():
    movie_name = request.form.get("movie_name")
    recommendations = get_movie_recommendations(movie_name)
    return render_template("recommendations.html", movie_name=movie_name, recommendations=recommendations)

@app.route("/rate_movie", methods=["POST"])
def rate_movie():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    
    movie_title = request.form.get("movie_title")
    rating = int(request.form.get("rating"))
    referrer = request.form.get("referrer", url_for("home"))
    
    # Check if the movie exists in the database
    movie = Film.query.filter_by(name=movie_title).first()
    if not movie:
        # If the movie doesn't exist, create it
        movie = Film(name=movie_title)
        db.session.add(movie)
        db.session.commit()
    
    # Check if the user has already rated this movie
    existing_rating = FilmRating.query.filter_by(user_id=current_user.id, film_id=movie.id).first()
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating
    else:
        # Create new rating
        new_rating = FilmRating(user_id=current_user.id, film_id=movie.id, rating=rating)
        db.session.add(new_rating)
    
    db.session.commit()
    flash("Movie rated successfully!")
    
    return redirect(referrer)

@app.route("/cancel_rating", methods=["POST"])
def cancel_rating():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    
    movie_title = request.form.get("movie_title")
    referrer = request.form.get("referrer", url_for("home"))
    
    movie = Film.query.filter_by(name=movie_title).first()
    if movie:
        rating = FilmRating.query.filter_by(user_id=current_user.id, film_id=movie.id).first()
        if rating:
            db.session.delete(rating)
            db.session.commit()
            flash(f"Rating for {movie_title} has been cancelled.")
        else:
            flash(f"You have not rated {movie_title}.")
    else:
        flash(f"{movie_title} not found.")
    
    return redirect(referrer)


@app.route("/watchlist")
def watchlist():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    
    watchlist_movies = current_user.films
    return render_template("watchlist.html", watchlist=watchlist_movies)

@app.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    
    movie_title = request.form.get("movie_title")
    movie = Film.query.filter_by(name=movie_title).first()
    
    if not movie:
        movie = Film(name=movie_title)
        db.session.add(movie)
    
    if movie not in current_user.films:
        current_user.films.append(movie)
        db.session.commit()
        flash(f"{movie_title} added to your watchlist!")
    else:
        flash(f"{movie_title} is already in your watchlist!")
    
    return redirect(request.referrer or url_for("home"))

@app.route("/remove_from_watchlist", methods=["POST"])
def remove_from_watchlist():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    
    movie_title = request.form.get("movie_title")
    movie = Film.query.filter_by(name=movie_title).first()
    
    if movie in current_user.films:
        current_user.films.remove(movie)
        db.session.commit()
        flash(f"{movie_title} removed from your watchlist!")
    else:
        flash(f"{movie_title} is not in your watchlist!")
    
    return redirect(url_for("watchlist"))

if __name__ == "__main__":
    app.run(debug=True)