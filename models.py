from extensions import db  # Import db from extensions, not directly from db.py
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import UserMixin


# Initialize bcrypt instance (Ensure this line is at the top level)
bcrypt = Bcrypt()

class JobListing(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    job_post_link = db.Column(db.Text)
    salary = db.Column(db.Numeric(10, 2))
    location_type = db.Column(db.String(50))
    job_type = db.Column(db.String(50))
    status = db.Column(db.String(50))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    job_description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Link to Users table


    # Relationships
    notes = db.relationship('Note', back_populates='job_listing', cascade="all, delete-orphan")
    documents = db.relationship('Document', back_populates='job_listing', cascade="all, delete-orphan")
    user = db.relationship('Users', back_populates='jobs')

    def __repr__(self):
        return f'<Job {self.job_title}>'


class Note(db.Model):
    __tablename__ = 'notes'  # Define the table name explicitly

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    stage = db.Column(db.String(50), nullable=False)
    note_text = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    job_listing = db.relationship('JobListing', back_populates='notes')

class Document(db.Model):
    __tablename__ = 'documents'  # Define the table name explicitly

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    stage = db.Column(db.String(50), nullable=False)
    document_name = db.Column(db.String(255), nullable=False)
    document_url = db.Column(db.String(255), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

    job_listing = db.relationship('JobListing', back_populates='documents')

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