from sqlalchemy import text
from extensions import db, limiter, csrf  # Import csrf from extensions
from flask import request, jsonify, Blueprint, current_app, session, make_response
from flask_wtf.csrf import generate_csrf
from flask_bcrypt import Bcrypt
from models import JobListing, Note, Document, Users
import os
from werkzeug.utils import secure_filename
from flask_login import login_required, login_user, logout_user, current_user
import bleach


bcrypt = Bcrypt()
bp = Blueprint('main', __name__)

# Path to store uploaded documents
UPLOAD_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# API to get jobs with filters
@bp.route('/api/jobs', methods=['GET'])
@login_required  # This ensures only logged-in users can add a job
def get_jobs_api():
    status = request.args.get('status')
    job_type = request.args.get('job_type')
    location_type = request.args.get('location_type')
    salary_min = request.args.get('salary_min')
    salary_max = request.args.get('salary_max')
    company = request.args.get('company')
    date_created = request.args.get('date_created')

    # Only query jobs for the current user
    query = JobListing.query.filter_by(user_id=current_user.id)

    if status:
        query = query.filter_by(status=status)
    
    if job_type:
        query = query.filter_by(job_type=job_type)
    
    if location_type:
        query = query.filter_by(location_type=location_type)

    if salary_min:
        query = query.filter(JobListing.salary >= salary_min)

    if salary_max:
        query = query.filter(JobListing.salary <= salary_max)

    if company:
        query = query.filter(JobListing.company.ilike(f'%{company}%'))

    if date_created:
        query = query.filter(JobListing.date_created >= date_created)

    job_listings = query.order_by(JobListing.date_created.desc()).all()

    jobs_list = [{
        'id': job.id,
        'job_title': job.job_title,
        'company': job.company,
        'job_post_link': job.job_post_link,
        'salary': job.salary,
        'location_type': job.location_type,
        'job_type': job.job_type,
        'status': job.status,
        'job_description': job.job_description,
        'notes': [{'id': note.id, 'stage': note.stage, 'note_text': note.note_text, 'date_created': note.date_created} for note in job.notes],
        'documents': [{'id': doc.id, 'stage': doc.stage, 'document_name': doc.document_name, 'document_url': doc.document_url, 'date_uploaded': doc.date_uploaded} for doc in job.documents]
    } for job in job_listings]

    return jsonify(jobs_list)

# API to add job with document upload handling
@bp.route('/api/jobs', methods=['POST'])
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

# Edit job with document upload and deletion
@bp.route('/api/jobs/<int:job_id>', methods=['PUT'])
@login_required  # This ensures only logged-in users can add a job
def update_job(job_id):
    job = JobListing.query.get_or_404(job_id)

    # Check if the request is JSON or form-data
    if request.is_json:
        # If the request is JSON (e.g., from drag-and-drop update)
        job.job_title = bleach.clean(request.json.get('title', job.job_title).strip())
        job.company = bleach.clean(request.json.get('company', job.company).strip())
        job.job_post_link = bleach.clean(request.json.get('job_post_link', job.job_post_link).strip())
        job.salary = request.json.get('salary', job.salary)  # Assuming salary is numeric, no need to bleach
        job.location_type = bleach.clean(request.json.get('location_type', job.location_type).strip())
        job.job_type = bleach.clean(request.json.get('job_type', job.job_type).strip())
        job.status = bleach.clean(request.json.get('status', job.status).strip())
        job.job_description = bleach.clean(request.json.get('job_description', job.job_description).strip())
    else:
        # If the request is form-data (e.g., from the update form)
        job.job_title = bleach.clean(request.form.get('title', job.job_title).strip())
        job.company = bleach.clean(request.form.get('company', job.company).strip())
        job.job_post_link = bleach.clean(request.form.get('job_post_link', job.job_post_link).strip())
        job.salary = request.form.get('salary', job.salary)  # Assuming salary is numeric
        job.location_type = bleach.clean(request.form.get('location_type', job.location_type).strip())
        job.job_type = bleach.clean(request.form.get('job_type', job.job_type).strip())
        job.status = bleach.clean(request.form.get('status', job.status).strip())
        job.job_description = bleach.clean(request.form.get('job_description', job.job_description).strip())

    # Handle notes (add or update)
    notes_data = request.form.to_dict(flat=False)  # Convert form data to a dictionary
    note_keys = [key for key in notes_data if key.startswith('notes')]  # Filter note-related keys

    existing_note_ids = {str(note.id) for note in job.notes}  # Create a set of existing note IDs as strings

    for key in set([key.split('[')[1].split(']')[0] for key in note_keys]):  # Deduplicate note indexes
        note_id = request.form.get(f'notes[{key}][id]', None)
        note_stage = request.form.get(f'notes[{key}][stage]')
        note_text = request.form.get(f'notes[{key}][note_text]')

        if note_id and note_id in existing_note_ids:  # If the note ID exists and matches an existing note
            existing_note = Note.query.get(note_id)
            if existing_note:
                existing_note.stage = note_stage
                existing_note.note_text = note_text
        elif not note_id:  # Only add new notes if they don't have an ID (this means they are new)
            new_note = Note(
                job_id=job.id,
                stage=note_stage,
                note_text=note_text
            )
            db.session.add(new_note)



    # Handle document uploads
    if 'documents[]' in request.files:
        for document in request.files.getlist('documents[]'):
            if document and allowed_file(document.filename):
                filename = secure_filename(document.filename)
                document_path = os.path.join(UPLOAD_FOLDER, filename)
                document.save(document_path)

                new_document = Document(
                    job_id=job.id,
                    stage=request.form.get('document_stage', 'Saved'),
                    document_name=filename,
                    document_url=document_path
                )
                db.session.add(new_document)

    # Handle document removal
    document_ids_to_remove = request.form.getlist('remove_document_ids[]')
    print(f"Document IDs to remove: {document_ids_to_remove}")

    for document_id in document_ids_to_remove:
        document = Document.query.get(document_id)
        if document:
            try:
                # Remove the document from the file system
                print(f"Removing file: {document.document_url}")
                if os.path.exists(document.document_url):
                    os.remove(document.document_url)
                else:
                    print(f"File {document.document_url} does not exist.")
            except Exception as e:
                print(f"Error removing file: {e}")  # Log error if file doesn't exist or can't be deleted

            # Remove the document entry from the database
            db.session.delete(document)

    # Handle note removal (missing part added)
    remove_note_ids = request.form.getlist('remove_note_ids[]')  # Get note IDs to remove
    for note_id in remove_note_ids:
        note = Note.query.get(note_id)
        if note:
            db.session.delete(note)

    # Commit all changes
    db.session.commit()

    return jsonify({'message': 'Job updated successfully'})



# API to delete a job
@bp.route('/api/jobs/<int:job_id>', methods=['DELETE'])
@login_required  # This ensures only logged-in users can add a job
def delete_job(job_id):
    job = JobListing.query.get_or_404(job_id)

    # Handle associated documents (delete files from filesystem)
    for document in job.documents:
        try:
            if os.path.exists(document.document_url):
                os.remove(document.document_url)  # Remove file from filesystem
            else:
                print(f"File {document.document_url} does not exist.")
        except Exception as e:
            print(f"Error deleting file {document.document_url}: {e}")
        # Delete the document from the database even if file removal fails
        db.session.delete(document)

    # Delete the job
    db.session.delete(job)
    db.session.commit()
    return jsonify({'message': 'Job deleted successfully'})

# Register Route
@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    nickname = bleach.clean(data.get('nickname', '').strip())
    email = bleach.clean(data.get('email', '').strip())
    password = data.get('password').strip()

    if Users.query.filter_by(email=email).first():
        return jsonify({'error': 'User already exists'}), 400

    new_user = Users(nickname=nickname, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    # Automatically log in the user after successful registration
    login_user(new_user)
    return jsonify({'message': 'User registered successfully'}), 201

@csrf.exempt
@bp.route('/login', methods=['GET', 'OPTIONS', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])  # Limit only POST requests, not GET or OPTIONS
def login():
    print(f"Request Content-Type: {request.headers.get('Content-Type')}")

    if request.method == 'OPTIONS':
        # Handle the preflight OPTIONS request
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-CSRFToken")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200  # Ensure 200 OK response for OPTIONS

    # Process the POST login request
    if request.method == 'POST':
        try:
            data = request.get_json()  # Try to extract the JSON data
            print(f"Received request data: {data}")

            if not data or 'email' not in data or 'password' not in data:
                print('Missing email or password in the request')
                return jsonify({'error': 'Email and password are required'}), 400

            email = bleach.clean(data['email'].strip())
            password = data['password'].strip()

            user = Users.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user)
                return jsonify({'message': 'Login successful'}), 200
            else:
                return jsonify({'error': 'Invalid email or password'}), 401

        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({'error': 'An error occurred during login'}), 500

    return jsonify({'error': 'Method not allowed'}), 405


# Logout Route
@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return '', 204  # No content to return, just a successful response

# Get user details API
@bp.route('/api/user-details', methods=['GET'])
@login_required
def get_user_details_api():
    # Return the current user's details, such as their nickname and email
    user_details = {
        "nickname": current_user.nickname,
        "email": current_user.email
    }
    return jsonify(user_details), 200

@bp.route('/api/get-csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()  # Generate CSRF token
    return jsonify({'csrf_token': token})

