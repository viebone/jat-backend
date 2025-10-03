from extensions import db
from datetime import datetime

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
