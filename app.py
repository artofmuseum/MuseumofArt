from flask import Flask, render_template, abort, url_for, redirect, flash, request, make_response, jsonify
from flask_babel import Babel, gettext, ngettext
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
import os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import secrets
from PIL import Image
from functools import wraps
from sqlalchemy import or_
from forms import RegistrationForm, LoginForm, EditUserRoleForm, ArtistForm, BlogPostForm, CommentForm, SearchForm, ArtMovementForm, VirtualMuseumForm, NewsletterForm, NewsletterSendForm, EditProfileForm, ArtworkForm
from flask_migrate import Migrate
# from weasyprint import HTML
import requests
from flask_mail import Mail, Message
import openai
import re
import unicodedata
from flask_dance.contrib.google import make_google_blueprint, google
# from flask_dance.contrib.microsoft import make_microsoft_blueprint, microsoft
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized, oauth_error
from sqlalchemy.exc import NoResultFound
import random
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, FileField
from wtforms.validators import DataRequired
import pdfkit
from sqlalchemy.orm import relationship, foreign

app = Flask(__name__)

# --- Babel Konfigürasyonu ---
babel = Babel(app)

# Desteklenen diller
LANGUAGES = {
    'en': 'English',
    'tr': 'Türkçe'
}

@babel.localeselector
def get_locale():
    # URL'den dil parametresi al
    lang = request.args.get('lang')
    if lang in LANGUAGES:
        return lang
    
    # Session'dan dil tercihi al
    if 'lang' in session:
        return session['lang']
    
    # Browser dilini kontrol et
    return request.accept_languages.best_match(LANGUAGES.keys(), default='en')

# --- YAPIlandırma ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'f9bf78b9a18ce6d46a0cd2b0b86df9da')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'artofmuseum.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads')
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# OAuth Configuration from environment variables
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
# app.config['MICROSOFT_OAUTH_CLIENT_ID'] = os.getenv('MICROSOFT_CLIENT_ID')
# app.config['MICROSOFT_OAUTH_CLIENT_SECRET'] = os.getenv('MICROSOFT_CLIENT_SECRET')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Bu sayfayı görüntülemek için lütfen giriş yapın."
login_manager.login_message_category = "info"
mail = Mail(app)
migrate = Migrate(app, db)

# --- ROUTES ---

# Dil değiştirme route'ları
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in LANGUAGES:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route('/cultural')
def cultural_page():
    return render_template('cultural.html')

@app.route('/veri_tabani')
def database_page():
    # Kullanıcı istatistikleri
    total_users = User.query.count()
    admin_count = User.query.filter_by(role='admin').count()
    akademisyen_count = User.query.filter_by(role='akademisyen').count()
    arastirmaci_count = User.query.filter_by(role='arastirmaci').count()
    kullanici_count = User.query.filter_by(role='kullanici').count()
    
    # Blog istatistikleri
    total_posts = BlogPost.query.count()
    published_posts = BlogPost.query.filter_by(status='yayinlandi').count()
    pending_posts = BlogPost.query.filter_by(status='beklemede').count()
    total_comments = Comment.query.count()
    
    # Sanatçı istatistikleri
    total_artists = Artist.query.count()
    artists_with_movement = Artist.query.filter(Artist.movement_id.isnot(None)).count()
    
    # Sanat akımları
    total_movements = ArtMovement.query.count()
    
    # Kültür yerleri
    total_cultural_places = CulturalPlace.query.count()
    approved_cultural_places = CulturalPlace.query.count()  # Tüm onaylı yerler
    pending_suggestions = SuggestCulturalPlace.query.filter_by(approved=False).count()
    
    # Müzeler
    total_museums = VirtualMuseum.query.count()
    
    # Kategoriler
    total_categories = BlogCategory.query.count()
    
    # Newsletter
    total_subscribers = NewsletterSubscriber.query.count()
    
    return render_template('veri_tabani.html',
                         total_users=total_users,
                         admin_count=admin_count,
                         akademisyen_count=akademisyen_count,
                         arastirmaci_count=arastirmaci_count,
                         kullanici_count=kullanici_count,
                         total_posts=total_posts,
                         published_posts=published_posts,
                         pending_posts=pending_posts,
                         total_comments=total_comments,
                         total_artists=total_artists,
                         artists_with_movement=artists_with_movement,
                         total_movements=total_movements,
                         total_cultural_places=total_cultural_places,
                         approved_cultural_places=approved_cultural_places,
                         pending_suggestions=pending_suggestions,
                         total_museums=total_museums,
                         total_categories=total_categories,
                         total_subscribers=total_subscribers)



app = Flask(__name__)

# --- YAPIlandırma ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'f9bf78b9a18ce6d46a0cd2b0b86df9da'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'artofmuseum.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads')
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'boztas.yusuf123@outlook.com'
app.config['MAIL_PASSWORD'] = 'Marmara.25'

# OAuth Configuration
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
# app.config['MICROSOFT_OAUTH_CLIENT_ID'] = os.getenv('MICROSOFT_CLIENT_ID')
# app.config['MICROSOFT_OAUTH_CLIENT_SECRET'] = os.getenv('MICROSOFT_CLIENT_SECRET')


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = "Bu sayfayı görüntülemek için lütfen giriş yapın."
login_manager.login_message_category = "info"
migrate = Migrate(app, db)
mail = Mail(app)

# OAuth Blueprints
google_bp = make_google_blueprint(
    client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
    client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
    scope=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
)

# Register blueprints
app.register_blueprint(google_bp, url_prefix='/login')

# OAuth storage
google_bp.storage = SQLAlchemyStorage(db.Model, user=current_user, user_required=False, session=db.session)

# --- MODELLER ---

# İlişki için yardımcı tablo (Onu kullanan modellerden ÖNCE tanımlanmalı)
post_artist_association = db.Table('post_artist_association',
    db.Column('blog_post_id', db.Integer, db.ForeignKey('blog_posts.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True)
)

class MuseumImage(db.Model):
    __tablename__ = 'museum_images'
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(120), nullable=False)
    museum_id = db.Column(db.Integer, db.ForeignKey('virtual_museums.id'), nullable=False)

class VirtualMuseum(db.Model):
    __tablename__ = 'virtual_museums'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    tour_url = db.Column(db.String(500), nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default_museum.jpg')
    images = db.relationship('MuseumImage', backref='museum', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<VirtualMuseum {self.name}>'

class ArtMovement(db.Model):
    __tablename__ = 'art_movements'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    period = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default_movement.jpg')
    artists = db.relationship('Artist', backref='movement', lazy=True)

    def __repr__(self):
        return f'<ArtMovement {self.name}>'

class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    period = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(120), nullable=False, default='default_artist.jpg')
    movement_id = db.Column(db.Integer, db.ForeignKey('art_movements.id'), nullable=True)
    posts = db.relationship('BlogPost', secondary=post_artist_association, back_populates='artists', lazy='dynamic')

    def __repr__(self):
        return f'<Artist {self.name}>'

class BlogImage(db.Model):
    __tablename__ = 'blog_images'
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(120), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)

class BlogCategory(db.Model):
    __tablename__ = 'blog_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    posts = db.relationship('BlogPost', backref='category', lazy=True)

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    summary = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default_post.jpg')
    status = db.Column(db.String(20), nullable=False, default='yayinlandi')
    post_type = db.Column(db.String(50), nullable=False, default='blog')  # blog, makale, arastirma, inceleme, haber
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan")
    artists = db.relationship('Artist', secondary=post_artist_association, back_populates='posts', lazy='dynamic')
    images = db.relationship('BlogImage', backref='post', lazy=True, cascade="all, delete-orphan")
    category_id = db.Column(db.Integer, db.ForeignKey('blog_category.id'), nullable=True)

    def __repr__(self):
        return f'<BlogPost {self.title}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(80), nullable=False, default='kullanici')
    email_confirmed = db.Column(db.Boolean, default=False)
    email_confirm_token = db.Column(db.String(120), nullable=True)
    profile_image = db.Column(db.String(120), nullable=False, default='default_artist.jpg')
    bio = db.Column(db.String(300), nullable=True, default='')
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    posts = db.relationship('BlogPost', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    followers = db.relationship('UserFollow', foreign_keys='UserFollow.followed_id', backref='followed', lazy='dynamic', cascade="all, delete-orphan")
    following = db.relationship('UserFollow', foreign_keys='UserFollow.follower_id', backref='follower', lazy='dynamic', cascade="all, delete-orphan")
    content_likes = db.relationship('ContentLike', backref='user', lazy=True, cascade="all, delete-orphan")
    content_favorites = db.relationship('ContentFavorite', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rating = db.Column(db.Integer, nullable=False, default=5)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    
    # İlişkiler
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic', cascade="all, delete-orphan")
    likes = db.relationship('CommentLike', backref='comment', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Comment {self.id}>'
    
    @property
    def is_reply(self):
        """Bu yorum bir yanıt mı?"""
        return self.parent_id is not None
    
    @property
    def is_top_level(self):
        """Bu yorum üst seviye yorum mu?"""
        return self.parent_id is None

class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_subscribed = db.Column(db.DateTime, default=datetime.utcnow)

class CommentLike(db.Model):
    __tablename__ = 'comment_likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserFollow(db.Model):
    __tablename__ = 'user_follows'
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Kültür Noktası Modeli
class CulturalPlaceImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('cultural_place.id'))
    filename = db.Column(db.String(120))
    place = relationship('CulturalPlace', back_populates='images')

class CulturalPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image = db.Column(db.String(120))  # eski tekil alan, geriye dönük uyumluluk için
    category = db.Column(db.String(50))
    images = relationship('CulturalPlaceImage', back_populates='place', cascade='all, delete-orphan')

class SuggestCulturalPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)

class Artwork(db.Model):
    __tablename__ = 'artworks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(50), nullable=False)
    period = db.Column(db.String(100), nullable=False)
    medium = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technique = db.Column(db.Text, nullable=False)
    museum = db.Column(db.String(200), nullable=False)
    facts = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"Artwork('{self.title}', '{self.artist}')"
    
    # Relationships for likes and favorites (using content_type filter)
    likes = db.relationship('ContentLike',
        primaryjoin="and_(foreign(ContentLike.content_id)==Artwork.id, ContentLike.content_type=='artwork')",
        lazy=True, cascade="all, delete-orphan")
    favorites = db.relationship('ContentFavorite',
        primaryjoin="and_(foreign(ContentFavorite.content_id)==Artwork.id, ContentFavorite.content_type=='artwork')",
        lazy=True, cascade="all, delete-orphan")

class ContentLike(db.Model):
    __tablename__ = 'content_likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # 'artwork', 'blog_post', 'artist', 'movement'
    content_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate likes
    __table_args__ = (db.UniqueConstraint('user_id', 'content_type', 'content_id', name='unique_user_content_like'),)

class ContentFavorite(db.Model):
    __tablename__ = 'content_favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # 'artwork', 'blog_post', 'artist', 'movement'
    content_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (db.UniqueConstraint('user_id', 'content_type', 'content_id', name='unique_user_content_favorite'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- YARDIMCI FONKSİYONLAR ---

@app.context_processor
def base_template():
    search_form = SearchForm()
    blog_categories = BlogCategory.query.order_by(BlogCategory.name).all()
    current_lang = get_locale()
    return dict(
        search_form=search_form, 
        blog_categories=blog_categories,
        current_lang=current_lang,
        languages=LANGUAGES
    )

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Bu sayfaya erişim için lütfen giriş yapın.", "warning")
                return redirect(url_for('login_page', next=request.path))
            if current_user.role not in roles:
                flash("Bu sayfaya erişim yetkiniz yok.", "danger")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/uploads', picture_fn)

    output_size = (800, 800)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    if f_ext.lower() == '.webp':
        i.save(picture_path, format='WEBP')
    else:
        i.save(picture_path)
    return picture_fn

def save_multiple_pictures(form_pictures):
    filenames = []
    for picture in form_pictures:
        if picture and picture.filename:
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(picture.filename)
            picture_fn = random_hex + f_ext
            picture_path = os.path.join(app.root_path, 'static/uploads', picture_fn)
            output_size = (1200, 1200)
            try:
                i = Image.open(picture)
                i.thumbnail(output_size)
                if f_ext.lower() == '.webp':
                    i.save(picture_path, format='WEBP')
                else:
                    i.save(picture_path)
            except Exception:
                picture.save(picture_path)
            filenames.append(picture_fn)
    return filenames

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_artwork_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/uploads/artworks', picture_fn)
    
    # Yüksek kaliteli resim için boyut ayarı
    output_size = (1920, 1920)
    try:
        i = Image.open(form_picture)
        i.thumbnail(output_size, Image.Resampling.LANCZOS)
        if f_ext.lower() == '.webp':
            i.save(picture_path, format='WEBP', quality=95)
        else:
            i.save(picture_path, quality=95)
    except Exception:
        form_picture.save(picture_path)
    
    return picture_fn

def create_default_categories():
    default_categories = [
        'Arkeoloji',
        'Sanat Tarihi', 
        'Antropoloji',
        'Tarih',
        'Müze Bilimi',
        'Kültür Mirası'
    ]
    for name in default_categories:
        if not BlogCategory.query.filter_by(name=name).first():
            db.session.add(BlogCategory(name=name))
    db.session.commit()

def slugify(value):
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value

# --- GENEL ROTALAR ---

@app.route('/')
def home():
    # İstatistikleri hesapla
    total_posts = BlogPost.query.filter_by(status='yayinlandi').count()
    total_artists = Artist.query.count()
    total_comments = Comment.query.count()
    
    # Son yazıları al
    latest_posts = BlogPost.query.filter_by(status='yayinlandi').order_by(BlogPost.date_posted.desc()).limit(12).all()
    
    return render_template('index_tailwind.html', 
                         total_posts=total_posts,
                         total_artists=total_artists,
                         total_comments=total_comments,
                         latest_posts=latest_posts)

@app.route('/tailwind-home')
def tailwind_home():
    return render_template('index_tailwind.html')

@app.route('/modern-home')
def modern_home():
    # İstatistikleri hesapla
    total_posts = BlogPost.query.filter_by(status='yayinlandi').count()
    total_artists = Artist.query.count()
    total_comments = Comment.query.count()
    
    # Son yazıları al
    latest_posts = BlogPost.query.filter_by(status='yayinlandi').order_by(BlogPost.date_posted.desc()).limit(12).all()
    
    return render_template('index_modern.html', 
                         total_posts=total_posts,
                         total_artists=total_artists,
                         total_comments=total_comments,
                         latest_posts=latest_posts)

@app.route('/artists')
def artists_page():
    page = request.args.get('page', 1, type=int)
    artists = Artist.query.order_by(Artist.name).paginate(page=page, per_page=8)
    return render_template('artists.html', title="Sanatçılar - Art of Museum", artists=artists)

@app.route('/blog')
def blog_list_page():
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.filter_by(status='yayinlandi').order_by(BlogPost.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('blog_list.html', title="Blog - Art of Museum", posts=posts)

@app.route('/movements')
def movements_page():
    all_movements = ArtMovement.query.order_by(ArtMovement.name).all()
    return render_template('movements.html', title="Sanat Akımları", movements=all_movements)

@app.route('/museums')
def museums_page():
    all_museums = VirtualMuseum.query.order_by(VirtualMuseum.country, VirtualMuseum.name).all()
    return render_template('museums.html', title="Sanal Müzeler", museums=all_museums)

@app.route('/movement/<int:movement_id>')
def movement_detail_page(movement_id):
    movement = ArtMovement.query.get_or_404(movement_id)
    return render_template('movement_detail.html', movement=movement)

@app.route('/artist/<int:artist_id>')
def artist_detail_page(artist_id):
    found_artist = Artist.query.get_or_404(artist_id)
    return render_template('artist_detail.html', artist=found_artist)

@app.route('/blog/<int:post_id>', methods=['GET', 'POST'])
def blog_post_detail_page(post_id):
    found_post = BlogPost.query.get_or_404(post_id)
    form = CommentForm()
    
    # Form gönderildiğinde, ana yorum veya yanıt olabilir
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Yorum yapmak için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login_page'))
        
        # Parent ID'yi doğrudan request.form'dan alıyoruz
        parent_id_str = request.form.get('parent_id')
        parent_id = None
        if parent_id_str and parent_id_str != 'None':
            try:
                parent_id = int(parent_id_str)
                # Güvenlik kontrolü: Parent yorumu var mı ve bu posta mı ait?
                if not Comment.query.filter_by(id=parent_id, post_id=found_post.id).first():
                    flash('Geçersiz yanıt işlemi.', 'danger')
                    return redirect(url_for('blog_post_detail_page', post_id=found_post.id))
            except (ValueError, TypeError):
                flash('Geçersiz yanıt işlemi.', 'danger')
                return redirect(url_for('blog_post_detail_page', post_id=found_post.id))

        # Yorumu oluştur
        new_comment = Comment(
            content=form.content.data,
            post_id=found_post.id,
            user_id=current_user.id,
            parent_id=parent_id
        )
        db.session.add(new_comment)
        db.session.commit()

        flash('Yorumunuz başarıyla gönderildi.', 'success')
        # Sayfayı yeniden yükleyerek tüm güncel yorumları göster
        return redirect(url_for('blog_post_detail_page', post_id=found_post.id))
    
    # Sadece ana yorumları (parent_id'si None olanları) çekiyoruz
    top_level_comments = Comment.query.filter_by(post_id=found_post.id, parent_id=None).order_by(Comment.date_posted.desc()).all()

    # Güvenli sayma işlemleri
    if isinstance(found_post.author.posts, list):
        author_posts_count = len(found_post.author.posts)
    else:
        author_posts_count = found_post.author.posts.count()

    if isinstance(found_post.author.followers, list):
        author_followers_count = len(found_post.author.followers)
    else:
        author_followers_count = found_post.author.followers.count()

    # Popüler yazılar ve kategoriler için örnek veri (geliştirilebilir)
    popular_posts = []
    categories = []

    return render_template(
        'blog_post_detail.html', 
        post=found_post, 
        form=form, 
        comments=top_level_comments, 
        Comment=Comment,
        author_posts_count=author_posts_count,
        author_followers_count=author_followers_count,
        popular_posts=popular_posts,
        categories=categories
    )

@app.route('/blog/post/<int:post_id>/comment/<int:comment_id>/reply', methods=['POST'])
@login_required
def add_comment_reply(post_id, comment_id):
    post = BlogPost.query.get_or_404(post_id)
    parent_comment = Comment.query.get_or_404(comment_id)
    form = CommentForm()
    if form.validate_on_submit():
        reply = Comment(
            content=form.content.data,
            author=current_user,
            post=post,
            parent_id=comment_id
        )
        db.session.add(reply)
        db.session.commit()
        flash('Yanıtınız eklendi!', 'success')
    return redirect(url_for('blog_post_detail_page', post_id=post_id))

@app.route('/hakkimizda')
def hakkimizda_page():
    return render_template('hakkimizda.html')

@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email')
    if email and '@' in email:
        if not NewsletterSubscriber.query.filter_by(email=email).first():
            new_subscriber = NewsletterSubscriber(email=email)
            db.session.add(new_subscriber)
            db.session.commit()
            flash('Bültene başarıyla abone oldunuz!', 'success')
        else:
            flash('Bu e-posta zaten abone.', 'info')
    else:
        flash('Geçerli bir e-posta giriniz.', 'danger')
    return redirect(request.referrer or url_for('home'))

@app.route('/library')
@login_required
@role_required('admin', 'akademisyen', 'arastirmaci')
def library_page():
    return render_template('library.html', title="Araştırma Kütüphanesi")

@app.route('/search', methods=['POST'])
def search_page():
    form = SearchForm()
    if form.validate_on_submit():
        search_term = form.searched.data
        artists_found = Artist.query.filter(or_(Artist.name.ilike(f'%{search_term}%'), Artist.period.ilike(f'%{search_term}%'), Artist.bio.ilike(f'%{search_term}%'))).order_by(Artist.name).all()
        posts_found = BlogPost.query.filter(BlogPost.status=='yayinlandi').filter(or_(BlogPost.title.ilike(f'%{search_term}%'), BlogPost.summary.ilike(f'%{search_term}%'), BlogPost.content.ilike(f'%{search_term}%'))).order_by(BlogPost.date_posted.desc()).all()
        if not artists_found and not posts_found:
            flash(f"'{search_term}' için sonuç bulunamadı.", 'warning')
        return render_template("search_results.html", searched=search_term, artists=artists_found, posts=posts_found)
    return redirect(url_for('home'))

# --- KULLANICI KİMLİK DOĞRULAMA ROTALARI ---
ART_BG_IMAGES = [
    # Wikimedia Commons, Unsplash, MET, Art Institute of Chicago gibi açık kaynaklardan alınmış örnekler
    'https://upload.wikimedia.org/wikipedia/commons/5/5c/Raphael_School_of_Athens.jpg',
    'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
    'https://images.metmuseum.org/CRDImages/ep/original/DT1567.jpg',
    'https://www.artic.edu/iiif/2/8e7e2e7e-2e7e-2e7e-2e7e-2e7e2e7e2e7e/full/843,/0/default.jpg',
    # Dilerseniz buraya daha fazla sanat eseri ekleyebilirsiniz
]

def get_random_art_bg():
    return random.choice(ART_BG_IMAGES)

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # Redirect to login page with register form active
    return redirect(url_for('login_page', form='register'))

def get_random_art_image():
    # Wikimedia Commons'tan sanat tarihiyle ilgili rastgele bir görsel çek
    url = 'https://commons.wikimedia.org/w/api.php'
    keywords = [
        'renaissance painting', 'impressionist art', 'museum interior', 'ancient sculpture',
        'baroque painting', 'art gallery', 'famous artwork', 'classical art', 'modern art',
        'art history', 'masterpiece', 'canvas painting', 'historic mural', 'fresco', 'art exhibition'
    ]
    search_term = random.choice(keywords)
    params = {
        'action': 'query',
        'format': 'json',
        'generator': 'search',
        'gsrsearch': search_term,
        'gsrlimit': 1,
        'gsrnamespace': 6,  # Dosya sayfaları
        'prop': 'imageinfo',
        'iiprop': 'url',
        'iiurlwidth': 1920
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            if 'imageinfo' in page:
                return page['imageinfo'][0].get('thumburl', page['imageinfo'][0].get('url'))
    except Exception:
        pass
    # Yedek görsel
    return '/static/uploads/logo.png'

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    login_form = LoginForm()
    register_form = RegistrationForm()
    bg_url = get_random_art_image()
    
    # Handle login form submission
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user, remember=login_form.remember.data)
            flash(f'Hoş geldin, {user.username}! Başarıyla giriş yaptınız.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Giriş başarısız. Lütfen e-posta ve şifrenizi kontrol edin.', 'danger')
    
    # Handle registration form submission
    if register_form.validate_on_submit():
        if User.query.filter_by(username=register_form.username.data).first():
            flash('Bu kullanıcı adı zaten alınmış.', 'danger')
            return redirect(url_for('login_page', form='register'))
        if User.query.filter_by(email=register_form.email.data).first():
            flash('Bu e-posta adresi zaten kayıtlı.', 'danger')
            return redirect(url_for('login_page', form='register'))
        new_user = User(
            first_name=register_form.first_name.data,
            last_name=register_form.last_name.data,
            username=register_form.username.data,
            email=register_form.email.data,
            email_confirmed=False
        )
        new_user.set_password(register_form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Hesabınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login_page'))
    
    return render_template('login.html', title='Giriş Yap / Kayıt Ol', login_form=login_form, register_form=register_form, bg_url=bg_url)

@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('home'))

def flatten(users):
    flat = []
    for u in users:
        if isinstance(u, list):
            flat.extend(flatten(u))
        else:
            flat.append(u)
    return flat

@app.route('/profile')
@login_required
def profile_page():
    follower_count = current_user.followers.count()
    following_count = current_user.following.count()
    raw_followers = [f.follower for f in current_user.followers]
    raw_following = [f.followed for f in current_user.following]
    followers = [u for u in raw_followers if hasattr(u, 'id') and isinstance(u.id, int)]
    following = [u for u in raw_following if hasattr(u, 'id') and isinstance(u.id, int)]
    
    # Get liked and favorited content
    liked_content = ContentLike.query.filter_by(user_id=current_user.id).order_by(ContentLike.timestamp.desc()).all()
    favorited_content = ContentFavorite.query.filter_by(user_id=current_user.id).order_by(ContentFavorite.timestamp.desc()).all()
    
    # Group content by type
    liked_artworks = []
    liked_blog_posts = []
    liked_artists = []
    liked_movements = []
    
    favorited_artworks = []
    favorited_blog_posts = []
    favorited_artists = []
    favorited_movements = []
    
    for like in liked_content:
        if like.content_type == 'artwork':
            artwork = Artwork.query.get(like.content_id)
            if artwork:
                liked_artworks.append(artwork)
        elif like.content_type == 'blog_post':
            post = BlogPost.query.get(like.content_id)
            if post:
                liked_blog_posts.append(post)
        elif like.content_type == 'artist':
            artist = Artist.query.get(like.content_id)
            if artist:
                liked_artists.append(artist)
        elif like.content_type == 'movement':
            movement = ArtMovement.query.get(like.content_id)
            if movement:
                liked_movements.append(movement)
    
    for favorite in favorited_content:
        if favorite.content_type == 'artwork':
            artwork = Artwork.query.get(favorite.content_id)
            if artwork:
                favorited_artworks.append(artwork)
        elif favorite.content_type == 'blog_post':
            post = BlogPost.query.get(favorite.content_id)
            if post:
                favorited_blog_posts.append(post)
        elif favorite.content_type == 'artist':
            artist = Artist.query.get(favorite.content_id)
            if artist:
                favorited_artists.append(artist)
        elif favorite.content_type == 'movement':
            movement = ArtMovement.query.get(favorite.content_id)
            if movement:
                favorited_movements.append(movement)
    
    # Bekleyen yazıları al
    pending_posts = BlogPost.query.filter_by(author=current_user, status='beklemede').order_by(BlogPost.date_posted.desc()).all()
    published_posts = BlogPost.query.filter_by(author=current_user, status='yayinlandi').order_by(BlogPost.date_posted.desc()).all()
    
    return render_template('profile.html', 
                         follower_count=follower_count, 
                         following_count=following_count, 
                         followers=followers, 
                         following=following,
                         liked_artworks=liked_artworks,
                         favorited_artworks=favorited_artworks,
                         liked_blog_posts=liked_blog_posts,
                         favorited_blog_posts=favorited_blog_posts,
                         liked_artists=liked_artists,
                         favorited_artists=favorited_artists,
                         liked_movements=liked_movements,
                         favorited_movements=favorited_movements,
                         pending_posts=pending_posts,
                         published_posts=published_posts)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile_page():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.profile_image.data:
            picture_file = save_picture(form.profile_image.data)
            current_user.profile_image = picture_file
        db.session.commit()
        flash('Profiliniz başarıyla güncellendi!', 'success')
        return redirect(url_for('profile_page'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('edit_profile.html', form=form)

# --- KULLANICI PANELİ ROTALARI ---
@app.route('/panel')
@login_required
@role_required('admin', 'akademisyen', 'arastirmaci')
def user_panel_page():
    user_posts = BlogPost.query.filter_by(author=current_user).order_by(BlogPost.date_posted.desc()).all()
    return render_template('user_panel.html', title="Panelim", posts=user_posts)

@app.route('/panel/add_post', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'akademisyen', 'arastirmaci')
def user_add_post_page():
    form = BlogPostForm()
    form.artists.choices = [(a.id, a.name) for a in Artist.query.order_by('name')]
    form.category.choices = [(c.id, c.name) for c in BlogCategory.query.order_by('name')]
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            author=current_user,
            status='inceleniyor',
            category_id=form.category.data,
            post_type=form.post_type.data
        )
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            post.image_file = picture_file
        selected_artists = Artist.query.filter(Artist.id.in_(form.artists.data)).all()
        for artist in selected_artists:
            post.artists.append(artist)
        db.session.add(post)
        db.session.commit()
        # Çoklu ek görselleri kaydet
        if form.ek_gorseller.data:
            filenames = save_multiple_pictures(form.ek_gorseller.data)
            for fname in filenames:
                db.session.add(BlogImage(image_file=fname, post_id=post.id))
            db.session.commit()
        flash('Yazınız incelenmek üzere başarıyla gönderildi!', 'success')
        return redirect(url_for('user_panel_page'))
    return render_template('add_post.html', title="Yeni Yazı Ekle", form=form, context='user')

# --- ADMİN ROTALARI ---
@app.route('/admin')
@login_required
@role_required('admin')
def admin_panel_page():
    all_users = User.query.all()
    posts_to_review = BlogPost.query.filter_by(status='beklemede').order_by(BlogPost.date_posted.desc()).all()
    all_museums = VirtualMuseum.query.order_by(VirtualMuseum.name).all()
    published_posts = BlogPost.query.filter_by(status='yayinlandi').order_by(BlogPost.date_posted.desc()).all()
    return render_template('admin_panel.html', users=all_users, posts_to_review=posts_to_review, museums=all_museums, published_posts=published_posts)

@app.route('/admin/approve_post/<int:post_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_post_page(post_id):
    post_to_approve = BlogPost.query.get_or_404(post_id)
    post_to_approve.status = 'yayinlandi'
    db.session.commit()
    flash(f"'{post_to_approve.title}' başlıklı yazı başarıyla yayınlandı.", 'success')
    return redirect(url_for('admin_panel_page'))

@app.route('/admin/reject_post/<int:post_id>', methods=['POST'])
@login_required
@role_required('admin')
def reject_post_page(post_id):
    post_to_reject = BlogPost.query.get_or_404(post_id)
    title = post_to_reject.title
    db.session.delete(post_to_reject)
    db.session.commit()
    flash(f"'{title}' başlıklı yazı reddedildi ve silindi.", 'warning')
    return redirect(url_for('admin_panel_page'))

# Kullanıcı Yönetimi
@app.route('/admin/edit_user_role/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user_role_page(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    form = EditUserRoleForm()
    if request.method == 'GET':
        form.role.data = user_to_edit.role
    if form.validate_on_submit():
        user_to_edit.role = form.role.data
        db.session.commit()
        flash(f"'{user_to_edit.username}' kullanıcısının rolü başarıyla '{form.role.data.capitalize()}' olarık güncellendi.", 'success')
        return redirect(url_for('admin_panel_page'))
    return render_template('edit_user_role.html', title=f"Rol Düzenle: {user_to_edit.username}", form=form, user_to_edit=user_to_edit)

# Blog Yönetimi
@app.route('/admin/add_post', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_post_page():
    form = BlogPostForm()
    form.artists.choices = [(a.id, a.name) for a in Artist.query.order_by('name')]
    form.category.choices = [(c.id, c.name) for c in BlogCategory.query.order_by('name')]
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            author=current_user,
            status='yayinlandi',
            category_id=form.category.data,
            post_type=form.post_type.data
        )
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            post.image_file = picture_file
        selected_artists = Artist.query.filter(Artist.id.in_(form.artists.data)).all()
        for artist in selected_artists:
            post.artists.append(artist)
        db.session.add(post)
        db.session.commit()
        # Çoklu ek görselleri kaydet
        if form.ek_gorseller.data:
            filenames = save_multiple_pictures(form.ek_gorseller.data)
            for fname in filenames:
                db.session.add(BlogImage(image_file=fname, post_id=post.id))
            db.session.commit()
        flash('Yeni blog yazısı başarıyla yayınlandı!', 'success')
        return redirect(url_for('blog_list_page'))
    return render_template('add_post.html', title="Yeni Blog Yazısı Ekle (Admin)", form=form, context='admin')

@app.route('/admin/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_post_page(post_id):
    post_to_edit = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm()
    form.artists.choices = [(a.id, a.name) for a in Artist.query.order_by('name')]
    form.category.choices = [(c.id, c.name) for c in BlogCategory.query.order_by('name')]
    if form.validate_on_submit():
        post_to_edit.title = form.title.data
        post_to_edit.summary = form.summary.data
        post_to_edit.content = form.content.data
        post_to_edit.category_id = form.category.data
        post_to_edit.post_type = form.post_type.data
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            post_to_edit.image_file = picture_file
        post_to_edit.artists = []
        selected_artists = Artist.query.filter(Artist.id.in_(form.artists.data)).all()
        for artist in selected_artists:
            post_to_edit.artists.append(artist)
        db.session.commit()
        # Çoklu ek görselleri kaydet
        if form.ek_gorseller.data:
            filenames = save_multiple_pictures(form.ek_gorseller.data)
            for fname in filenames:
                db.session.add(BlogImage(image_file=fname, post_id=post_to_edit.id))
            db.session.commit()
        flash('Blog yazısı başarıyla güncellendi!', 'success')
        return redirect(url_for('blog_post_detail_page', post_id=post_to_edit.id))
    elif request.method == 'GET':
        form.title.data = post_to_edit.title
        form.summary.data = post_to_edit.summary
        form.content.data = post_to_edit.content
        form.artists.data = [artist.id for artist in post_to_edit.artists]
        form.category.data = post_to_edit.category_id
        form.post_type.data = post_to_edit.post_type
    return render_template('edit_post.html', title=f"Düzenle: {post_to_edit.title}", form=form, post=post_to_edit)

@app.route('/admin/delete_post_confirm/<int:post_id>')
@login_required
@role_required('admin')
def delete_post_confirm_page(post_id):
    post_to_delete = BlogPost.query.get_or_404(post_id)
    return render_template('delete_post_confirm.html', title="Silme Onayı", post_to_delete=post_to_delete)

@app.route('/admin/delete_post/<int:post_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_post_page(post_id):
    post_to_delete = BlogPost.query.get_or_404(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    flash(f"'{post_to_delete.title}' başlıklı yazı başarıyla silindi.", 'success')
    return redirect(url_for('blog_list_page'))

# Sanatçı Yönetimi
@app.route('/admin/add_artist', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_artist_page():
    form = ArtistForm()
    form.movement.choices = [(0, '-- Bir Akım Seçin --')] + [(m.id, m.name) for m in ArtMovement.query.order_by('name')]
    if form.validate_on_submit():
        movement_id = form.movement.data if form.movement.data > 0 else None
        artist = Artist(name=form.name.data, period=form.period.data, bio=form.bio.data, movement_id=movement_id)
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            artist.image_file = picture_file
        db.session.add(artist)
        db.session.commit()
        flash(f"'{artist.name}' adlı sanatçı başarıyla eklendi!", 'success')
        return redirect(url_for('artists_page'))
    return render_template('add_artist.html', title="Yeni Sanatçı Ekle", form=form)

@app.route('/admin/edit_artist/<int:artist_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_artist_page(artist_id):
    artist_to_edit = Artist.query.get_or_404(artist_id)
    form = ArtistForm()
    form.movement.choices = [(0, '-- Bir Akım Seçin --')] + [(m.id, m.name) for m in ArtMovement.query.order_by('name')]
    if form.validate_on_submit():
        artist_to_edit.name = form.name.data
        artist_to_edit.period = form.period.data
        artist_to_edit.bio = form.bio.data
        movement_id = form.movement.data if form.movement.data > 0 else None
        artist_to_edit.movement_id = movement_id
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            artist_to_edit.image_file = picture_file
        db.session.commit()
        flash(f"'{artist_to_edit.name}' adlı sanatçının bilgileri başarıyla güncellendi!", 'success')
        return redirect(url_for('artist_detail_page', artist_id=artist_to_edit.id))
    elif request.method == 'GET':
        form.name.data = artist_to_edit.name
        form.period.data = artist_to_edit.period
        form.bio.data = artist_to_edit.bio
        form.movement.data = artist_to_edit.movement_id if artist_to_edit.movement_id else 0
    return render_template('edit_artist.html', title=f"Düzenle: {artist_to_edit.name}", form=form, artist_to_edit=artist_to_edit)

@app.route('/admin/delete_artist_confirm/<int:artist_id>')
@login_required
@role_required('admin')
def delete_artist_confirm_page(artist_id):
    artist_to_delete = Artist.query.get_or_404(artist_id)
    return render_template('delete_artist_confirm.html', title="Silme Onayı", artist_to_delete=artist_to_delete)

@app.route('/admin/delete_artist/<int:artist_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_artist_page(artist_id):
    artist_to_delete = Artist.query.get_or_404(artist_id)
    db.session.delete(artist_to_delete)
    db.session.commit()
    flash(f"'{artist_to_delete.name}' adlı sanatçı başarıyla silindi.", 'success')
    return redirect(url_for('artists_page'))

# Sanat Akımı Yönetimi
@app.route('/admin/add_movement', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_movement_page():
    form = ArtMovementForm()
    if form.validate_on_submit():
        movement = ArtMovement(name=form.name.data, period=form.period.data, description=form.description.data)
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            movement.image_file = picture_file
        db.session.add(movement)
        db.session.commit()
        flash('Yeni sanat akımı başarıyla eklendi!', 'success')
        return redirect(url_for('movements_page'))
    return render_template('add_movement.html', title="Yeni Sanat Akımı Ekle", form=form)

@app.route('/admin/edit_movement/<int:movement_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_movement_page(movement_id):
    movement_to_edit = ArtMovement.query.get_or_404(movement_id)
    form = ArtMovementForm()
    if form.validate_on_submit():
        movement_to_edit.name = form.name.data
        movement_to_edit.period = form.period.data
        movement_to_edit.description = form.description.data
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            movement_to_edit.image_file = picture_file
        db.session.commit()
        flash(f"'{movement_to_edit.name}' akımı başarıyla güncellendi!", 'success')
        return redirect(url_for('movement_detail_page', movement_id=movement_to_edit.id))
    elif request.method == 'GET':
        form.name.data = movement_to_edit.name
        form.period.data = movement_to_edit.period
        form.description.data = movement_to_edit.description
    return render_template('edit_movement.html', title=f"Düzenle: {movement_to_edit.name}", form=form, movement_to_edit=movement_to_edit)

@app.route('/admin/delete_movement_confirm/<int:movement_id>')
@login_required
@role_required('admin')
def delete_movement_confirm_page(movement_id):
    movement_to_delete = ArtMovement.query.get_or_404(movement_id)
    return render_template('delete_movement_confirm.html', title="Silme Onayı", movement_to_delete=movement_to_delete)

@app.route('/admin/delete_movement/<int:movement_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_movement_page(movement_id):
    movement_to_delete = ArtMovement.query.get_or_404(movement_id)
    for artist in movement_to_delete.artists:
        artist.movement_id = None
    db.session.delete(movement_to_delete)
    db.session.commit()
    flash(f"'{movement_to_delete.name}' adlı sanat akımı başarıyla silindi.", 'success')
    return redirect(url_for('movements_page'))

@app.route('/admin/add_museum', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_museum_page():
    form = VirtualMuseumForm()
    if form.validate_on_submit():
        museum = VirtualMuseum(
            name=form.name.data,
            city=form.city.data,
            country=form.country.data,
            description=form.description.data,
            tour_url=form.tour_url.data
        )
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            museum.image_file = picture_file
        db.session.add(museum)
        db.session.commit()
        flash('Yeni sanal müze başarıyla eklendi!', 'success')
        return redirect(url_for('museums_page'))
    return render_template('add_museum.html', title="Yeni Sanal Müze Ekle", form=form)

@app.route('/blog/<int:post_id>/pdf')
def blog_post_pdf(post_id):
    post = BlogPost.query.get_or_404(post_id)
    html = render_template('blog_pdf.html', post=post, year=datetime.now().year)
    pdf = pdfkit.from_string(html, False)
    response = make_response(pdf)
    filename = slugify(post.title) + '.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@app.route('/blog/kategori/<int:category_id>')
def blog_category_page(category_id):
    category = BlogCategory.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.filter_by(status='yayinlandi', category_id=category.id).order_by(BlogPost.date_posted.desc()).paginate(page=page, per_page=6)
    return render_template('blog_category.html', title=f"{category.name} - Blog Kategorisi", posts=posts, selected_category=category)

@app.route('/explore', methods=['GET', 'POST'])
def explore_page():
    images = []
    query = request.args.get('q')
    if query:
        url = 'https://commons.wikimedia.org/w/api.php'
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'imageinfo',
            'generator': 'search',
            'gsrsearch': query,
            'gsrlimit': 12,
            'gsrnamespace': 6,  # SADECE DOSYA (GÖRSEL) SAYFALARI
            'iiprop': 'url',
            'iiurlwidth': 400
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        print('Wikimedia API yanıtı:', data)  # Debug için
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            if 'imageinfo' in page:
                images.append({
                    'title': page.get('title'),
                    'url': page['imageinfo'][0].get('thumburl', page['imageinfo'][0].get('url'))
                })
    return render_template('explore.html', images=images, query=query or '')

@app.route('/admin/send_newsletter', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def send_newsletter_page():
    form = NewsletterSendForm()
    if form.validate_on_submit():
        subscribers = NewsletterSubscriber.query.all()
        if not subscribers:
            flash('Hiç abone yok!', 'warning')
            return redirect(url_for('send_newsletter_page'))
        for sub in subscribers:
            msg = Message(
                subject=form.subject.data,
                recipients=[sub.email],
                body=form.body.data,
                sender=app.config['MAIL_USERNAME']
            )
            mail.send(msg)
        flash('Bülten başarıyla gönderildi!', 'success')
        return redirect(url_for('admin_panel_page'))
    return render_template('send_newsletter.html', form=form)

@app.route('/maya')
def maya_chat():
    return render_template('maya_chat.html')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# OpenAI client'ı try-except ile oluştur
try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
except AttributeError:
    # Eski OpenAI API versiyonu için
    openai.api_key = OPENAI_API_KEY
    client = openai

@app.route('/maya_ask', methods=['POST'])
def maya_ask():
    data = request.get_json()
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided.'}), 400

    # Eğer kullanıcı haritaya nokta eklemek istiyorsa (örnek komut: Haritaya nokta ekle: Adı=..., Kategori=..., Açıklama=..., Enlem=..., Boylam=...)
    if user_message.lower().startswith('haritaya nokta ekle:'):
        try:
            # Basit bir parse işlemi (Adı=..., Kategori=..., Açıklama=..., Enlem=..., Boylam=...)
            import re
            fields = dict(re.findall(r'(Adı|Kategori|Açıklama|Enlem|Boylam)\s*=\s*([^,]+)', user_message, re.IGNORECASE))
            name = fields.get('Adı') or fields.get('adı')
            category = fields.get('Kategori') or fields.get('kategori')
            description = fields.get('Açıklama') or fields.get('açıklama')
            latitude = fields.get('Enlem') or fields.get('enlem')
            longitude = fields.get('Boylam') or fields.get('boylam')
            if not (name and category and description and latitude and longitude):
                return jsonify({'answer': 'Lütfen Adı, Kategori, Açıklama, Enlem ve Boylam alanlarını eksiksiz girin. Örnek: Haritaya nokta ekle: Adı=..., Kategori=..., Açıklama=..., Enlem=..., Boylam=...'}), 200
            suggestion = SuggestCulturalPlace(
                name=name.strip(),
                category=category.strip(),
                description=description.strip(),
                latitude=float(latitude.strip()),
                longitude=float(longitude.strip())
            )
            db.session.add(suggestion)
            db.session.commit()
            return jsonify({'answer': f"'{name}' adlı nokta öneriniz başarıyla alındı! Onaylandıktan sonra haritada görünecek."}), 200
        except Exception as e:
            return jsonify({'answer': 'Nokta eklenirken bir hata oluştu: ' + str(e)}), 200

    system_prompt = (
        "You are Maya, an expert in art and art history. Only answer questions about art, artists, art movements, art history, and related topics. "
        "If the question is not about art, politely refuse. Answer in English, in an academic yet friendly tone."
    )
    try:
        # Yeni OpenAI API versiyonu için
        if hasattr(client, 'chat'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=600,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
        else:
            # Eski OpenAI API versiyonu için
            response = client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=600,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
        
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/delete_museum_confirm/<int:museum_id>')
@login_required
@role_required('admin')
def delete_museum_confirm_page(museum_id):
    museum_to_delete = VirtualMuseum.query.get_or_404(museum_id)
    return render_template('delete_museum_confirm.html', title="Müze Silme Onayı", museum_to_delete=museum_to_delete)

@app.route('/admin/delete_museum/<int:museum_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_museum_page(museum_id):
    museum_to_delete = VirtualMuseum.query.get_or_404(museum_id)
    db.session.delete(museum_to_delete)
    db.session.commit()
    flash(f"'{museum_to_delete.name}' adlı müze başarıyla silindi.", 'success')
    return redirect(url_for('museums_page'))

# OAuth Callbacks
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Google ile giriş başarısız.", "danger")
        return False
    
    resp = google.get("/oauth2/v1/userinfo")
    if not resp.ok:
        flash("Google kullanıcı bilgileri alınamadı.", "danger")
        return False
    
    google_info = resp.json()
    google_user_id = str(google_info["id"])
    
    # Check if user already exists
    user = User.query.filter_by(email=google_info["email"]).first()
    
    if not user:
        # Create new user
        user = User(
            first_name=google_info.get("given_name", ""),
            last_name=google_info.get("family_name", ""),
            username=google_info["email"].split("@")[0],  # Use email prefix as username
            email=google_info["email"],
            email_confirmed=True  # Google email is already verified
        )
        user.set_password(secrets.token_urlsafe(16))  # Random password
        db.session.add(user)
        db.session.commit()
        flash("Google hesabınızla başarıyla kayıt oldunuz!", "success")
    else:
        flash("Google hesabınızla başarıyla giriş yaptınız!", "success")
    
    login_user(user)
    return False  # Don't save the OAuth token

@oauth_error.connect_via(google_bp)
def google_error(blueprint, error, error_description=None, error_uri=None):
    flash(f"Google OAuth hatası: {error}", "danger")

# --- YASAL SAYFALAR ---
@app.route('/kullanici-sozlesmesi')
def kullanici_sozlesmesi():
    return render_template('kullanici_sozlesmesi.html')

@app.route('/gizlilik-politikasi')
def gizlilik_politikasi():
    return render_template('gizlilik_politikasi.html')

@app.route('/cerez-politikasi')
def cerez_politikasi():
    return render_template('cerez_politikasi.html')

@app.route('/aydinlatma-metni')
def aydinlatma_metni():
    return render_template('aydinlatma_metni.html')

@app.route('/telif-hakki')
def telif_hakki():
    return render_template('telif_hakki.html')

@app.route('/sorumluluk-reddi')
def sorumluluk_reddi():
    return render_template('sorumluluk_reddi.html')

@app.route('/iletisim')
def iletisim():
    return render_template('iletisim.html')

@app.route('/like_comment/<int:comment_id>', methods=['POST'])
@login_required
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    existing_like = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        liked = False
    else:
        new_like = CommentLike(user_id=current_user.id, comment_id=comment_id)
        db.session.add(new_like)
        db.session.commit()
        liked = True
    like_count = comment.likes.count()
    return jsonify({'success': True, 'liked': liked, 'like_count': like_count})

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    user_to_follow = User.query.get_or_404(user_id)
    if user_to_follow.id == current_user.id:
        return jsonify({'success': False, 'message': 'Kendinizi takip edemezsiniz.'}), 400
    existing = UserFollow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()
    if not existing:
        follow = UserFollow(follower_id=current_user.id, followed_id=user_id)
        db.session.add(follow)
        db.session.commit()
    follower_count = user_to_follow.followers.count()
    return jsonify({'success': True, 'following': True, 'follower_count': follower_count})

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    user_to_unfollow = User.query.get_or_404(user_id)
    follow = UserFollow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()
    if follow:
        db.session.delete(follow)
        db.session.commit()
    follower_count = user_to_unfollow.followers.count()
    return jsonify({'success': True, 'following': False, 'follower_count': follower_count})

@app.route('/user/<int:user_id>')
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    follower_count = user.followers.count()
    following_count = user.following.count()
    is_following = False
    if current_user.is_authenticated and user.id != current_user.id:
        is_following = UserFollow.query.filter_by(follower_id=current_user.id, followed_id=user.id).first() is not None
    return render_template('public_profile.html', user=user, follower_count=follower_count, following_count=following_count, is_following=is_following)

# Kültür Haritası Sayfası
@app.route('/cultural_map')
def cultural_map():
    return render_template('cultural_map.html')

# Kültür Noktaları API
@app.route('/api/cultural_places')
def api_cultural_places():
    places = CulturalPlace.query.all()
    return jsonify([
        {
            'name': p.name,
            'description': p.description,
            'lat': p.latitude,
            'lng': p.longitude,
            'image': p.image,
            'category': p.category,
            'images': [img.filename for img in p.images]
        } for p in places
    ])

CULTURAL_CATEGORIES = [
    ('Müze', 'Müze'),
    ('Galeri', 'Galeri'),
    ('Etkinlik', 'Etkinlik'),
    ('Tarihi Mekan', 'Tarihi Mekan'),
    ('Diğer', 'Diğer')
]

class CulturalPlaceForm(FlaskForm):
    name = StringField('İsim', validators=[DataRequired()])
    description = TextAreaField('Açıklama', validators=[DataRequired()])
    category = SelectField('Kategori', choices=CULTURAL_CATEGORIES, validators=[DataRequired()])
    latitude = FloatField('Enlem', validators=[DataRequired()])
    longitude = FloatField('Boylam', validators=[DataRequired()])
    image = FileField('Görsel')

@app.route('/admin/cultural_places', methods=['GET', 'POST'])
@login_required
def admin_cultural_places():
    if current_user.role != 'admin':
        flash('Yetkisiz erişim.', 'danger')
        return redirect(url_for('home'))
    form = CulturalPlaceForm()
    # Onaylama işlemi
    if request.method == 'POST' and request.form.get('approve_id'):
        approve_id = int(request.form.get('approve_id'))
        suggestion = SuggestCulturalPlace.query.get(approve_id)
        if suggestion:
            place = CulturalPlace(
                name=suggestion.name,
                description=suggestion.description,
                category=suggestion.category,
                latitude=suggestion.latitude,
                longitude=suggestion.longitude,
                image=suggestion.image
            )
            db.session.add(place)
            suggestion.approved = True
            db.session.commit()
            flash('Öneri onaylandı ve haritaya eklendi!', 'success')
        return redirect(url_for('admin_cultural_places'))
    # Silme işlemi
    if request.method == 'POST' and request.form.get('delete_id'):
        delete_id = int(request.form.get('delete_id'))
        suggestion = SuggestCulturalPlace.query.get(delete_id)
        if suggestion:
            db.session.delete(suggestion)
            db.session.commit()
            flash('Öneri silindi.', 'info')
        return redirect(url_for('admin_cultural_places'))
    # Normal ekleme işlemi
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_file = form.image.data
            image_filename = image_file.filename
            upload_path = os.path.join('static', 'uploads', image_filename)
            image_file.save(upload_path)
        place = CulturalPlace(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            image=image_filename
        )
        db.session.add(place)
        db.session.flush()  # id almak için
        # Çoklu görselleri kaydet
        if hasattr(form, 'images') and form.images.data:
            for img_file in form.images.data:
                if img_file and img_file.filename:
                    img_filename = img_file.filename
                    upload_path = os.path.join('static', 'uploads', img_filename)
                    img_file.save(upload_path)
                    db.session.add(CulturalPlaceImage(place_id=place.id, filename=img_filename))
        db.session.commit()
        flash('Kültür noktası eklendi!', 'success')
        return redirect(url_for('admin_cultural_places'))
    places = CulturalPlace.query.order_by(CulturalPlace.id.desc()).all()
    suggestions = SuggestCulturalPlace.query.filter_by(approved=False).order_by(SuggestCulturalPlace.created_at.desc()).all()
    return render_template('admin_cultural_places.html', form=form, places=places, suggestions=suggestions)

def add_sample_cultural_places_v2():
    from app import db, CulturalPlace, CulturalPlaceImage
    # Örnek görsellerin uploads klasöründe olduğundan emin olun
    samples = [
        {
            'name': 'Louvre Müzesi',
            'description': "Dünyanın en büyük sanat müzesi. Paris'in kalbinde yer alan Louvre, Mona Lisa, Venus de Milo ve binlerce başyapıta ev sahipliği yapar. 12. yüzyıldan kalma bir saraydan müzeye dönüştürülmüştür. Ziyaretçilerine sanatın ve tarihin büyüleyici bir yolculuğunu sunar.",
            'category': 'Müze',
            'latitude': 48.8606,
            'longitude': 2.3376,
            'images': ['louvre1.jpg', 'louvre2.jpg', 'louvre3.jpg']
        },
        {
            'name': 'Ayasofya',
            'description': "İstanbul'un simgesi, Bizans ve Osmanlı'nın izlerini taşıyan eşsiz bir yapı. 1500 yıldan fazla tarihe sahip olan Ayasofya, hem kilise hem cami hem de müze olarak kullanılmıştır. Mozaikleri, kubbesi ve mistik atmosferiyle büyüler.",
            'category': 'Tarihi Mekan',
            'latitude': 41.0086,
            'longitude': 28.9802,
            'images': ['ayasofya1.jpg', 'ayasofya2.jpg']
        },
        {
            'name': 'Tate Modern',
            'description': "Londra'nın Thames Nehri kıyısında yer alan Tate Modern, çağdaş sanatın en önemli merkezlerinden biridir. Eski bir elektrik santralinden dönüştürülmüş olan müze, devasa sergi salonları ve interaktif sanat deneyimleriyle ünlüdür.",
            'category': 'Müze',
            'latitude': 51.5076,
            'longitude': -0.0994,
            'images': ['tate1.jpg', 'tate2.jpg']
        },
        {
            'name': 'Venedik Bienali',
            'description': "Dünyanın en prestijli çağdaş sanat etkinliklerinden biri. Her iki yılda bir Venedik'te düzenlenen bienal, uluslararası sanatçıları ve yenilikçi eserleri bir araya getirir. Sanatın güncel nabzını tutar.",
            'category': 'Etkinlik',
            'latitude': 45.4371,
            'longitude': 12.3326,
            'images': ['bienal1.jpg', 'bienal2.jpg']
        },
        {
            'name': 'Salt Galata',
            'description': "İstanbul'un kalbinde, çağdaş sanat ve araştırma merkezi. Modern sergiler, arşivler ve etkinliklerle sanatseverlerin buluşma noktasıdır.",
            'category': 'Galeri',
            'latitude': 41.0201,
            'longitude': 28.9769,
            'images': ['salt1.jpg', 'salt2.jpg']
        }
    ]
    for s in samples:
        place = CulturalPlace(
            name=s['name'],
            description=s['description'],
            category=s['category'],
            latitude=s['latitude'],
            longitude=s['longitude'],
            image=s['images'][0] if s['images'] else None
        )
        db.session.add(place)
        db.session.flush()
        for img in s['images']:
            db.session.add(CulturalPlaceImage(place_id=place.id, filename=img))
    db.session.commit()

@app.route('/suggest_cultural_place', methods=['POST'])
def suggest_cultural_place():
    from flask import jsonify
    # CORS header
    response_headers = {'Access-Control-Allow-Origin': '*'}
    if request.content_type and request.content_type.startswith('application/json'):
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        category = data.get('category')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        image_filename = None
        # Görsel desteği JSON ile yok, sadece form-data ile
    else:
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        image_file = request.files.get('image')
        image_filename = None
        if image_file:
            image_filename = image_file.filename
            upload_path = os.path.join('static', 'uploads', image_filename)
            image_file.save(upload_path)
    if not (name and description and category and latitude and longitude):
        return jsonify({'success': False, 'error': 'Tüm alanlar zorunlu.'}), 400, response_headers
    try:
        suggestion = SuggestCulturalPlace(
            name=name,
            description=description,
            category=category,
            latitude=float(latitude),
            longitude=float(longitude),
            image=image_filename
        )
        db.session.add(suggestion)
        db.session.commit()
        return jsonify({'success': True}), 200, response_headers
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500, response_headers

def update_cultural_places_from_wikipedia():
    from app import db, CulturalPlace
    for place in CulturalPlace.query.all():
        wiki_api = f'https://tr.wikipedia.org/api/rest_v1/page/summary/{place.name.replace(" ", "_")}'
        try:
            res = requests.get(wiki_api, timeout=5)
            if res.ok:
                data = res.json()
                summary = data.get('extract')
                thumb = data.get('thumbnail', {}).get('source')
                updated = False
                if summary and (not place.description or len(place.description) < 40):
                    place.description = summary
                    updated = True
                if thumb and not place.image:
                    # Wikipedia görselini indirip uploads'a kaydet
                    img_data = requests.get(thumb, timeout=5).content
                    ext = thumb.split('.')[-1].split('?')[0][:4]
                    filename = f'wikipedia_{place.id}.{ext}'
                    with open(f'static/uploads/{filename}', 'wb') as f:
                        f.write(img_data)
                    place.image = filename
                    updated = True
                if updated:
                    print(f"Güncellendi: {place.name}")
            else:
                print(f"Wikipedia bulunamadı: {place.name}")
        except Exception as e:
            print(f"Wikipedia hatası: {place.name} - {e}")
    db.session.commit()

def add_sample_istanbul_places():
    from app import db, CulturalPlace, CulturalPlaceImage
    samples = [
        {
            'name': 'İstanbul Modern',
            'description': "Türkiye'nin ilk modern ve çağdaş sanat müzesi. Boğaz manzaralı yeni binasında uluslararası sergiler, koleksiyonlar ve etkinlikler sunar.",
            'category': 'Müze',
            'latitude': 41.0306,
            'longitude': 28.9769,
            'images': ['istanbulmodern1.jpg', 'istanbulmodern2.jpg']
        },
        {
            'name': 'Sakıp Sabancı Müzesi',
            'description': "Emirgan'da Boğaz'a nazır tarihi bir köşkte yer alan müze, Osmanlı hat sanatı koleksiyonu ve uluslararası sergileriyle ünlüdür.",
            'category': 'Müze',
            'latitude': 41.1091,
            'longitude': 29.0556,
            'images': ['sabanci1.jpg', 'sabanci2.jpg']
        },
        {
            'name': 'Pera Müzesi',
            'description': "Beyoğlu'nda yer alan Pera Müzesi, Orientalist resim koleksiyonu, Kütahya çinileri ve çağdaş sanat sergileriyle dikkat çeker.",
            'category': 'Müze',
            'latitude': 41.0321,
            'longitude': 28.9768,
            'images': ['pera1.jpg', 'pera2.jpg']
        },
        {
            'name': 'Salt Galata',
            'description': "Tarihi Osmanlı Bankası binasında yer alan Salt Galata, çağdaş sanat sergileri, arşivler ve araştırma alanlarıyla öne çıkar.",
            'category': 'Galeri',
            'latitude': 41.0201,
            'longitude': 28.9769,
            'images': ['saltgalata1.jpg', 'saltgalata2.jpg']
        },
        {
            'name': 'İKSV İstanbul Film Festivali',
            'description': "Her yıl düzenlenen uluslararası film festivali. Dünya sinemasından seçkin filmler ve özel gösterimler İstanbul'un farklı mekanlarında sanatseverlerle buluşur.",
            'category': 'Etkinlik',
            'latitude': 41.0381,
            'longitude': 28.9857,
            'images': ['iksv1.jpg', 'iksv2.jpg']
        }
    ]
    for s in samples:
        place = CulturalPlace(
            name=s['name'],
            description=s['description'],
            category=s['category'],
            latitude=s['latitude'],
            longitude=s['longitude'],
            image=s['images'][0] if s['images'] else None
        )
        db.session.add(place)
        db.session.flush()
        for img in s['images']:
            db.session.add(CulturalPlaceImage(place_id=place.id, filename=img))
    db.session.commit()


# --- EKSTRA ROUTES: Menüdeki eksik yönlendirmeler için ---
@app.route('/veri_tabani')
def veri_tabani_page():
    return render_template('veri_tabani.html')

@app.route('/maya_chat')
def maya_chat_page():
    return render_template('maya_chat.html')

@app.route('/cultural-map')
def cultural_map_page():
    return render_template('cultural_map.html')

@app.route('/create-categories')
def create_categories():
    # Önce eski kategorileri temizle
    BlogCategory.query.delete()
    db.session.commit()
    
    # Yeni kategorileri oluştur
    create_default_categories()
    return "Kategoriler temizlendi ve yeniden oluşturuldu!"

@app.route('/check-categories')
def check_categories():
    categories = BlogCategory.query.all()
    result = []
    for cat in categories:
        result.append(f"ID: {cat.id} - Name: {cat.name}")
    return "<br>".join(result)

@app.route('/sozluk')
def dictionary_page():
    return render_template('dictionary.html')

@app.route('/dictionary')
def dictionary_page_english():
    return render_template('dictionary.html')

@app.route('/rastgele-eser')
def random_artwork_page():
    return render_template('random_artwork.html')

@app.route('/random-artwork')
def random_artwork_page_english():
    # Veritabanından eserleri çek ve JSON'a dönüştürülebilir hale getir
    artworks = Artwork.query.all()
    artworks_data = []
    for artwork in artworks:
        artworks_data.append({
            'id': artwork.id,
            'title': artwork.title,
            'artist': artwork.artist,
            'year': artwork.year,
            'period': artwork.period,
            'medium': artwork.medium,
            'location': artwork.location,
            'image_url': artwork.image_url,
            'description': artwork.description,
            'technique': artwork.technique,
            'museum': artwork.museum,
            'facts': artwork.facts
        })
    return render_template('random_artwork.html', artworks=artworks_data)

@app.route('/admin/add_artwork', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_artwork_page():
    form = ArtworkForm()
    if form.validate_on_submit():
        # Resim URL'si veya dosya yükleme kontrolü
        image_url = form.image_url.data
        
        # Eğer dosya yüklendiyse
        if form.image_file.data and form.image_file.data.filename:
            picture_file = save_artwork_picture(form.image_file.data)
            image_url = url_for('static', filename=f'uploads/artworks/{picture_file}')
        
        # Eğer hem URL hem dosya yoksa hata ver
        if not image_url:
            flash('Lütfen bir resim URL\'si girin veya dosya yükleyin!', 'error')
            return render_template('admin/add_artwork.html', title='Eser Ekle', form=form)
        
        artwork = Artwork(
            title=form.title.data,
            artist=form.artist.data,
            year=form.year.data,
            period=form.period.data,
            medium=form.medium.data,
            location=form.location.data,
            image_url=image_url,
            description=form.description.data,
            technique=form.technique.data,
            museum=form.museum.data,
            facts=form.facts.data,
            created_by=current_user.id
        )
        db.session.add(artwork)
        db.session.commit()
        flash('Sanat eseri başarıyla eklendi!', 'success')
        return redirect(url_for('admin_artworks_page'))
    return render_template('admin/add_artwork.html', title='Eser Ekle', form=form)

@app.route('/admin/artworks')
@login_required
@role_required('admin')
def admin_artworks_page():
    from datetime import datetime, timedelta
    
    artworks = Artwork.query.order_by(Artwork.created_at.desc()).all()
    
    # Bu ay istatistiği
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_artworks = [a for a in artworks if a.created_at >= start_of_month]
    
    return render_template('admin/artworks.html', title='Sanat Eserleri', 
                         artworks=artworks, 
                         this_month_count=len(this_month_artworks))

@app.route('/admin/edit_artwork/<int:artwork_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_artwork_page(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    form = ArtworkForm()
    
    if form.validate_on_submit():
        # Resim URL'si veya dosya yükleme kontrolü
        image_url = form.image_url.data
        
        # Eğer dosya yüklendiyse
        if form.image_file.data and form.image_file.data.filename:
            picture_file = save_artwork_picture(form.image_file.data)
            image_url = url_for('static', filename=f'uploads/artworks/{picture_file}')
        
        # Eğer hem URL hem dosya yoksa hata ver
        if not image_url:
            flash('Lütfen bir resim URL\'si girin veya dosya yükleyin!', 'error')
            return render_template('admin/edit_artwork.html', title='Eser Düzenle', form=form, artwork=artwork)
        
        artwork.title = form.title.data
        artwork.artist = form.artist.data
        artwork.year = form.year.data
        artwork.period = form.period.data
        artwork.medium = form.medium.data
        artwork.location = form.location.data
        artwork.image_url = image_url
        artwork.description = form.description.data
        artwork.technique = form.technique.data
        artwork.museum = form.museum.data
        artwork.facts = form.facts.data
        
        db.session.commit()
        flash('Sanat eseri başarıyla güncellendi!', 'success')
        return redirect(url_for('admin_artworks_page'))
    
    elif request.method == 'GET':
        form.title.data = artwork.title
        form.artist.data = artwork.artist
        form.year.data = artwork.year
        form.period.data = artwork.period
        form.medium.data = artwork.medium
        form.location.data = artwork.location
        form.image_url.data = artwork.image_url
        form.description.data = artwork.description
        form.technique.data = artwork.technique
        form.museum.data = artwork.museum
        form.facts.data = artwork.facts
    
    return render_template('admin/edit_artwork.html', title='Eser Düzenle', form=form, artwork=artwork)

@app.route('/admin/delete_artwork/<int:artwork_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_artwork_page(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    db.session.delete(artwork)
    db.session.commit()
    flash('Sanat eseri başarıyla silindi!', 'success')
    return redirect(url_for('admin_artworks_page'))

# General Content Like/Unlike API
@app.route('/content/<content_type>/<int:content_id>/like', methods=['POST'])
@login_required
def like_content(content_type, content_id):
    # Validate content type
    valid_types = ['artwork', 'blog_post', 'artist', 'movement']
    if content_type not in valid_types:
        return jsonify({'error': 'Invalid content type'}), 400
    
    existing_like = ContentLike.query.filter_by(
        user_id=current_user.id, 
        content_type=content_type, 
        content_id=content_id
    ).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'status': 'unliked', 'message': 'Beğeni kaldırıldı'})
    else:
        new_like = ContentLike(
            user_id=current_user.id, 
            content_type=content_type, 
            content_id=content_id
        )
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'status': 'liked', 'message': 'İçerik beğenildi'})

# General Content Favorite/Unfavorite API
@app.route('/content/<content_type>/<int:content_id>/favorite', methods=['POST'])
@login_required
def favorite_content(content_type, content_id):
    # Validate content type
    valid_types = ['artwork', 'blog_post', 'artist', 'movement']
    if content_type not in valid_types:
        return jsonify({'error': 'Invalid content type'}), 400
    
    existing_favorite = ContentFavorite.query.filter_by(
        user_id=current_user.id, 
        content_type=content_type, 
        content_id=content_id
    ).first()
    
    if existing_favorite:
        db.session.delete(existing_favorite)
        db.session.commit()
        return jsonify({'status': 'unfavorited', 'message': 'Favorilerden çıkarıldı'})
    else:
        new_favorite = ContentFavorite(
            user_id=current_user.id, 
            content_type=content_type, 
            content_id=content_id
        )
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify({'status': 'favorited', 'message': 'Favorilere eklendi'})

# Legacy artwork endpoints for backward compatibility
@app.route('/artwork/<int:artwork_id>/like', methods=['POST'])
@login_required
def like_artwork(artwork_id):
    return like_content('artwork', artwork_id)

@app.route('/artwork/<int:artwork_id>/favorite', methods=['POST'])
@login_required
def favorite_artwork(artwork_id):
    return favorite_content('artwork', artwork_id)

# Blog oluşturma route'u (Evrim Ağacı benzeri)
@app.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_blog_post():
    if request.method == 'GET':
        form = BlogPostForm()
        # Kategori seçeneklerini dinamik olarak yükle
        categories = BlogCategory.query.all()
        form.category.choices = [(cat.id, cat.name) for cat in categories]
        return render_template('create_blog_post.html', form=form, title='Yazı Oluştur')
    
    # POST işlemi
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        post_type = request.form.get('post_type', 'blog')
        category_id = request.form.get('category')
        summary = request.form.get('summary', '')
        
        if not title or not content:
            flash('Başlık ve içerik gereklidir.', 'danger')
            return redirect(url_for('create_blog_post'))
        
        # Quill HTML içeriğini işle
        html_content = content  # Quill zaten HTML formatında veri gönderir
        
        # Yeni blog yazısı oluştur
        new_post = BlogPost(
            title=title,
            content=html_content,
            user_id=current_user.id,
            post_type=post_type,
            category_id=category_id if category_id else None,
            summary=summary,
            status='beklemede'  # Admin onayı gerekiyor
        )
        
        # Kapak görseli varsa kaydet
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = save_picture(file)
                    new_post.image_file = filename
        
        db.session.add(new_post)
        db.session.commit()
        
        flash('İçeriğiniz başarıyla oluşturuldu ve admin onayına gönderildi!', 'success')
        return redirect(url_for('blog_list_page'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Bir hata oluştu: {str(e)}', 'danger')
        return redirect(url_for('create_blog_post'))

def convert_editorjs_to_html(data):
    """EditorJS JSON verisini HTML'e dönüştürür"""
    html_content = ''
    
    for block in data.get('blocks', []):
        block_type = block.get('type')
        block_data = block.get('data', {})
        
        if block_type == 'header':
            level = block_data.get('level', 2)
            text = block_data.get('text', '')
            html_content += f'<h{level}>{text}</h{level}>'
            
        elif block_type == 'paragraph':
            text = block_data.get('text', '')
            html_content += f'<p>{text}</p>'
            
        elif block_type == 'list':
            items = block_data.get('items', [])
            list_type = 'ol' if block_data.get('style') == 'ordered' else 'ul'
            html_content += f'<{list_type}>'
            for item in items:
                html_content += f'<li>{item}</li>'
            html_content += f'</{list_type}>'
            
        elif block_type == 'image':
            file_data = block_data.get('file', {})
            url = file_data.get('url', '')
            caption = block_data.get('caption', '')
            html_content += f'<figure><img src="{url}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'
            
        elif block_type == 'quote':
            text = block_data.get('text', '')
            caption = block_data.get('caption', '')
            html_content += f'<blockquote><p>{text}</p><cite>{caption}</cite></blockquote>'
            
        elif block_type == 'delimiter':
            html_content += '<hr>'
            
        elif block_type == 'table':
            content = block_data.get('content', [])
            html_content += '<table>'
            for row_index, row in enumerate(content):
                html_content += '<tr>'
                for cell in row:
                    tag = 'th' if row_index == 0 else 'td'
                    html_content += f'<{tag}>{cell}</{tag}>'
                html_content += '</tr>'
            html_content += '</table>'
            
        elif block_type == 'warning':
            title = block_data.get('title', '')
            message = block_data.get('message', '')
            html_content += f'<div class="warning"><h4>{title}</h4><p>{message}</p></div>'
            
    return html_content

# Normal kullanıcılar için içerik ekleme route'ları
@app.route('/add_artwork', methods=['GET', 'POST'])
@login_required
def add_artwork_user():
    form = ArtworkForm()
    if form.validate_on_submit():
        artwork = Artwork(
            title=form.title.data,
            artist=form.artist.data,
            description=form.description.data,
            period=form.period.data,
            technique=form.technique.data,
            dimensions=form.dimensions.data,
            location=form.location.data,
            created_by=current_user.id
        )
        
        if form.image_file.data:
            picture_file = save_artwork_picture(form.image_file.data)
            artwork.image_url = picture_file
        elif form.image_url.data:
            artwork.image_url = form.image_url.data
            
        db.session.add(artwork)
        db.session.commit()
        flash('Sanat eseri başarıyla eklendi!', 'success')
        return redirect(url_for('random_artwork_page'))
        
    return render_template('add_artwork_user.html', form=form, title='Sanat Eseri Ekle')

@app.route('/add_artist', methods=['GET', 'POST'])
@login_required
def add_artist_user():
    if request.method == 'POST':
        name = request.form.get('name')
        birth_year = request.form.get('birth_year')
        death_year = request.form.get('death_year')
        nationality = request.form.get('nationality')
        biography = request.form.get('biography')
        style = request.form.get('style')
        
        # Resim yükleme işlemi
        image_file = 'default_artist.jpg'
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    image_file = save_picture(file)
        
        artist = Artist(
            name=name,
            period=f"{birth_year}-{death_year}" if birth_year and death_year else birth_year or death_year,
            bio=biography,
            image_file=image_file
        )
        
        db.session.add(artist)
        db.session.commit()
        flash('Sanatçı başarıyla eklendi!', 'success')
        return redirect(url_for('artists_page'))
        
    return render_template('add_artist_user.html', title='Sanatçı Ekle')

@app.route('/add_museum', methods=['GET', 'POST'])
@login_required
def add_museum_user():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        description = request.form.get('description')
        website = request.form.get('website')
        
        # Resim yükleme işlemi
        image_file = 'default_museum.jpg'
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    image_file = save_picture(file)
        
        museum = VirtualMuseum(
            name=name,
            city=location.split(',')[0] if location else None,
            country=location.split(',')[1].strip() if location and ',' in location else None,
            description=description,
            tour_url=website or 'https://example.com',
            image_file=image_file
        )
        
        db.session.add(museum)
        db.session.commit()
        flash('Müze başarıyla eklendi!', 'success')
        return redirect(url_for('museums_page'))
        
    return render_template('add_museum_user.html', title='Müze Ekle')

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    """TinyMCE için resim yükleme endpoint'i"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = save_picture(file)
            return jsonify({
                'location': url_for('static', filename=f'uploads/{filename}', _external=True)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/add_virtual_museum', methods=['GET', 'POST'])
@login_required
def add_virtual_museum_user():
    if request.method == 'POST':
        name = request.form.get('name')
        city = request.form.get('city')
        country = request.form.get('country')
        description = request.form.get('description')
        tour_url = request.form.get('tour_url')
        
        museum = VirtualMuseum(
            name=name,
            city=city,
            country=country,
            description=description,
            tour_url=tour_url,
            image_file='default_museum.jpg'
        )
        
        db.session.add(museum)
        db.session.commit()
        flash('Sanal müze başarıyla eklendi!', 'success')
        return redirect(url_for('museums_page'))
        
    return render_template('add_virtual_museum_user.html', title='Sanal Müze Ekle')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_categories()
    app.run(debug=True)
