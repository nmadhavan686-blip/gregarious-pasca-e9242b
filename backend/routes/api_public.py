from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.utils.helpers import format_inr, generate_whatsapp_message, build_whatsapp_link

api_public = Blueprint('api_public', __name__)

@api_public.route('/settings', methods=['GET'])
def get_settings():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT owner_name, owner_whatsapp, business_email, instagram_url, youtube_url, business_address FROM site_settings LIMIT 1")
        settings = cursor.fetchone()
        if not settings:
            settings = {
                'owner_name': 'C2T MOBILES',
                'owner_whatsapp': '919994645492',
                'business_email': 'contact@c2tmobiles.com',
                'instagram_url': 'https://instagram.com/c2tmobiles',
                'youtube_url': 'https://youtube.com/@c2tmobiles',
                'business_address': ''
            }
        return jsonify(settings)

@api_public.route('/brands', methods=['GET'])
def get_brands():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands WHERE is_active = 1 ORDER BY display_order ASC, name ASC")
        brands = cursor.fetchall()
        
        for b in brands:
            cursor.execute("SELECT COUNT(*) as count FROM products WHERE (LOWER(brand) = LOWER(?) OR brand_id = ?) AND status = 'AVAILABLE'", (b['name'], b['id']))
            b['product_count'] = cursor.fetchone()['count']
            
        return jsonify({'brands': brands, 'count': len(brands)})

@api_public.route('/brands/<identifier>', methods=['GET'])
def get_brand_detail(identifier):
    with get_db() as conn:
        cursor = conn.cursor()
        if identifier.isdigit():
            cursor.execute("SELECT * FROM brands WHERE id = ?", (int(identifier),))
        else:
            cursor.execute("SELECT * FROM brands WHERE LOWER(slug) = LOWER(?) OR LOWER(name) = LOWER(?)", (identifier, identifier))
            
        brand = cursor.fetchone()
        if not brand:
            # Create a virtual brand response if brand exists in products text but not yet in brands table
            brand = {
                'id': 0,
                'name': identifier.capitalize(),
                'slug': identifier.lower(),
                'logo_icon': '📱',
                'description': f"Explore quality second-hand {identifier.capitalize()} smartphones.",
                'is_active': 1
            }
            
        cursor.execute("SELECT COUNT(*) as count FROM products WHERE (LOWER(brand) = LOWER(?) OR brand_id = ?) AND status = 'AVAILABLE'", (brand['name'], brand.get('id', 0)))
        brand['product_count'] = cursor.fetchone()['count']
        return jsonify(brand)

@api_public.route('/products', methods=['GET'])
def get_products():
    brand = request.args.get('brand', '').strip()
    condition = request.args.get('condition', '').strip()
    storage = request.args.get('storage', '').strip()
    status = request.args.get('status', '').strip() # AVAILABLE or SOLD
    search = request.args.get('search', '').strip()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    featured_only = request.args.get('featured', type=int)
    sort_by = request.args.get('sort', 'newest').strip()
    limit = request.args.get('limit', type=int)
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if brand:
        # Handle multiple comma separated brands or single brand
        brands_list = [b.strip() for b in brand.split(',') if b.strip()]
        if len(brands_list) == 1:
            query += " AND (LOWER(brand) = LOWER(?) OR brand_id IN (SELECT id FROM brands WHERE LOWER(slug) = LOWER(?) OR LOWER(name) = LOWER(?)))"
            params.extend([brands_list[0], brands_list[0], brands_list[0]])
        elif len(brands_list) > 1:
            placeholders = ','.join(['LOWER(?)'] * len(brands_list))
            query += f" AND LOWER(brand) IN ({placeholders})"
            params.extend([b.lower() for b in brands_list])

    if condition:
        conditions_list = [c.strip() for c in condition.split(',') if c.strip()]
        if len(conditions_list) == 1:
            query += " AND LOWER(condition) = LOWER(?)"
            params.append(conditions_list[0])
        elif len(conditions_list) > 1:
            placeholders = ','.join(['LOWER(?)'] * len(conditions_list))
            query += f" AND LOWER(condition) IN ({placeholders})"
            params.extend([c.lower() for c in conditions_list])

    if storage:
        storage_list = [s.strip() for s in storage.split(',') if s.strip()]
        if len(storage_list) == 1:
            query += " AND LOWER(storage) = LOWER(?)"
            params.append(storage_list[0])
        elif len(storage_list) > 1:
            placeholders = ','.join(['LOWER(?)'] * len(storage_list))
            query += f" AND LOWER(storage) IN ({placeholders})"
            params.extend([s.lower() for s in storage_list])

    if status:
        query += " AND LOWER(status) = LOWER(?)"
        params.append(status)
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    if featured_only:
        query += " AND featured = 1"
    if search:
        query += " AND (LOWER(brand) LIKE ? OR LOWER(model) LIKE ? OR LOWER(product_id) LIKE ? OR LOWER(storage) LIKE ? OR LOWER(colour) LIKE ?)"
        term = f"%{search.lower()}%"
        params.extend([term, term, term, term, term])
        
    # Sorting
    if sort_by == 'price_asc':
        query += " ORDER BY price ASC"
    elif sort_by == 'price_desc':
        query += " ORDER BY price DESC"
    elif sort_by == 'popular':
        query += " ORDER BY featured DESC, created_at DESC"
    else:
        query += " ORDER BY created_at DESC"

    if limit and limit > 0:
        query += " LIMIT ?"
        params.append(limit)
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        # Attach images and formatted fields
        for p in products:
            cursor.execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY is_primary DESC, display_order ASC", (p['id'],))
            p['images'] = cursor.fetchall()
            p['primary_image'] = p['images'][0]['image_url'] if p['images'] else '/assets/images/placeholder.jpg'
            p['price_formatted'] = format_inr(p['price'])
            if p['mrp'] and p['mrp'] > p['price']:
                p['mrp_formatted'] = format_inr(p['mrp'])
                p['discount_percent'] = round(((p['mrp'] - p['price']) / p['mrp']) * 100)
            else:
                p['mrp_formatted'] = None
                p['discount_percent'] = 0
                
        return jsonify({'products': products, 'count': len(products)})

@api_public.route('/products/search', methods=['GET'])
def search_products():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'products': [], 'count': 0})
        
    term = f"%{q.lower()}%"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM products 
            WHERE LOWER(brand) LIKE ? 
               OR LOWER(model) LIKE ? 
               OR LOWER(product_id) LIKE ? 
               OR LOWER(storage) LIKE ? 
               OR LOWER(colour) LIKE ?
            ORDER BY created_at DESC
        """, (term, term, term, term, term))
        products = cursor.fetchall()
        
        for p in products:
            cursor.execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY is_primary DESC, display_order ASC", (p['id'],))
            p['images'] = cursor.fetchall()
            p['primary_image'] = p['images'][0]['image_url'] if p['images'] else '/assets/images/placeholder.jpg'
            p['price_formatted'] = format_inr(p['price'])
            
        return jsonify({'products': products, 'count': len(products)})

@api_public.route('/products/<identifier>', methods=['GET'])
def get_product_detail(identifier):
    with get_db() as conn:
        cursor = conn.cursor()
        
        if identifier.isdigit():
            cursor.execute("SELECT * FROM products WHERE id = ?", (int(identifier),))
        else:
            cursor.execute("SELECT * FROM products WHERE UPPER(product_id) = UPPER(?) OR slug = ?", (identifier, identifier))
            
        product = cursor.fetchone()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
            
        cursor.execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY is_primary DESC, display_order ASC", (product['id'],))
        images = cursor.fetchall()
        product['images'] = images if images else [{'image_url': '/assets/images/placeholder.jpg', 'is_primary': 1}]
        product['primary_image'] = product['images'][0]['image_url']
        product['price_formatted'] = format_inr(product['price'])
        
        if product['mrp'] and product['mrp'] > product['price']:
            product['mrp_formatted'] = format_inr(product['mrp'])
            product['discount_percent'] = round(((product['mrp'] - product['price']) / product['mrp']) * 100)
        else:
            product['mrp_formatted'] = None
            product['discount_percent'] = 0
            
        # Get owner whatsapp number
        cursor.execute("SELECT owner_whatsapp FROM site_settings LIMIT 1")
        settings = cursor.fetchone()
        wa_number = settings['owner_whatsapp'] if (settings and settings['owner_whatsapp']) else '919994645492'
        
        wa_message = generate_whatsapp_message(product)
        product['whatsapp_url'] = build_whatsapp_link(wa_number, wa_message)
        product['whatsapp_message'] = wa_message
        
        # Fetch related products
        cursor.execute("""
            SELECT * FROM products 
            WHERE brand = ? AND id != ? AND status = 'AVAILABLE' 
            ORDER BY created_at DESC LIMIT 4
        """, (product['brand'], product['id']))
        related = cursor.fetchall()
        for rel in related:
            cursor.execute("SELECT image_url FROM product_images WHERE product_id = ? ORDER BY is_primary DESC LIMIT 1", (rel['id'],))
            img = cursor.fetchone()
            rel['primary_image'] = img['image_url'] if img else '/assets/images/placeholder.jpg'
            rel['price_formatted'] = format_inr(rel['price'])
            
        product['related_products'] = related
        
        return jsonify(product)

@api_public.route('/enquiries', methods=['POST'])
def record_enquiry():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    user_id = session.get('user_id')
    
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, product_id, brand, model, price FROM products WHERE id = ? OR UPPER(product_id) = UPPER(?)", (product_id, str(product_id)))
        prod = cursor.fetchone()
        
        if prod:
            product_name = f"{prod['brand']} {prod['model']}"
            cursor.execute("""
                INSERT INTO whatsapp_enquiries (product_id, user_id, product_code, product_name, product_price)
                VALUES (?, ?, ?, ?, ?)
            """, (prod['id'], user_id, prod['product_id'], product_name, prod['price']))
            return jsonify({'success': True, 'message': 'Enquiry recorded successfully'})
        else:
            return jsonify({'error': 'Product not found'}), 404
