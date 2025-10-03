from flask import request, jsonify, Blueprint
from flask_login import login_required
from extensions import db
from ..job_discovery.models import JobListing
from .models import Note, Document
import bleach
import os
from werkzeug.utils import secure_filename

job_organization_bp = Blueprint('job_organization', __name__)

# Path to store uploaded documents
UPLOAD_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Edit job with document upload and deletion
@job_organization_bp.route('/api/jobs/<int:job_id>', methods=['PUT'])
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
