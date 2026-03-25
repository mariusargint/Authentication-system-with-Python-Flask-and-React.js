"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)


@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():
    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }
    return jsonify(response_body), 200


@api.route('/signup', methods=['POST'])
def signup():
    body = request.get_json()
    if not body:
        raise APIException("Missing request body", status_code=400)

    email = body.get("email")
    password = body.get("password")

    if not email:
        raise APIException("Email is required", status_code=400)
    if not password:
        raise APIException("Password is required", status_code=400)

    if User.query.filter_by(email=email).first():
        raise APIException("Email already registered", status_code=409)

    user = User(email=email, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created successfully", "user": user.serialize()}), 201


@api.route('/login', methods=['POST'])
def login():
    body = request.get_json()
    if not body:
        raise APIException("Missing request body", status_code=400)

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        raise APIException("Email and password are required", status_code=400)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise APIException("Invalid email or password", status_code=401)

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"token": access_token, "user": user.serialize()}), 200


@api.route('/private', methods=['GET'])
@jwt_required()
def private():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        raise APIException("User not found", status_code=404)
    return jsonify({"message": "Access granted", "user": user.serialize()}), 200
