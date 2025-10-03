from flask import request, jsonify, Blueprint, make_response, session
from flask_wtf.csrf import generate_csrf
from flask_login import login_required, login_user, logout_user, current_user
from extensions import db, limiter, csrf
import bleach
import os
from .models import Users

auth_bp = Blueprint('authentication', __name__)

# Load the environment from system environment variable or default to 'development'
env = os.environ.get('FLASK_ENV', 'development')

# Register Route
@auth_bp.route('/register', methods=['POST'])
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
@auth_bp.route('/login', methods=['GET', 'OPTIONS', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])  # Limit only POST requests, not GET or OPTIONS
def login():
    print(f"Request Content-Type: {request.headers.get('Content-Type')}")

    if request.method == 'OPTIONS':
        # Handle the preflight OPTIONS request
        response = make_response()
        print("Handling OPTIONS preflight")
        print(f"Request Headers: {request.headers}")

        # Dynamically set Access-Control-Allow-Origin
        origin = request.headers.get("Origin")
        if env == "production" and origin == "https://jat-frontend.fly.dev":
            response.headers.add("Access-Control-Allow-Origin", "https://jat-frontend.fly.dev")
        elif env == "development" and origin == "http://localhost:3000":
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        else:
            return jsonify({"error": "Origin not allowed"}), 403  # Block other origins

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
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return '', 204  # No content to return, just a successful response

@csrf.exempt
@auth_bp.route('/api/user-details', methods=['GET'])
@login_required
def get_user_details_api():
    # Log the session and current_user details for debugging
    print(f"Session content: {dict(session)}")  # Log session content (use dict() for safe printing)
    print(f"Is user authenticated: {current_user.is_authenticated}")  # Check if the user is authenticated
    print(f"Current user: {current_user}")  # Log the current_user object

    if current_user.is_authenticated:
        # Return user details if authenticated
        user_details = {
            "nickname": current_user.nickname,
            "email": current_user.email
        }
        print(f"User details: {user_details}")
        return jsonify(user_details), 200
    else:
        # Return an error if not authenticated
        print("User is not authenticated.")
        return jsonify({"error": "User not authenticated"}), 401

@auth_bp.route('/api/get-csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()  # Generate CSRF token
    return jsonify({'csrf_token': token})
