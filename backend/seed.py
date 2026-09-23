import os
import re
from pathlib import Path
from PIL import Image, ImageDraw
from backend.config import Config
from backend.database import init_db, get_db
from backend.utils.auth import hash_password
from backend.utils.helpers import slugify

def create_sample_image(filename: str, brand_text: str, model_text: str, bg_color="#1e293b", text_color="#38bdf8"):
    target_path = Config.UPLOADS_DIR / filename
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    img = Image.new("RGB", (800, 800), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    margin = 150
    draw.rounded_rectangle([margin, 60, 800 - margin, 800 - 60], radius=40, fill="#0f172a", outline="#475569", width=4)
    draw.rounded_rectangle([margin + 20, 110, 800 - margin - 20, 800 - 90], radius=24, fill="#1e1e2e")
    draw.ellipse([385, 80, 415, 95], fill="#000000")
    
    draw.text((400, 340), brand_text, fill=text_color, anchor="ms")
    draw.text((400, 400), model_text, fill="#ffffff", anchor="ms")
    draw.text((400, 470), "C2T MOBILES", fill="#10b981", anchor="ms")
    draw.text((400, 520), "100% Quality Inspected", fill="#94a3b8", anchor="ms")
    
    img.save(target_path, "JPEG", quality=90)
    return f"/uploads/products/{filename}"

def seed_database():
    print("[DB] Initializing Database Schema...")
    init_db()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Ensure Admin Account Exists
        cursor.execute("SELECT id FROM admins WHERE username = ?", (Config.ADMIN_USERNAME,))
        if not cursor.fetchone():
            pass_hash = hash_password(Config.ADMIN_PASSWORD)
            cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", (Config.ADMIN_USERNAME, pass_hash))
            print(f"[AUTH] Created default admin user: {Config.ADMIN_USERNAME}")

        # 2. Seed Default Brands (Use SVG logo paths, NO emojis)
        initial_brands = [
            {"name": "Apple", "slug": "apple", "logo_icon": "/assets/images/brands/apple.svg", "order": 1},
            {"name": "Samsung", "slug": "samsung", "logo_icon": "/assets/images/brands/samsung.svg", "order": 2},
            {"name": "OnePlus", "slug": "oneplus", "logo_icon": "/assets/images/brands/oneplus.svg", "order": 3},
            {"name": "Google", "slug": "google", "logo_icon": "/assets/images/brands/google.svg", "order": 4},
            {"name": "Xiaomi", "slug": "xiaomi", "logo_icon": "/assets/images/brands/xiaomi.svg", "order": 5},
            {"name": "Redmi", "slug": "redmi", "logo_icon": "/assets/images/brands/redmi.svg", "order": 6},
            {"name": "Realme", "slug": "realme", "logo_icon": "/assets/images/brands/realme.svg", "order": 7},
            {"name": "Vivo", "slug": "vivo", "logo_icon": "/assets/images/brands/vivo.svg", "order": 8},
            {"name": "Oppo", "slug": "oppo", "logo_icon": "/assets/images/brands/oppo.svg", "order": 9},
            {"name": "Nothing", "slug": "nothing", "logo_icon": "/assets/images/brands/nothing.svg", "order": 10},
            {"name": "Motorola", "slug": "motorola", "logo_icon": "/assets/images/brands/motorola.svg", "order": 11},
            {"name": "iQOO", "slug": "iqoo", "logo_icon": "/assets/images/brands/iqoo.svg", "order": 12},
            {"name": "POCO", "slug": "poco", "logo_icon": "/assets/images/brands/poco.svg", "order": 13},
            {"name": "ASUS", "slug": "asus", "logo_icon": "/assets/images/brands/asus.svg", "order": 14},
            {"name": "Other", "slug": "other", "logo_icon": "/assets/images/brands/other.svg", "order": 15}
        ]

        for b in initial_brands:
            cursor.execute("SELECT id FROM brands WHERE slug = ?", (b['slug'],))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE brands SET logo_icon = ?, is_active = 1 WHERE id = ?", (b['logo_icon'], row['id']))
            else:
                cursor.execute("""
                    INSERT INTO brands (name, slug, logo_icon, description, is_active, display_order)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (b['name'], b['slug'], b['logo_icon'], f"Explore pre-owned {b['name']} smartphones.", b['order']))
        print("[SUCCESS] Brand categories updated with SVG vector logos!")
            
        # 3. Seed Sample Products if DB is empty
        cursor.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()['count'] > 0:
            print("[INFO] Products already exist in database. Skipping product seed.")
            return
            
        print("[SEED] Seeding sample second-hand mobile devices...")
        
        sample_mobiles = [
            {
                "product_id": "C2T-IPH13-001",
                "brand": "Apple",
                "model": "iPhone 13",
                "price": 32999,
                "mrp": 59900,
                "storage": "128GB",
                "ram": "4GB",
                "colour": "Midnight",
                "condition": "Excellent",
                "battery_health": "87%",
                "network": "5G / Dual SIM",
                "sim_type": "Physical SIM + eSIM",
                "warranty": "3 Months C2T Store Warranty",
                "accessories": "Original Lightning to USB-C Cable, Premium Clear Case",
                "box_included": 1,
                "charger_included": 1,
                "purchase_date": "Oct 2022",
                "description": "Mint condition iPhone 13 128GB in Midnight Blue. Display has zero scratch, body in 9.5/10 condition. Battery health is at 87% original Apple battery.",
                "specifications": "A15 Bionic chip, 6.1-inch Super Retina XDR OLED display, Dual 12MP camera system with Cinematic mode, IP68 water resistance.",
                "status": "AVAILABLE",
                "featured": 1,
                "badge": "HOT DEAL",
                "display_condition": "Flawless screen, glass guard installed",
                "body_condition": "Minor micro-scratches on side frame",
                "camera_condition": "Lens scratchless, 4K 60fps crystal clear",
                "battery_condition": "87% Original Apple Battery",
                "bg": "#0f172a", "fg": "#38bdf8"
            },
            {
                "product_id": "C2T-IPH14-002",
                "brand": "Apple",
                "model": "iPhone 14",
                "price": 42999,
                "mrp": 69900,
                "storage": "128GB",
                "ram": "6GB",
                "colour": "Blue",
                "condition": "Like New",
                "battery_health": "91%",
                "network": "5G / Dual SIM",
                "sim_type": "Physical SIM + eSIM",
                "warranty": "6 Months AppleCare + C2T Warranty",
                "accessories": "Original Apple Box, Cable, Matte Screen Guard",
                "box_included": 1,
                "charger_included": 1,
                "purchase_date": "Jan 2024",
                "description": "Like new condition iPhone 14 128GB Blue. Barely used device with 91% battery health. Comes with original serial-matched box.",
                "specifications": "A15 Bionic with 5-core GPU, Photonic Engine, Crash Detection, Action Mode Video.",
                "status": "AVAILABLE",
                "featured": 1,
                "badge": "LIKE NEW",
                "display_condition": "100% Scratchless screen",
                "body_condition": "No dents, pristine aluminum edges",
                "camera_condition": "Photonic Engine dual cameras tested",
                "battery_condition": "91% Original Apple Battery",
                "bg": "#1e1b4b", "fg": "#818cf8"
            },
            {
                "product_id": "C2T-S23U-003",
                "brand": "Samsung",
                "model": "Galaxy S23 Ultra",
                "price": 58999,
                "mrp": 124999,
                "storage": "256GB",
                "ram": "12GB",
                "colour": "Phantom Black",
                "condition": "Excellent",
                "battery_health": "94%",
                "network": "5G Dual SIM",
                "sim_type": "Dual Nano SIM",
                "warranty": "3 Months C2T Store Warranty",
                "accessories": "S-Pen, 45W Fast Charger, Original Box",
                "box_included": 1,
                "charger_included": 1,
                "purchase_date": "May 2023",
                "description": "Flagship Samsung Galaxy S23 Ultra with 200MP camera and built-in S-Pen. 12GB RAM, 256GB UFS 4.0 storage.",
                "specifications": "Snapdragon 8 Gen 2 for Galaxy, 6.8-inch QHD+ 120Hz Dynamic AMOLED 2X, 200MP 100x Space Zoom camera.",
                "status": "AVAILABLE",
                "featured": 1,
                "badge": "FEATURED",
                "display_condition": "Clean curved AMOLED display",
                "body_condition": "9/10 condition, spotless back glass",
                "camera_condition": "100x Space zoom tested & clear",
                "battery_condition": "94% Health, 5000mAh long battery life",
                "bg": "#18181b", "fg": "#f43f5e"
            },
            {
                "product_id": "C2T-OP12-004",
                "brand": "OnePlus",
                "model": "OnePlus 12",
                "price": 46999,
                "mrp": 64999,
                "storage": "256GB",
                "ram": "12GB",
                "colour": "Emerald Green",
                "condition": "Like New",
                "battery_health": "96%",
                "network": "5G Dual SIM",
                "sim_type": "Dual Nano SIM",
                "warranty": "8 Months Official OnePlus Warranty Remaining",
                "accessories": "100W SUPERVOOC Power Adapter, Cable, Box, Bill",
                "box_included": 1,
                "charger_included": 1,
                "purchase_date": "Mar 2024",
                "description": "Super clean OnePlus 12 256GB in Emerald Green. Includes original bill, box and 100W fast charger.",
                "specifications": "Snapdragon 8 Gen 3, 4th Gen Hasselblad Camera, 2K 120Hz ProXDR display, 5400mAh battery.",
                "status": "AVAILABLE",
                "featured": 1,
                "badge": "SALE",
                "display_condition": "Factory screen guard intact",
                "body_condition": "10/10 Like new zero scratches",
                "camera_condition": "Hasselblad triple camera perfect",
                "battery_condition": "96% Battery Health",
                "bg": "#064e3b", "fg": "#34d399"
            },
            {
                "product_id": "C2T-PIX8-005",
                "brand": "Google",
                "model": "Pixel 8",
                "price": 37999,
                "mrp": 75999,
                "storage": "128GB",
                "ram": "8GB",
                "colour": "Hazel",
                "condition": "Good",
                "battery_health": "89%",
                "network": "5G / eSIM",
                "sim_type": "Nano SIM + eSIM",
                "warranty": "3 Months C2T Store Warranty",
                "accessories": "Type-C Cable, Quick Switch Adapter, Box",
                "box_included": 1,
                "charger_included": 0,
                "purchase_date": "Nov 2023",
                "description": "Pure Google Android experience with AI magic editor & camera features. Smooth 120Hz Actua display.",
                "specifications": "Google Tensor G3 chip, 50MP main camera with Magic Eraser, Best Take, 7 years OS update support.",
                "status": "AVAILABLE",
                "featured": 0,
                "badge": "HOT DEAL",
                "display_condition": "Clean display with minor hairline mark",
                "body_condition": "8.5/10 aluminum frame",
                "camera_condition": "Pixel AI camera working 100%",
                "battery_condition": "89% Health",
                "bg": "#292524", "fg": "#fbbf24"
            },
            {
                "product_id": "C2T-VIVO-006",
                "brand": "Vivo",
                "model": "X100",
                "price": 41999,
                "mrp": 63999,
                "storage": "256GB",
                "ram": "12GB",
                "colour": "Asteroid Black",
                "condition": "Excellent",
                "battery_health": "92%",
                "network": "5G Dual SIM",
                "sim_type": "Dual Nano SIM",
                "warranty": "3 Months C2T Warranty",
                "accessories": "120W FlashCharge Adapter, Cable, Case",
                "box_included": 1,
                "charger_included": 1,
                "purchase_date": "Feb 2024",
                "description": "Camera king Vivo X100 with ZEISS optics and APO Telephoto lens. Extremely fast 120W charging.",
                "specifications": "Dimensity 9300 chipset, ZEISS optics 50MP telephoto, 120W FlashCharge, 5000mAh battery.",
                "status": "AVAILABLE",
                "featured": 0,
                "badge": "",
                "display_condition": "Spotless AMOLED screen",
                "body_condition": "9/10 condition",
                "camera_condition": "ZEISS portrait camera super crisp",
                "battery_condition": "92% Health",
                "bg": "#111827", "fg": "#60a5fa"
            },
            {
                "product_id": "C2T-NOTH2-007",
                "brand": "Nothing",
                "model": "Phone (2)",
                "price": 28999,
                "mrp": 44999,
                "storage": "256GB",
                "ram": "12GB",
                "colour": "Dark Grey",
                "condition": "Excellent",
                "battery_health": "90%",
                "network": "5G Dual SIM",
                "sim_type": "Dual Nano SIM",
                "warranty": "3 Months C2T Warranty",
                "accessories": "Original Nothing Cable, Box",
                "box_included": 1,
                "charger_included": 0,
                "purchase_date": "Aug 2023",
                "description": "Transparent glyph interface design smartphone. 12GB RAM + 256GB storage edition in Dark Grey.",
                "specifications": "Snapdragon 8+ Gen 1, Glyph Interface lighting, 50MP dual camera with OIS, 120Hz LTPO OLED.",
                "status": "AVAILABLE",
                "featured": 0,
                "badge": "FEATURED",
                "display_condition": "100% clean OLED screen",
                "body_condition": "Glyph lights working perfectly, transparent back intact",
                "camera_condition": "Dual 50MP OIS camera tested",
                "battery_condition": "90% Battery Health",
                "bg": "#171717", "fg": "#e5e5e5"
            },
            {
                "product_id": "C2T-RED13-008",
                "brand": "Redmi",
                "model": "Note 13 Pro+",
                "price": 21999,
                "mrp": 33999,
                "storage": "256GB",
                "ram": "12GB",
                "colour": "Fusion Purple",
                "condition": "Good",
                "battery_health": "88%",
                "network": "5G Dual SIM",
                "sim_type": "Dual SIM",
                "warranty": "3 Months C2T Warranty",
                "accessories": "120W HyperCharge Adapter, Cable, Leather Finish Back Case",
                "box_included": 1,
                "charger_included": 1,
                "purchase_date": "Jan 2024",
                "description": "200MP camera curved AMOLED smartphone with IP68 water resistance and 120W HyperCharge.",
                "specifications": "Dimensity 7200-Ultra, 200MP OIS camera, 1.5K 120Hz Curved AMOLED, IP68 rated.",
                "status": "SOLD",
                "featured": 0,
                "badge": "SOLD OUT",
                "display_condition": "Curved AMOLED screen clean",
                "body_condition": "Minor wear around USB-C port",
                "camera_condition": "200MP OIS camera fully tested",
                "battery_condition": "88% Health",
                "bg": "#3b0764", "fg": "#c084fc"
            }
        ]
        
        for p in sample_mobiles:
            slug = slugify(f"{p['brand']}-{p['model']}-{p['storage']}-{p['product_id']}")
            cursor.execute("SELECT id FROM brands WHERE LOWER(name) = LOWER(?)", (p['brand'],))
            b_row = cursor.fetchone()
            brand_id = b_row['id'] if b_row else None
            
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
                p['product_id'], slug, p['brand'], brand_id, p['model'], p['price'], p['mrp'], p['storage'],
                p['ram'], p['colour'], p['condition'], p['battery_health'], p['network'],
                p['sim_type'], p['warranty'], p['accessories'], p['box_included'], p['charger_included'],
                p['purchase_date'], p['description'], p['specifications'], p['status'], p['featured'],
                p['badge'], p['display_condition'], p['body_condition'], p['camera_condition'],
                p['battery_condition'], 'Loud & clear stereo speakers', 'Dual mic noise cancellation tested',
                'Clean USB-C/Lightning port', 'Face ID / Fingerprint fast response', 'All Indian 5G bands tested',
                'Wi-Fi 6 tested', 'Bluetooth 5.3 tested', 'Volume & Power buttons tactile', 'No repairs', 'Original factory assembly'
            ))
            
            prod_id = cursor.lastrowid
            
            img1_name = f"seed_{prod_id}_front.jpg"
            img2_name = f"seed_{prod_id}_back.jpg"
            img3_name = f"seed_{prod_id}_box.jpg"
            
            url1 = create_sample_image(img1_name, p['brand'], f"{p['model']} (Front View)", p['bg'], p['fg'])
            url2 = create_sample_image(img2_name, p['brand'], f"{p['model']} (Back & Camera)", p['bg'], "#38bdf8")
            url3 = create_sample_image(img3_name, p['brand'], f"{p['model']} (Box & Accessories)", "#0f172a", "#10b981")
            
            cursor.execute("INSERT INTO product_images (product_id, image_url, is_primary, display_order) VALUES (?, ?, 1, 0)", (prod_id, url1))
            cursor.execute("INSERT INTO product_images (product_id, image_url, is_primary, display_order) VALUES (?, ?, 0, 1)", (prod_id, url2))
            cursor.execute("INSERT INTO product_images (product_id, image_url, is_primary, display_order) VALUES (?, ?, 0, 2)", (prod_id, url3))
            
        print("[SUCCESS] Sample devices and brands seeded successfully!")

if __name__ == '__main__':
    seed_database()
