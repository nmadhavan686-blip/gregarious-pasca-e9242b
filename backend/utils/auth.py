from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, jsonify

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_admin = session.get('admin_logged_in')
        role = session.get('user_role', 'customer')
        if not is_admin and role not in ['owner', 'admin']:
            return jsonify({'error': 'Forbidden. Owner/Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    return admin_required(f)
