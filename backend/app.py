from flask import Flask, send_from_directory, jsonify, render_template, request
from flask_cors import CORS
from pathlib import Path
from backend.config import Config
from backend.database import init_db
from backend.routes.api_public import api_public
from backend.routes.api_admin import api_admin
from backend.routes.api_auth import api_auth

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register REST API Blueprints
app.register_blueprint(api_public, url_prefix='/api')
app.register_blueprint(api_admin, url_prefix='/api/admin')
app.register_blueprint(api_auth, url_prefix='/api/auth')

# Serve uploaded product images
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(str(UPLOADS_DIR), filename)

# Root route
@app.route('/')
def serve_root():
    return send_from_directory(str(FRONTEND_DIR), 'index.html')

@app.route('/login')
@app.route('/login.html')
def serve_user_login():
    return send_from_directory(str(FRONTEND_DIR), 'login.html')

@app.route('/register')
@app.route('/register.html')
def serve_user_register():
    return send_from_directory(str(FRONTEND_DIR), 'register.html')

@app.route('/brand/<slug>')
@app.route('/brand/<slug>.html')
def serve_brand_route(slug):
    return send_from_directory(str(FRONTEND_DIR), 'brand.html')

@app.route('/<page_name>.html')
def serve_html_pages(page_name):
    target_file = FRONTEND_DIR / f"{page_name}.html"
    if target_file.exists():
        return send_from_directory(str(FRONTEND_DIR), f"{page_name}.html")
    return send_from_directory(str(FRONTEND_DIR), 'index.html')

@app.route('/admin/')
@app.route('/admin')
def serve_admin_index():
    return send_from_directory(str(FRONTEND_DIR / 'admin'), 'dashboard.html')

@app.route('/admin/<path:filename>')
def serve_admin_pages(filename):
    admin_dir = FRONTEND_DIR / 'admin'
    target_file = admin_dir / filename
    if target_file.exists():
        return send_from_directory(str(admin_dir), filename)
    return send_from_directory(str(admin_dir), 'login.html')

@app.route('/product/<path:path>')
def serve_product_seo_route(path):
    return send_from_directory(str(FRONTEND_DIR), 'product.html')

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return send_from_directory(str(FRONTEND_DIR), 'index.html')

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return jsonify({'error': 'Something went wrong. Please try again later.'}), 500

if __name__ == '__main__':
    init_db()
    print("[SERVER] C2T MOBILES Server running on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
