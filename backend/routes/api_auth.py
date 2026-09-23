import re
import json
import base64
from flask import Blueprint, request, jsonify, session
from backend.database import get_db
from backend.utils.auth import hash_password, verify_password

api_auth = Blueprint('api_auth', __name__)

def parse_jwt_unverified(token):
    """Fallback helper to extract payload from a JWT token without external libraries."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += '=' * (4 - rem)
        decoded = base64.b64decode(payload_b64).decode('utf-8')
        return json.loads(decoded)
    except Exception:
        return {}

@api_auth.route('/register', methods=['POST'])
def user_register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    confirm_password = data.get('confirm_password', '').strip()
    
    if not full_name or not email or not phone or not password:
        return jsonify({'error': 'Full Name, Email, Phone Number and Password are required'}), 400
        
    if confirm_password and password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
        
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
    clean_phone = re.sub(r'\D', '', phone)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'An account with this email already exists'}), 400
            
        cursor.execute("SELECT id FROM users WHERE phone = ?", (clean_phone,))
        if cursor.fetchone():
            return jsonify({'error': 'An account with this mobile number already exists'}), 400
            
        pass_hash = hash_password(password)
        
        # Public registrations strictly create CUSTOMER role
        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, auth_provider, role, avatar_url, last_login)
            VALUES (?, ?, ?, ?, 'local', 'customer', '', CURRENT_TIMESTAMP)
        """, (full_name, email, clean_phone, pass_hash))
        
        user_id = cursor.lastrowid
        
        session['user_id'] = user_id
        session['user_name'] = full_name
        session['user_email'] = email
        session['user_role'] = 'customer'
        session['admin_logged_in'] = False
        
        user_data = {
            'id': user_id,
            'full_name': full_name,
            'email': email,
            'phone': clean_phone,
            'auth_provider': 'local',
            'role': 'customer',
            'avatar_url': ''
        }
        
        return jsonify({'success': True, 'user': user_data, 'message': 'Account created successfully'})

@api_auth.route('/login', methods=['POST'])
def user_login():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip().lower() or data.get('email_or_phone', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not identifier or not password:
        return jsonify({'error': 'Email / Phone and Password are required'}), 400
        
    clean_digits = re.sub(r'\D', '', identifier)
    short_phone = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users 
            WHERE LOWER(email) = ? 
               OR phone = ? 
               OR phone = ? 
               OR (length(phone) >= 10 AND substr(phone, -10) = ?)
        """, (identifier, identifier, clean_digits, short_phone))
        user = cursor.fetchone()
        
        if not user or not verify_password(user['password_hash'], password):
            return jsonify({'error': 'Invalid email/phone or password'}), 401
            
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
        
        user_role = user.get('role') or 'customer'
        
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['user_email'] = user['email']
        session['user_role'] = user_role
        
        if user_role in ['owner', 'admin']:
            session['admin_logged_in'] = True
            session['admin_username'] = user['email']
        else:
            session['admin_logged_in'] = False
        
        user_data = {
            'id': user['id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'phone': user['phone'] or '',
            'auth_provider': user.get('auth_provider', 'local'),
            'role': user_role,
            'avatar_url': user.get('avatar_url', '') or ''
        }
        
        return jsonify({'success': True, 'user': user_data, 'message': 'Logged in successfully'})

@api_auth.route('/google', methods=['POST'])
def google_auth():
    data = request.get_json() or {}
    credential = data.get('credential')
    
    email = data.get('email', '').strip().lower()
    full_name = data.get('full_name', '').strip() or data.get('name', '').strip()
    avatar_url = data.get('avatar_url', '').strip() or data.get('picture', '').strip()
    
    if credential:
        jwt_payload = parse_jwt_unverified(credential)
        if jwt_payload:
            email = jwt_payload.get('email', email).strip().lower()
            full_name = jwt_payload.get('name', full_name).strip()
            avatar_url = jwt_payload.get('picture', avatar_url).strip()
            
    if not email:
        return jsonify({'error': 'Failed to obtain email from Google authentication'}), 400
        
    if not full_name:
        full_name = email.split('@')[0].capitalize()
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            user_id = user['id']
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP,
                    avatar_url = COALESCE(NULLIF(?, ''), avatar_url),
                    auth_provider = CASE WHEN auth_provider = 'local' THEN auth_provider ELSE 'google' END
                WHERE id = ?
            """, (avatar_url, user_id))
            phone = user['phone'] or ''
            auth_prov = user.get('auth_provider') or 'google'
            user_role = user.get('role') or 'customer'
            existing_avatar = user.get('avatar_url') or avatar_url
        else:
            dummy_hash = hash_password('OAUTH_ACCOUNT_NO_PASSWORD_' + email)
            cursor.execute("""
                INSERT INTO users (full_name, email, phone, password_hash, auth_provider, role, avatar_url, last_login)
                VALUES (?, ?, '', ?, 'google', 'customer', ?, CURRENT_TIMESTAMP)
            """, (full_name, email, dummy_hash, avatar_url))
            user_id = cursor.lastrowid
            phone = ''
            auth_prov = 'google'
            user_role = 'customer'
            existing_avatar = avatar_url
            
        session['user_id'] = user_id
        session['user_name'] = full_name
        session['user_email'] = email
        session['user_role'] = user_role
        
        if user_role in ['owner', 'admin']:
            session['admin_logged_in'] = True
            session['admin_username'] = email
        else:
            session['admin_logged_in'] = False
        
        user_data = {
            'id': user_id,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'auth_provider': auth_prov,
            'role': user_role,
            'avatar_url': existing_avatar
        }
        
        return jsonify({'success': True, 'user': user_data, 'message': 'Google authentication successful'})

@api_auth.route('/apple', methods=['POST'])
def apple_auth():
    data = request.get_json() or {}
    id_token = data.get('id_token')
    
    email = data.get('email', '').strip().lower()
    full_name = data.get('full_name', '').strip() or data.get('name', '').strip()
    
    if id_token:
        jwt_payload = parse_jwt_unverified(id_token)
        if jwt_payload:
            email = jwt_payload.get('email', email).strip().lower()
            
    if not email:
        return jsonify({'error': 'Failed to obtain email from Apple authentication'}), 400
        
    if not full_name:
        full_name = email.split('@')[0].capitalize()
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            user_id = user['id']
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            phone = user['phone'] or ''
            auth_prov = user.get('auth_provider') or 'apple'
            user_role = user.get('role') or 'customer'
            avatar_url = user.get('avatar_url') or ''
        else:
            dummy_hash = hash_password('OAUTH_ACCOUNT_NO_PASSWORD_' + email)
            cursor.execute("""
                INSERT INTO users (full_name, email, phone, password_hash, auth_provider, role, avatar_url, last_login)
                VALUES (?, ?, '', ?, 'apple', 'customer', '', CURRENT_TIMESTAMP)
            """, (full_name, email, dummy_hash))
            user_id = cursor.lastrowid
            phone = ''
            auth_prov = 'apple'
            user_role = 'customer'
            avatar_url = ''
            
        session['user_id'] = user_id
        session['user_name'] = full_name
        session['user_email'] = email
        session['user_role'] = user_role
        
        if user_role in ['owner', 'admin']:
            session['admin_logged_in'] = True
            session['admin_username'] = email
        else:
            session['admin_logged_in'] = False
        
        user_data = {
            'id': user_id,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'auth_provider': auth_prov,
            'role': user_role,
            'avatar_url': avatar_url
        }
        
        return jsonify({'success': True, 'user': user_data, 'message': 'Apple authentication successful'})

@api_auth.route('/logout', methods=['POST'])
def user_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@api_auth.route('/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, email, phone, auth_provider, role, avatar_url, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            session.clear()
            return jsonify({'authenticated': False}), 200
            
        if not user.get('phone'):
            user['phone'] = ''
        if not user.get('avatar_url'):
            user['avatar_url'] = ''
        if not user.get('role'):
            user['role'] = 'customer'
            
        session['user_role'] = user['role']
        if user['role'] in ['owner', 'admin']:
            session['admin_logged_in'] = True
            
        return jsonify({'authenticated': True, 'user': user})

@api_auth.route('/user/profile', methods=['GET'])
def get_user_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, email, phone, auth_provider, role, avatar_url, created_at, last_login FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            session.clear()
            return jsonify({'error': 'User not found'}), 404
            
        if not user.get('phone'):
            user['phone'] = ''
        if not user.get('avatar_url'):
            user['avatar_url'] = ''
        if not user.get('role'):
            user['role'] = 'customer'
            
        cursor.execute("""
            SELECT e.*, p.product_id as code, p.brand, p.model, p.price, p.slug
            FROM whatsapp_enquiries e
            LEFT JOIN products p ON e.product_id = p.id
            WHERE e.user_id = ?
            ORDER BY e.created_at DESC
        """, (user_id,))
        enquiries = cursor.fetchall()
        
        return jsonify({'profile': user, 'user': user, 'enquiries': enquiries})

@api_auth.route('/user/profile', methods=['PUT'])
def update_user_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
        
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip().lower()
    
    if not full_name:
        return jsonify({'error': 'Full Name is required'}), 400
        
    clean_phone = re.sub(r'\D', '', phone) if phone else None
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if email and email != user['email']:
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
            if cursor.fetchone():
                return jsonify({'error': 'This email is already in use by another account'}), 400
        else:
            email = user['email']
            
        if clean_phone and clean_phone != (user['phone'] or ''):
            cursor.execute("SELECT id FROM users WHERE phone = ? AND id != ?", (clean_phone, user_id))
            if cursor.fetchone():
                return jsonify({'error': 'This mobile number is already in use by another account'}), 400
                
        cursor.execute("""
            UPDATE users 
            SET full_name = ?, email = ?, phone = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (full_name, email, clean_phone, user_id))
        
        session['user_name'] = full_name
        session['user_email'] = email
        
        cursor.execute("SELECT id, full_name, email, phone, auth_provider, role, avatar_url, created_at FROM users WHERE id = ?", (user_id,))
        updated_user = cursor.fetchone()
        if not updated_user.get('phone'):
            updated_user['phone'] = ''
        if not updated_user.get('avatar_url'):
            updated_user['avatar_url'] = ''
        if not updated_user.get('role'):
            updated_user['role'] = 'customer'
            
        return jsonify({'success': True, 'user': updated_user, 'message': 'Profile updated successfully'})
