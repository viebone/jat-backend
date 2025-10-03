from extensions import db
from datetime import datetime

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
