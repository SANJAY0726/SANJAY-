# app.py
# Main Flask web application

from flask import Flask, render_template, request, redirect, url_for
from scraper import collect_products
from analyzer import process_products
from database import (
    init_db,
    save_products,
    get_products_by_query,
    clear_old_results,
    get_global_stats,
    get_history,
    get_platform_stats,
    get_top_deals,
    clear_all_history
)

# Create the Flask app
app = Flask(__name__)

# Initialize database when app starts
init_db()


def build_search_insight(products, query):
    if not products:
        return {
            'headline': f"Smart recommendation for '{query}'",
            'summary': 'No products found yet. Try a broader search term or refresh results.',
            'platforms': [],
            'average_score': 0,
            'best_discount': 0,
            'best_rating': 0,
            'product_count': 0,
        }

    platforms = sorted({p['platform'] for p in products if p.get('platform')})
    average_score = round(sum(p['final_score'] for p in products) / len(products), 2)
    best_discount = max((p.get('discount_percent') or 0) for p in products)
    best_rating = max((p.get('rating') or 0) for p in products)

    return {
        'headline': f"AI smart insight for '{query}'",
        'summary': f"Analyzed {len(products)} products across {len(platforms)} platforms and selected the strongest candidate by combining price, sentiment, rating and social proof.",
        'platforms': platforms,
        'average_score': average_score,
        'best_discount': best_discount,
        'best_rating': best_rating,
        'product_count': len(products),
    }


@app.route('/')
def home():
    """Home page - shows the search form with real-time stats and top deals"""
    stats = get_global_stats()
    top_deals = get_top_deals(4)  # Get top 4 best recommendation deals
    ticker_deals = get_top_deals(15) # For the scrolling bar
    return render_template('index.html', stats=stats, top_deals=top_deals, ticker_deals=ticker_deals)


@app.route('/search', methods=['GET', 'POST'])
def search():
    """
    Handle search form submission.
    1. Get search query from form or URL query parameters
    2. Collect product data (using scraping or cache)
    3. Run AI analysis
    4. Save to database
    5. Display results
    """
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        refresh = request.form.get('refresh', 'false').lower() == 'true'
    else:
        query = request.args.get('query', '').strip()
        refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    if not query:
        return render_template('index.html', error='Please enter a product name!')
    
    # --- CACHING LOGIC ---
    if not refresh:
        try:
            from datetime import datetime, timedelta
            cached_results = get_products_by_query(query)
            if cached_results:
                # Check if cache is fresh (within 60 minutes)
                # SQLite stores timestamp as string, parse it
                try:
                    # Format: '2026-04-26 02:31:10'
                    last_created = datetime.strptime(cached_results[0]['created_at'], '%Y-%m-%d %H:%M:%S')
                    if datetime.now() - last_created < timedelta(minutes=60):
                        print(f"[Cache Hit] Using fresh results for: {query}")
                        best_product = cached_results[0]
                        return render_template(
                            'results.html',
                            products=cached_results,
                            best_product=best_product,
                            query=query,
                            total=len(cached_results),
                            insight=build_search_insight(cached_results, query)
                        )
                except Exception as e:
                    print(f"[Cache Error] Timestamp parsing failed: {e}")
        except Exception as e:
            print(f"[Cache Warning] Failed to retrieve cache: {e}")
    # --- END CACHING LOGIC ---
    
    # Step 1: Collect raw product data
    print(f'Searching for: {query} (Force Refresh: {refresh})')
    try:
        raw_products = collect_products(query)
    except Exception as e:
        print(f"Scraper error: {e}")
        raw_products = []
    
    if not raw_products:
        return render_template('results.html', products=[], query=query, total=0)
    
    # Step 2: Run AI analysis on all products
    try:
        analyzed_products = process_products(raw_products)
    except Exception as e:
        print(f"Analysis error: {e}")
        analyzed_products = raw_products # fallback to raw data
    
    # Step 3: Clear old results and save new ones
    try:
        clear_old_results(query)
        save_products(analyzed_products)
    except Exception as e:
        print(f"Database error: {e}")
    
    # Step 4: Get the best product (first in sorted list by AI score)
    best_product = analyzed_products[0] if analyzed_products else None
    
    # Step 5: Render results page
    return render_template(
        'results.html',
        products=analyzed_products,
        best_product=best_product,
        query=query,
        total=len(analyzed_products),
        insight=build_search_insight(analyzed_products, query)
    )


@app.route('/dashboard')
def dashboard():
    """Dashboard page - shows advanced analytics, charts and top deals"""
    stats = get_global_stats()
    platform_stats = get_platform_stats()
    top_deals = get_top_deals(5)
    
    # Calculate extra stats
    history = get_history()
    avg_rating = 0.0
    max_discount = 0.0
    
    if platform_stats:
        total_rating = sum(p['avg_rating'] for p in platform_stats if p['avg_rating'])
        count_rating = sum(1 for p in platform_stats if p['avg_rating'])
        if count_rating > 0:
            avg_rating = round(total_rating / count_rating, 2)
            
    if top_deals:
        max_discount = max(p['discount_percent'] for p in top_deals)
        
    return render_template(
        'dashboard.html',
        stats=stats,
        platform_stats=platform_stats,
        top_deals=top_deals,
        history=history,
        avg_rating=avg_rating,
        max_discount=max_discount
    )


@app.route('/history')
def history_page():
    """History page - shows search logs and statistics"""
    history = get_history()
    return render_template('history.html', history=history)


@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear all query results from database"""
    try:
        clear_all_history()
        print("[Database] All search history cleared.")
    except Exception as e:
        print(f"[Database Error] Failed to clear history: {e}")
    return redirect(url_for('history_page'))


@app.route('/saved')
def saved_page():
    """Saved products page - powered by client-side localStorage"""
    return render_template('saved.html')


# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5000)
