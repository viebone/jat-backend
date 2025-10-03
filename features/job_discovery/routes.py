from flask import request, jsonify, Blueprint
from flask_login import login_required, current_user
from extensions import db
from .models import JobListing
from ..job_organization.models import Note, Document
import bleach
import os
from werkzeug.utils import secure_filename

job_discovery_bp = Blueprint('job_discovery', __name__)

# Path to store uploaded documents
UPLOAD_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API to add job with document upload handling
@job_discovery_bp.route('/api/jobs', methods=['POST'])
@login_required  # This ensures only logged-in users can add a job
def add_job_api():
    # Check if the request contains form data
    if 'title' not in request.form:
        return jsonify({'error': 'No job data provided'}), 400

    # Extract job data from the form
    # Sanitize job data
    title = bleach.clean(request.form['title'].strip())
    company = bleach.clean(request.form['company'].strip())
    job_post_link = bleach.clean(request.form.get('job_post_link', '').strip())
    salary = request.form.get('salary', None)  # Assuming salary is a number, no need for bleach
    location_type = bleach.clean(request.form.get('location_type', '').strip())
    job_type = bleach.clean(request.form.get('job_type', '').strip())
    status = bleach.clean(request.form.get('status', '').strip())
    job_description = bleach.clean(request.form.get('job_description', '').strip())

    # Handle notes (which are sent as a JSON string)
    notes = request.form.get('notes', '[]')
    notes = eval(notes)  # Convert JSON string back to list

    # Create a new job listing
    new_job = JobListing(
        job_title=title,
        company=company,
        job_post_link=job_post_link,
        salary=salary,
        location_type=location_type,
        job_type=job_type,
        status=status,
        job_description=job_description,
        user_id=current_user.id  # Assign job to the current user
    )
    db.session.add(new_job)
    db.session.commit()

    # Add notes if any
    for note in notes:
        new_note = Note(
            job_id=new_job.id,
            stage=note['stage'],
            note_text=note['note_text']
        )
        db.session.add(new_note)

    # Handle document uploads
    if 'documents[]' in request.files:
        files = request.files.getlist('documents[]')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))  # Save the file
                new_document = Document(
                    job_id=new_job.id,
                    document_name=filename,
                    document_url=os.path.join('uploads', filename),
                    stage=request.form.get('stage', 'Saved')  # Optionally handle the stage
                )
                db.session.add(new_document)

    db.session.commit()
    return jsonify({'message': 'Job added successfully', 'job_id': new_job.id})
