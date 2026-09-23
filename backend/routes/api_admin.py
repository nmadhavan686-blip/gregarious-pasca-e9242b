import os
import uuid
import re
from pathlib import Path
from flask import Blueprint, request, jsonify, session
from backend.database import get_db
from backend.config import Config
from backend.utils.auth import admin_required, verify_password, hash_password
from backend.utils.helpers import slugify, allowed_file, optimize_and_save_image, format_inr

api_admin = Blueprint('api_admin', __name__)

@api_admin.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'error': 'Username/Email and password are required'}), 400
        
    clean_user = username.lower()
    clean_digits = re.sub(r'\D', '', username)
    short_phone = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits

    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Check users table for owner or admin accounts
        cursor.execute("""
            SELECT * FROM users 
            WHERE (LOWER(email) = ? 
               OR phone = ? 
               OR phone = ? 
               OR (length(phone) >= 10 AND substr(phone, -10) = ?))
              AND role IN ('owner', 'admin')
        """, (clean_user, username, clean_digits, short_phone))
        user = cursor.fetchone()
        
        if user and verify_password(user['password_hash'], password):
            session.permanent = True
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session['admin_logged_in'] = True
            session['admin_username'] = user['email']
            
            user_data = {
                'id': user['id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'phone': user['phone'] or '',
                'auth_provider': user.get('auth_provider', 'local'),
                'role': user['role'],
                'avatar_url': user.get('avatar_url', '') or ''
            }
            return jsonify({'success': True, 'user': user_data, 'message': 'Owner authenticated successfully'})
            
        # 2. Check legacy admins table or env config fallback
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        
        if (not admin and username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD) or \
           (admin and verify_password(admin['password_hash'], password)):
            session.permanent = True
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['user_role'] = 'owner'
            return jsonify({'success': True, 'message': 'Admin authenticated successfully'})
            
        return jsonify({'error': 'Invalid owner or admin credentials'}), 401

@api_admin.route('/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@api_admin.route('/check-auth', methods=['GET'])
def check_auth():
    admin_logged = session.get('admin_logged_in', False)
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if admin_logged or (user_id and user_role in ['owner', 'admin']):
        return jsonify({
            'authenticated': True,
            'username': session.get('admin_username') or session.get('user_name') or session.get('user_email', ''),
            'user': {
                'id': user_id,
                'email': session.get('user_email', ''),
                'role': user_role or 'owner'
            }
        }), 200
    
    return jsonify({'authenticated': False}), 401

@api_admin.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_data():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM products")
        total_products = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as available FROM products WHERE status = 'AVAILABLE'")
        available_products = cursor.fetchone()['available']
        
        cursor.execute("SELECT COUNT(*) as sold FROM products WHERE status = 'SOLD'")
        sold_products = cursor.fetchone()['sold']
        
        cursor.execute("SELECT COUNT(*) as featured FROM products WHERE featured = 1")
        featured_products = cursor.fetchone()['featured']
        
        cursor.execute("SELECT COUNT(*) as total FROM whatsapp_enquiries")
        total_enquiries = cursor.fetchone()['total']
        
        # Recent Enquiries
        cursor.execute("""
            SELECT e.*, p.product_id as code, u.full_name as user_name
            FROM whatsapp_enquiries e 
            LEFT JOIN products p ON e.product_id = p.id 
            LEFT JOIN users u ON e.user_id = u.id
            ORDER BY e.created_at DESC LIMIT 10
        """)
        recent_enquiries = cursor.fetchall()
        for e in recent_enquiries:
            e['product_price_formatted'] = format_inr(e['product_price']) if e['product_price'] else 'N/A'
            
        # Recent Products
        cursor.execute("SELECT * FROM products ORDER BY created_at DESC LIMIT 5")
        recent_products = cursor.fetchall()
        for p in recent_products:
            p['price_formatted'] = format_inr(p['price'])
            cursor.execute("SELECT image_url FROM product_images WHERE product_id = ? ORDER BY is_primary DESC LIMIT 1", (p['id'],))
            img = cursor.fetchone()
            p['primary_image'] = img['image_url'] if img else '/assets/images/placeholder.jpg'
            
        return jsonify({
            'total_products': total_products,
            'available_products': available_products,
            'sold_products': sold_products,
            'featured_products': featured_products,
            'total_enquiries': total_enquiries,
            'recent_enquiries': recent_enquiries,
            'recent_products': recent_products
        })

# Brand Management Admin Endpoints
@api_admin.route('/brands', methods=['GET'])
@admin_required
def get_admin_brands():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands ORDER BY display_order ASC, name ASC")
        brands = cursor.fetchall()
        return jsonify({'brands': brands, 'count': len(brands)})

@api_admin.route('/brands', methods=['POST'])
@admin_required
def create_brand():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Brand name is required'}), 400
        
    slug = slugify(name)
    logo_icon = data.get('logo_icon', '📱').strip()
    description = data.get('description', f'Explore second-hand {name} smartphones.').strip()
    is_active = int(data.get('is_active', 1))
    display_order = int(data.get('display_order', 0))
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM brands WHERE LOWER(name) = LOWER(?) OR slug = ?", (name, slug))
        if cursor.fetchone():
            return jsonify({'error': f'Brand {name} already exists'}), 400
            
        cursor.execute("""
            INSERT INTO brands (name, slug, logo_icon, description, is_active, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, slug, logo_icon, description, is_active, display_order))
        
        return jsonify({'success': True, 'id': cursor.lastrowid, 'message': 'Brand created successfully'})

@api_admin.route('/brands/<int:id>', methods=['PUT'])
@admin_required
def update_brand(id):
    data = request.get_json() or {}
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands WHERE id = ?", (id,))
        brand = cursor.fetchone()
        if not brand:
            return jsonify({'error': 'Brand not found'}), 404
            
        name = data.get('name', brand['name']).strip()
        slug = slugify(name)
        logo_icon = data.get('logo_icon', brand['logo_icon']).strip()
        description = data.get('description', brand['description']).strip()
        is_active = int(data.get('is_active', brand['is_active']))
        display_order = int(data.get('display_order', brand['display_order']))
        
        cursor.execute("""
            UPDATE brands SET
                name = ?, slug = ?, logo_icon = ?, description = ?,
                is_active = ?, display_order = ?
            WHERE id = ?
        """, (name, slug, logo_icon, description, is_active, display_order, id))
        
        return jsonify({'success': True, 'message': 'Brand updated successfully'})

@api_admin.route('/brands/<int:id>', methods=['DELETE'])
@admin_required
def delete_brand(id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM brands WHERE id = ?", (id,))
        return jsonify({'success': True, 'message': 'Brand deleted successfully'})

# Inventory Management Admin Endpoints
@api_admin.route('/products', methods=['GET'])
@admin_required
def get_admin_products():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if status:
        query += " AND LOWER(status) = LOWER(?)"
        params.append(status)
    if search:
        query += " AND (LOWER(brand) LIKE ? OR LOWER(model) LIKE ? OR LOWER(product_id) LIKE ?)"
        term = f"%{search.lower()}%"
        params.extend([term, term, term])
        
    query += " ORDER BY created_at DESC"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        for p in products:
            cursor.execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY is_primary DESC, display_order ASC", (p['id'],))
            p['images'] = cursor.fetchall()
            p['primary_image'] = p['images'][0]['image_url'] if p['images'] else '/assets/images/placeholder.jpg'
            p['price_formatted'] = format_inr(p['price'])
            
        return jsonify({'products': products, 'count': len(products)})

@api_admin.route('/products', methods=['POST'])
@admin_required
def create_product():
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    
    brand = data.get('brand', '').strip()
    model = data.get('model', '').strip()
    price = data.get('price')
    storage = data.get('storage', '').strip()
    condition = data.get('condition', '').strip()
    
    if not brand or not model or not price or not storage or not condition:
        return jsonify({'error': 'Brand, Model, Price, Storage and Condition are required'}), 400
        
    price = int(price)
    mrp = int(data.get('mrp', 0)) if data.get('mrp') else 0
    
    brand_id = None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM brands WHERE LOWER(name) = LOWER(?)", (brand,))
        b_row = cursor.fetchone()
        if b_row:
            brand_id = b_row['id']
            
    product_id = data.get('product_id', '').strip()
    if not product_id:
        brand_code = brand[:3].upper()
        model_code = re.sub(r'\D', '', model) or '001'
        rand_str = uuid.uuid4().hex[:4].upper()
        product_id = f"C2T-{brand_code}{model_code}-{rand_str}"
        
    base_slug = slugify(f"{brand}-{model}-{storage}-{product_id}")
    slug = base_slug
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM products WHERE UPPER(product_id) = UPPER(?)", (product_id,))
        if cursor.fetchone():
            return jsonify({'error': f'Product ID {product_id} already exists'}), 400
            
        cursor.execute("""
            INSERT INTO products (
                product_id, slug, brand, brand_id, model, price, mrp, storage, ram, colour,
                condition, battery_health, network, sim_type, warranty, accessories,
                box_included, charger_included, purchase_date, description, specifications,
                status, featured, badge, display_condition, body_condition, camera_condition,
                battery_condition, speaker_condition, mic_condition, charging_port_condition,
                face_id_condition, network_condition, wifi_condition, bluetooth_condition,
                buttons_condition, repairs, repair_details
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?
            )
        """, (
            product_id, slug, brand, brand_id, model, price, mrp, storage,
            data.get('ram', ''), data.get('colour', ''), condition,
            data.get('battery_health', ''), data.get('network', '5G'),
            data.get('sim_type', 'Dual SIM'), data.get('warranty', '3 Months C2T Warranty'),
            data.get('accessories', ''), int(data.get('box_included', 1)), int(data.get('charger_included', 1)),
            data.get('purchase_date', ''), data.get('description', ''), data.get('specifications', ''),
            data.get('status', 'AVAILABLE'), int(data.get('featured', 0)), data.get('badge', ''),
            data.get('display_condition', 'Flawless'), data.get('body_condition', 'Minor micro-scratches'),
            data.get('camera_condition', 'Clean, full functionality'), data.get('battery_condition', 'Original Battery'),
            data.get('speaker_condition', 'Loud and clear'), data.get('mic_condition', 'Tested & working'),
            data.get('charging_port_condition', 'Clean & tight fit'), data.get('face_id_condition', 'Working perfectly'),
            data.get('network_condition', 'All Indian SIMs tested'), data.get('wifi_condition', 'Tested & fast'),
            data.get('bluetooth_condition', 'Tested & working'), data.get('buttons_condition', 'All buttons tactile & working'),
            data.get('repairs', 'No major repairs'), data.get('repair_details', '')
        ))
        
        new_id = cursor.lastrowid
        
        if 'images' in request.files:
            files = request.files.getlist('images')
            for idx, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = f"prod_{new_id}_{idx}_{uuid.uuid4().hex[:6]}.jpg"
                    target_path = Config.UPLOADS_DIR / filename
                    optimize_and_save_image(file, target_path)
                    image_url = f"/uploads/products/{filename}"
                    is_primary = 1 if idx == 0 else 0
                    cursor.execute("""
                        INSERT INTO product_images (product_id, image_url, is_primary, display_order)
                        VALUES (?, ?, ?, ?)
                    """, (new_id, image_url, is_primary, idx))
                    
        return jsonify({'success': True, 'id': new_id, 'product_id': product_id, 'message': 'Product created successfully'})

@api_admin.route('/products/<int:id>', methods=['PUT'])
@admin_required
def update_product(id):
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (id,))
        prod = cursor.fetchone()
        if not prod:
            return jsonify({'error': 'Product not found'}), 404
            
        brand = data.get('brand', prod['brand']).strip()
        model = data.get('model', prod['model']).strip()
        price = int(data.get('price', prod['price']))
        mrp = int(data.get('mrp', prod['mrp'])) if data.get('mrp') is not None else prod['mrp']
        storage = data.get('storage', prod['storage']).strip()
        condition = data.get('condition', prod['condition']).strip()
        
        cursor.execute("SELECT id FROM brands WHERE LOWER(name) = LOWER(?)", (brand,))
        b_row = cursor.fetchone()
        brand_id = b_row['id'] if b_row else prod['brand_id']
        
        cursor.execute("""
            UPDATE products SET
                brand=?, brand_id=?, model=?, price=?, mrp=?, storage=?, ram=?, colour=?,
                condition=?, battery_health=?, network=?, sim_type=?, warranty=?,
                accessories=?, box_included=?, charger_included=?, purchase_date=?,
                description=?, specifications=?, status=?, featured=?, badge=?,
                display_condition=?, body_condition=?, camera_condition=?, battery_condition=?,
                speaker_condition=?, mic_condition=?, charging_port_condition=?, face_id_condition=?,
                network_condition=?, wifi_condition=?, bluetooth_condition=?, buttons_condition=?,
                repairs=?, repair_details=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            brand, brand_id, model, price, mrp, storage, data.get('ram', prod['ram']), data.get('colour', prod['colour']),
            condition, data.get('battery_health', prod['battery_health']), data.get('network', prod['network']),
            data.get('sim_type', prod['sim_type']), data.get('warranty', prod['warranty']),
            data.get('accessories', prod['accessories']), int(data.get('box_included', prod['box_included'])),
            int(data.get('charger_included', prod['charger_included'])), data.get('purchase_date', prod['purchase_date']),
            data.get('description', prod['description']), data.get('specifications', prod['specifications']),
            data.get('status', prod['status']), int(data.get('featured', prod['featured'])), data.get('badge', prod['badge']),
            data.get('display_condition', prod['display_condition']), data.get('body_condition', prod['body_condition']),
            data.get('camera_condition', prod['camera_condition']), data.get('battery_condition', prod['battery_condition']),
            data.get('speaker_condition', prod['speaker_condition']), data.get('mic_condition', prod['mic_condition']),
            data.get('charging_port_condition', prod['charging_port_condition']), data.get('face_id_condition', prod['face_id_condition']),
            data.get('network_condition', prod['network_condition']), data.get('wifi_condition', prod['wifi_condition']),
            data.get('bluetooth_condition', prod['bluetooth_condition']), data.get('buttons_condition', prod['buttons_condition']),
            data.get('repairs', prod['repairs']), data.get('repair_details', prod['repair_details']),
            id
        ))
        
        if 'images' in request.files:
            files = request.files.getlist('images')
            cursor.execute("SELECT COUNT(*) as cnt FROM product_images WHERE product_id = ?", (id,))
            existing_cnt = cursor.fetchone()['cnt']
            
            for idx, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = f"prod_{id}_{existing_cnt + idx}_{uuid.uuid4().hex[:6]}.jpg"
                    target_path = Config.UPLOADS_DIR / filename
                    optimize_and_save_image(file, target_path)
                    image_url = f"/uploads/products/{filename}"
                    is_primary = 1 if (existing_cnt == 0 and idx == 0) else 0
                    cursor.execute("""
                        INSERT INTO product_images (product_id, image_url, is_primary, display_order)
                        VALUES (?, ?, ?, ?)
                    """, (id, image_url, is_primary, existing_cnt + idx))
                    
        return jsonify({'success': True, 'message': 'Product updated successfully'})

@api_admin.route('/products/<int:id>/status', methods=['PUT'])
@admin_required
def update_product_status(id):
    data = request.get_json() or {}
    new_status = data.get('status', '').upper()
    if new_status not in ['AVAILABLE', 'SOLD']:
        return jsonify({'error': 'Status must be AVAILABLE or SOLD'}), 400
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, id))
        return jsonify({'success': True, 'status': new_status, 'message': f'Product marked as {new_status}'})

@api_admin.route('/products/<int:id>', methods=['DELETE'])
@admin_required
def delete_product(id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image_url FROM product_images WHERE product_id = ?", (id,))
        images = cursor.fetchall()
        
        for img in images:
            url = img['image_url']
            if url.startswith('/uploads/products/'):
                filename = url.replace('/uploads/products/', '')
                file_path = Config.UPLOADS_DIR / filename
                if file_path.exists():
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")
                        
        cursor.execute("DELETE FROM products WHERE id = ?", (id,))
        return jsonify({'success': True, 'message': 'Product deleted successfully'})

@api_admin.route('/products/<int:id>/images', methods=['POST'])
@admin_required
def upload_product_images(id):
    if 'images' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400
        
    files = request.files.getlist('images')
    uploaded = []
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM product_images WHERE product_id = ?", (id,))
        existing_cnt = cursor.fetchone()['cnt']
        
        for idx, file in enumerate(files):
            if file and allowed_file(file.filename):
                filename = f"prod_{id}_{existing_cnt + idx}_{uuid.uuid4().hex[:6]}.jpg"
                target_path = Config.UPLOADS_DIR / filename
                optimize_and_save_image(file, target_path)
                image_url = f"/uploads/products/{filename}"
                is_primary = 1 if (existing_cnt == 0 and idx == 0) else 0
                cursor.execute("""
                    INSERT INTO product_images (product_id, image_url, is_primary, display_order)
                    VALUES (?, ?, ?, ?)
                """, (id, image_url, is_primary, existing_cnt + idx))
                uploaded.append({'image_url': image_url, 'is_primary': is_primary})
                
        return jsonify({'success': True, 'uploaded': uploaded, 'message': f'{len(uploaded)} images uploaded'})

@api_admin.route('/images/<int:image_id>', methods=['DELETE'])
@admin_required
def delete_image(image_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_images WHERE id = ?", (image_id,))
        img = cursor.fetchone()
        if not img:
            return jsonify({'error': 'Image not found'}), 404
            
        url = img['image_url']
        if url.startswith('/uploads/products/'):
            filename = url.replace('/uploads/products/', '')
            file_path = Config.UPLOADS_DIR / filename
            if file_path.exists():
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
                    
        cursor.execute("DELETE FROM product_images WHERE id = ?", (image_id,))
        
        if img['is_primary']:
            cursor.execute("SELECT id FROM product_images WHERE product_id = ? ORDER BY display_order ASC LIMIT 1", (img['product_id'],))
            next_img = cursor.fetchone()
            if next_img:
                cursor.execute("UPDATE product_images SET is_primary = 1 WHERE id = ?", (next_img['id'],))
                
        return jsonify({'success': True, 'message': 'Image deleted successfully'})

@api_admin.route('/settings', methods=['PUT'])
@admin_required
def update_settings():
    data = request.get_json() or {}
    owner_whatsapp = data.get('owner_whatsapp', '').strip()
    owner_name = data.get('owner_name', '').strip()
    business_email = data.get('business_email', '').strip()
    instagram_url = data.get('instagram_url', '').strip()
    youtube_url = data.get('youtube_url', '').strip()
    business_address = data.get('business_address', '').strip()
    
    if not owner_whatsapp:
        return jsonify({'error': 'WhatsApp number is required'}), 400
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE site_settings SET
                owner_name = ?,
                owner_whatsapp = ?,
                business_email = ?,
                instagram_url = ?,
                youtube_url = ?,
                business_address = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (owner_name, owner_whatsapp, business_email, instagram_url, youtube_url, business_address))
        return jsonify({'success': True, 'message': 'Site settings updated successfully'})
