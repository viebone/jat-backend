from flask import jsonify, Blueprint
from flask_login import login_required
from extensions import db
from ..job_discovery.models import JobListing
import os

job_outcomes_bp = Blueprint('job_outcomes', __name__)

# API to delete a job
@job_outcomes_bp.route('/api/jobs/<int:job_id>', methods=['DELETE'])
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
