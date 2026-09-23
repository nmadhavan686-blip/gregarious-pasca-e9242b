-- C2T MOBILES SQL Database Schema

CREATE TABLE IF NOT EXISTS site_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_name TEXT NOT NULL DEFAULT 'C2T MOBILES Owner',
    owner_whatsapp TEXT NOT NULL DEFAULT '919994645492',
    business_email TEXT DEFAULT 'contact@c2tmobiles.com',
    instagram_url TEXT DEFAULT 'https://instagram.com/c2tmobiles',
    youtube_url TEXT DEFAULT 'https://youtube.com/@c2tmobiles',
    business_address TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Registered Customer & Owner Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT DEFAULT '',
    password_hash TEXT NOT NULL,
    auth_provider TEXT DEFAULT 'local', -- local, google, apple
    role TEXT DEFAULT 'customer', -- customer, owner
    avatar_url TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Database-Driven Brands Table
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    logo_icon TEXT DEFAULT '',
    description TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    brand TEXT NOT NULL,
    brand_id INTEGER,
    model TEXT NOT NULL,
    price INTEGER NOT NULL,
    mrp INTEGER DEFAULT 0,
    storage TEXT NOT NULL,
    ram TEXT DEFAULT '',
    colour TEXT DEFAULT '',
    condition TEXT NOT NULL, -- Like New, Excellent, Good, Fair
    battery_health TEXT DEFAULT '',
    network TEXT DEFAULT '5G',
    sim_type TEXT DEFAULT 'Dual SIM',
    warranty TEXT DEFAULT '3 Months C2T Warranty',
    accessories TEXT DEFAULT '',
    box_included INTEGER DEFAULT 1,
    charger_included INTEGER DEFAULT 1,
    purchase_date TEXT DEFAULT '',
    description TEXT DEFAULT '',
    specifications TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'AVAILABLE', -- AVAILABLE, SOLD
    featured INTEGER DEFAULT 0,
    badge TEXT DEFAULT '', -- NEW, FEATURED, HOT DEAL, SALE, SOLD OUT
    
    -- Condition Inspection Matrix
    display_condition TEXT DEFAULT 'Flawless',
    body_condition TEXT DEFAULT 'Minor micro-scratches',
    camera_condition TEXT DEFAULT 'Clean, full functionality',
    battery_condition TEXT DEFAULT 'Original Apple/OEM Battery',
    speaker_condition TEXT DEFAULT 'Loud and clear',
    mic_condition TEXT DEFAULT 'Tested & working',
    charging_port_condition TEXT DEFAULT 'Clean & tight fit',
    face_id_condition TEXT DEFAULT 'Working perfectly',
    network_condition TEXT DEFAULT 'All Indian SIMs tested',
    wifi_condition TEXT DEFAULT 'Tested & fast',
    bluetooth_condition TEXT DEFAULT 'Tested & working',
    buttons_condition TEXT DEFAULT 'All buttons tactile & working',
    repairs TEXT DEFAULT 'No major repairs',
    repair_details TEXT DEFAULT '',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    is_primary INTEGER DEFAULT 0,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS whatsapp_enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    user_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    product_price INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_brands_slug ON brands(slug);
CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_brand_id ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_featured ON products(featured);
CREATE INDEX IF NOT EXISTS idx_product_images_product_id ON product_images(product_id);
