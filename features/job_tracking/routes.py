from flask import request, jsonify, Blueprint
from flask_login import login_required, current_user
from extensions import db
from ..job_discovery.models import JobListing
import bleach

job_tracking_bp = Blueprint('job_tracking', __name__)

# API to get jobs with filters
@job_tracking_bp.route('/api/jobs', methods=['GET'])
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
