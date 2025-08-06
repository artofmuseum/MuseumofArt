from app import app, db, User

with app.app_context():
    user = User.query.filter_by(email='yusufbozts@gmail.com').first()
    if user:
        user.role = 'admin'
        db.session.commit()
        print(f"{user.email} artık admin!")
    else:
        print("Kullanıcı bulunamadı.")