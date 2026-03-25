import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from app import app as flask_app
from api.models import db


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['JWT_SECRET_KEY'] = 'test-secret'
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ── Signup tests ──────────────────────────────────────────────────────────────

def test_signup_success(client):
    resp = client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['user']['email'] == 'test@example.com'
    assert 'password' not in data['user']


def test_signup_duplicate_email(client):
    client.post('/api/signup', json={'email': 'dup@example.com', 'password': 'pass'})
    resp = client.post('/api/signup', json={'email': 'dup@example.com', 'password': 'pass'})
    assert resp.status_code == 409


def test_signup_missing_email(client):
    resp = client.post('/api/signup', json={'password': 'pass'})
    assert resp.status_code == 400


def test_signup_missing_password(client):
    resp = client.post('/api/signup', json={'email': 'test@example.com'})
    assert resp.status_code == 400


# ── Login tests ───────────────────────────────────────────────────────────────

def test_login_success(client):
    client.post('/api/signup', json={'email': 'login@example.com', 'password': 'mypassword'})
    resp = client.post('/api/login', json={'email': 'login@example.com', 'password': 'mypassword'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'token' in data
    assert data['user']['email'] == 'login@example.com'


def test_login_wrong_password(client):
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'correct'})
    resp = client.post('/api/login', json={'email': 'user@example.com', 'password': 'wrong'})
    assert resp.status_code == 401


def test_login_nonexistent_email(client):
    resp = client.post('/api/login', json={'email': 'nobody@example.com', 'password': 'pass'})
    assert resp.status_code == 401


def test_login_missing_fields(client):
    resp = client.post('/api/login', json={'email': 'only@example.com'})
    assert resp.status_code == 400


# ── Private route tests ───────────────────────────────────────────────────────

def test_private_with_valid_token(client):
    client.post('/api/signup', json={'email': 'priv@example.com', 'password': 'pass'})
    login_resp = client.post('/api/login', json={'email': 'priv@example.com', 'password': 'pass'})
    token = login_resp.get_json()['token']

    resp = client.get('/api/private', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['user']['email'] == 'priv@example.com'


def test_private_without_token(client):
    resp = client.get('/api/private')
    assert resp.status_code == 401


def test_private_with_invalid_token(client):
    resp = client.get('/api/private', headers={'Authorization': 'Bearer invalidtoken'})
    assert resp.status_code == 422
