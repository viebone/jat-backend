from extensions import db
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

# Initialize bcrypt instance
bcrypt = Bcrypt()

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relationship to JobListing
    jobs = db.relationship('JobListing', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
