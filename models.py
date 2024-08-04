from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

user_film = db.Table('user_film',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('film_id', db.Integer, db.ForeignKey('films.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    image = db.Column(db.String(255), default="https://th.bing.com/th/id/OIP.R9HMSxN_IRyxw9-iE1usugAAAA?rs=1&pid=ImgDetMain")
    films = db.relationship('Film', secondary=user_film, backref=db.backref('users'))
    ratings = db.relationship('FilmRating', backref='user')

class Film(db.Model):
    __tablename__ = "films"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ratings = db.relationship('FilmRating', backref='film')
    
class FilmRating(db.Model):
    __tablename__ = "film_ratings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    film_id = db.Column(db.Integer, db.ForeignKey('films.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)