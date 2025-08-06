from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired, FileStorage
from wtforms import (
    StringField, PasswordField, SubmitField, BooleanField, 
    SelectField, TextAreaField, RadioField, HiddenField, SelectMultipleField, FloatField, MultipleFileField
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, URL
from wtforms import ValidationError
import re

# Bu dosyada veritabanı modelleri import edilmez.

CULTURAL_CATEGORIES = [
    ('Müze', 'Müze'),
    ('Galeri', 'Galeri'),
    ('Etkinlik', 'Etkinlik'),
    ('Tarihi Mekan', 'Tarihi Mekan'),
    ('Diğer', 'Diğer')
]

class RegistrationForm(FlaskForm):
    first_name = StringField('Ad', validators=[DataRequired(), Length(min=2, max=30)])
    last_name = StringField('Soyad', validators=[DataRequired(), Length(min=2, max=30)])
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Kayıt Ol')

class LoginForm(FlaskForm):
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    remember = BooleanField('Beni Hatırla')
    submit = SubmitField('Giriş Yap')

class EditUserRoleForm(FlaskForm):
    available_roles = [('kullanici', 'Kullanıcı'), ('arastirmaci', 'Araştırmacı'), ('akademisyen', 'Akademisyen'), ('admin', 'Admin')]
    role = SelectField('Kullanıcı Rolü', choices=available_roles, validators=[DataRequired()])
    submit = SubmitField('Rolü Güncelle')

# BlogPostForm GÜNCELLENDİ
class BlogPostForm(FlaskForm):
    title = StringField('Başlık', validators=[DataRequired(), Length(min=5, max=200)])
    # İlişkili sanatçıları seçmek için çoklu seçim alanı
    artists = SelectMultipleField(
        'İlişkili Sanatçılar (Birden fazla seçmek için Ctrl/Cmd tuşuna basılı tutun)',
        coerce=int # Formdan gelen değerleri tamsayıya dönüştürür.
    )
    category = SelectField('Kategori', coerce=int, validators=[DataRequired()])
    post_type = SelectField('Yazı Türü', choices=[
        ('blog', 'Blog Yazısı'),
        ('makale', 'Makale'),
        ('arastirma', 'Araştırma'),
        ('inceleme', 'İnceleme'),
        ('haber', 'Haber'),
        ('roportaj', 'Röportaj'),
        ('kitap_tanitimi', 'Kitap Tanıtımı'),
        ('sergi_haberi', 'Sergi Haberi')
    ], validators=[DataRequired()])
    summary = TextAreaField('Özet', validators=[DataRequired(), Length(max=500)])
    content = TextAreaField('İçerik', validators=[DataRequired()])
    picture = FileField('Kapak Görseli (Opsiyonel)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    ek_gorseller = MultipleFileField('Ek Görseller (Birden fazla seçebilirsiniz)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    submit = SubmitField('Yazıyı Kaydet')

class ArtistForm(FlaskForm):
    movement = SelectField('Sanat Akımı', coerce=int)
    name = StringField('Sanatçı Adı', validators=[DataRequired(), Length(min=2, max=100)])
    period = StringField('Dönem / Yıllar', validators=[DataRequired(), Length(min=2, max=100)])
    bio = TextAreaField('Biyografi (Opsiyonel)')
    picture = FileField('Sanatçı Resmi (Opsiyonel)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    submit = SubmitField('Sanatçıyı Kaydet')

class CommentForm(FlaskForm):
    content = TextAreaField('Yorumunuz', validators=[DataRequired(message="Yorum alanı boş bırakılamaz.")])
    submit = SubmitField('Yorumu Gönder')

class SearchForm(FlaskForm):
    searched = StringField('Aranacak Kelime', validators=[DataRequired()])
    submit = SubmitField('Ara')

class ArtMovementForm(FlaskForm):
    name = StringField('Akım Adı', validators=[DataRequired(), Length(min=3, max=100)])
    period = StringField('Dönem (Örn: 19. Yüzyıl)', validators=[DataRequired()])
    description = TextAreaField('Açıklama', validators=[DataRequired()])
    picture = FileField('Akımı Temsil Eden Resim (Opsiyonel)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    submit = SubmitField('Sanat Akımını Kaydet')

class VirtualMuseumForm(FlaskForm):
    name = StringField('Müze Adı',
                       validators=[DataRequired(message="Müze adı zorunludur."),
                                   Length(min=3, max=150)])
    city = StringField('Şehir (Opsiyonel)')
    country = StringField('Ülke',
                          validators=[DataRequired(message="Ülke alanı zorunludur.")])
    tour_url = StringField('Sanal Tur Linki',
                           validators=[DataRequired(message="Sanal tur linki zorunludur."),
                                       URL(message="Lütfen geçerli bir URL girin.")])
    description = TextAreaField('Açıklama (Opsiyonel)')
    picture = FileField('Müze Resmi (Opsiyonel)',
                        validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    submit = SubmitField('Müzeyi Kaydet')

class NewsletterForm(FlaskForm):
    email = StringField('E-posta Adresi', validators=[DataRequired(), Email()])
    submit = SubmitField('Abone Ol')

class NewsletterSendForm(FlaskForm):
    subject = StringField('Konu', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('İçerik', validators=[DataRequired()])
    submit = SubmitField('Newsletter Gönder')

class EditProfileForm(FlaskForm):
    first_name = StringField('Ad', validators=[DataRequired(), Length(min=2, max=30)])
    last_name = StringField('Soyad', validators=[DataRequired(), Length(min=2, max=30)])
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    profile_image = FileField('Profil Resmi (Opsiyonel)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    submit = SubmitField('Profili Güncelle')

class CulturalPlaceForm(FlaskForm):
    name = StringField('İsim', validators=[DataRequired()])
    description = TextAreaField('Açıklama', validators=[DataRequired()])
    category = SelectField('Kategori', choices=CULTURAL_CATEGORIES, validators=[DataRequired()])
    latitude = FloatField('Enlem', validators=[DataRequired()])
    longitude = FloatField('Boylam', validators=[DataRequired()])
    image = FileField('Görsel')  # eski tekil alan, uyumluluk için
    images = MultipleFileField('Ek Görseller', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Sadece resim dosyası yükleyin!')])

class ArtworkForm(FlaskForm):
    title = StringField('Eser Adı', validators=[DataRequired()])
    artist = StringField('Sanatçı', validators=[DataRequired()])
    year = StringField('Yıl', validators=[DataRequired()])
    period = StringField('Dönem', validators=[DataRequired()])
    medium = StringField('Teknik', validators=[DataRequired()])
    location = StringField('Bulunduğu Yer', validators=[DataRequired()])
    dimensions = StringField('Boyutlar (Opsiyonel)')
    image_url = StringField('Resim URL (Opsiyonel)')
    image_file = FileField('Resim Dosyası', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Sadece resim dosyaları kabul edilir!')
    ])
    description = TextAreaField('Açıklama', validators=[DataRequired()])
    technique = TextAreaField('Teknik Detaylar', validators=[DataRequired()])
    museum = StringField('Müze/Galeri', validators=[DataRequired()])
    facts = TextAreaField('İlginç Bilgiler', validators=[DataRequired()])
    submit = SubmitField('Eser Ekle')
