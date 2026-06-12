# database.py
# This file handles all database operations

import sqlite3
import os

# Path to database file
# On Vercel, use /tmp since the filesystem is read-only except /tmp
if os.environ.get('VERCEL'):
    DB_DIR = '/tmp'
    DB_PATH = os.path.join(DB_DIR, 'products.db')
else:
    DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    DB_PATH = os.path.join(DB_DIR, 'products.db')

def init_db():
    """Create the database and table if they don't exist, and migrate missing columns"""
    # Make sure the 'data' folder exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            platform TEXT NOT NULL,
            price REAL,
            original_price REAL,
            discount_percent REAL,
            rating REAL,
            num_reviews INTEGER,
            review_text TEXT,
            sentiment_score REAL,
            final_score REAL,
            product_url TEXT,
            search_query TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image TEXT
        )
    ''')
    
    # Dynamic migration: check if 'created_at' or 'image' exists in columns
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'created_at' not in columns:
        print("[Database Migration] Adding missing 'created_at' column...")
        cursor.execute("ALTER TABLE products ADD COLUMN created_at TIMESTAMP")
        cursor.execute("UPDATE products SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    if 'image' not in columns:
        print("[Database Migration] Adding missing 'image' column...")
        cursor.execute("ALTER TABLE products ADD COLUMN image TEXT")
    
    conn.commit()
    conn.close()
    print('Database initialized successfully!')


def save_products(products_list):
    """Save a list of product dictionaries to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for product in products_list:
        cursor.execute('''
            INSERT INTO products 
            (name, platform, price, original_price, discount_percent,
             rating, num_reviews, review_text, sentiment_score,
             final_score, product_url, search_query, created_at, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        ''', (
            product.get('name', ''),
            product.get('platform', ''),
            product.get('price', 0),
            product.get('original_price', 0),
            product.get('discount_percent', 0),
            product.get('rating', 0),
            product.get('num_reviews', 0),
            product.get('review_text', ''),
            product.get('sentiment_score', 0),
            product.get('final_score', 0),
            product.get('product_url', ''),
            product.get('search_query', ''),
            product.get('image', '')
        ))
    
    conn.commit()
    conn.close()


def get_products_by_query(query):
    """Fetch all products matching a search query"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM products 
        WHERE search_query = ?
        ORDER BY final_score DESC
    ''', (query,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def clear_old_results(query):
    """Remove old results for a query before fetching new ones"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE search_query = ?', (query,))
    conn.commit()
    conn.close()

def get_global_stats():
    """Fetch total products and total searches performed"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM products')
    total_products = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT search_query) FROM products')
    total_searches = cursor.fetchone()[0]
    
    conn.close()
    return {
        'total_products': total_products,
        'total_searches': total_searches,
        'accuracy': 98.5 # Simulated accuracy metric
    }


def get_history():
    """Fetch list of all search queries performed with counts and dates"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT search_query, COUNT(*) as product_count, MAX(created_at) as last_searched,
               MIN(price) as min_price, AVG(price) as avg_price, MAX(rating) as max_rating
        FROM products 
        GROUP BY search_query 
        ORDER BY last_searched DESC
    ''')
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_platform_stats():
    """Get metrics grouped by platform for dashboard analytics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT platform, COUNT(*) as count, AVG(price) as avg_price, 
               AVG(rating) as avg_rating, AVG(sentiment_score) as avg_sentiment
        FROM products 
        GROUP BY platform
    ''')
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_top_deals(limit=5):
    """Fetch products with highest discount percent or final score"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM products 
        WHERE discount_percent > 0
        ORDER BY final_score DESC LIMIT ?
    ''', (limit,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def clear_all_history():
    """Delete all products from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products')
    conn.commit()
    conn.close()
