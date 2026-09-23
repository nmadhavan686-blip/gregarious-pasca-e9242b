import sqlite3
from contextlib import contextmanager
from backend.config import Config

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Config.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # 1. Ensure products table has brand_id, users has avatar_url, whatsapp_enquiries has user_id if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(products);")
        cols = [c[1] for c in cursor.fetchall()]
        if 'brand_id' not in cols:
            try:
                cursor.execute("ALTER TABLE products ADD COLUMN brand_id INTEGER;")
                conn.commit()
            except Exception as e:
                print(f"Migration notice: {e}")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='whatsapp_enquiries';")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(whatsapp_enquiries);")
        cols = [c[1] for c in cursor.fetchall()]
        if 'user_id' not in cols:
            try:
                cursor.execute("ALTER TABLE whatsapp_enquiries ADD COLUMN user_id INTEGER;")
                conn.commit()
            except Exception as e:
                print(f"Migration notice: {e}")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(users);")
        cols = [c[1] for c in cursor.fetchall()]
        if 'avatar_url' not in cols:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT DEFAULT '';")
                conn.commit()
            except Exception as e:
                print(f"Migration notice: {e}")

        if 'role' not in cols:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'customer';")
                conn.commit()
            except Exception as e:
                print(f"Migration notice: {e}")

        # Check if users table has strict NOT NULL on phone
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users';")
        sql_row = cursor.fetchone()
        if sql_row and ('phone TEXT UNIQUE NOT NULL' in sql_row[0] or 'phone TEXT NOT NULL' in sql_row[0]):
            try:
                cursor.execute("CREATE TABLE users_new (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT DEFAULT '', password_hash TEXT NOT NULL, auth_provider TEXT DEFAULT 'local', role TEXT DEFAULT 'customer', avatar_url TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP);")
                cursor.execute("INSERT INTO users_new SELECT id, full_name, email, COALESCE(phone, ''), password_hash, auth_provider, 'customer', COALESCE(avatar_url, ''), created_at, updated_at, last_login FROM users;")
                cursor.execute("DROP TABLE users;")
                cursor.execute("ALTER TABLE users_new RENAME TO users;")
                conn.commit()
                print("Migrated users table to relaxed phone schema with role column.")
            except Exception as e:
                print(f"Users table migration notice: {e}")
                
    # 2. Run full schema script
    with open(Config.SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    
    # 3. Ensure site_settings row exists & has updated contact info
    cursor.execute("SELECT COUNT(*) FROM site_settings;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO site_settings (owner_name, owner_whatsapp, business_email, instagram_url, youtube_url, business_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            Config.BUSINESS_NAME,
            Config.OWNER_WHATSAPP_NUMBER,
            Config.BUSINESS_EMAIL,
            Config.INSTAGRAM_URL,
            Config.YOUTUBE_URL,
            Config.BUSINESS_ADDRESS
        ))
    else:
        cursor.execute("""
            UPDATE site_settings SET owner_whatsapp = ?, business_address = ? WHERE id = 1
        """, (Config.OWNER_WHATSAPP_NUMBER, Config.BUSINESS_ADDRESS))
    conn.commit()
    
    # 4. Ensure an Owner user account exists in users table with role = 'owner'
    from werkzeug.security import generate_password_hash
    owner_email_clean = Config.OWNER_EMAIL.lower()
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ? OR LOWER(email) = 'owner@c2tmobiles.com' OR role = 'owner';", (owner_email_clean,))
    owner_row = cursor.fetchone()
    pass_hash = generate_password_hash(Config.OWNER_PASSWORD)
    if not owner_row:
        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, auth_provider, role, avatar_url, last_login)
            VALUES ('C2T MOBILES Owner', ?, '9994645492', ?, 'local', 'owner', '', CURRENT_TIMESTAMP)
        """, (owner_email_clean, pass_hash))
    else:
        cursor.execute("""
            UPDATE users 
            SET full_name = 'C2T MOBILES Owner', email = ?, phone = '9994645492', role = 'owner', password_hash = ?
            WHERE id = ?
        """, (owner_email_clean, pass_hash, owner_row[0]))
    conn.commit()

    conn.close()
    print("Database initialized, migrated, and verified successfully.")
