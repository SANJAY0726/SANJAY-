# analyzer.py
# AI module: Sentiment Analysis + Product Scoring

from textblob import TextBlob
import nltk
import os

# On Vercel, set NLTK data path to /tmp
if os.environ.get('VERCEL'):
    nltk.data.path.insert(0, '/tmp/nltk_data')

# Check NLTK version to determine correct tokenizer package
is_new_nltk = False
try:
    is_new_nltk = tuple(map(int, nltk.__version__.split('.')[:2])) >= (3, 9)
except Exception:
    pass

tokenizer_name = 'punkt_tab' if is_new_nltk else 'punkt'

# Download required NLTK data (only needed once)
try:
    nltk.data.find(f'tokenizers/{tokenizer_name}')
except (LookupError, OSError):
    download_dir = '/tmp/nltk_data' if os.environ.get('VERCEL') else None
    nltk.download(tokenizer_name, download_dir=download_dir)
    nltk.download('averaged_perceptron_tagger', download_dir=download_dir)


def analyze_sentiment(review_text):
    """
    Analyze the sentiment of a review.
    Returns a score between -1.0 (very negative) and +1.0 (very positive)
    0.0 means neutral
    """
    if not review_text or review_text.strip() == '':
        return 0.0
    
    analysis = TextBlob(review_text)
    # .sentiment.polarity gives a number between -1 and 1
    return round(analysis.sentiment.polarity, 3)


def get_sentiment_label(score):
    """Convert sentiment score to human-readable label"""
    if score >= 0.3:
        return 'Positive'
    elif score <= -0.1:
        return 'Negative'
    else:
        return 'Neutral'


def calculate_final_score(product, min_price, max_price):
    """
    Calculate a final recommendation score for a product.
    Returns a score between 0 and 100
    """
    price = product.get('price')
    if not price:
        price_score = 12
    else:
        if max_price > min_price:
            price_score = max(0, (1 - (price - min_price) / (max_price - min_price))) * 30
        else:
            price_score = 30

    rating = product.get('rating')
    if not rating or rating <= 0:
        rating = 4.0
        product['rating'] = rating
    rating_score = (min(rating, 5.0) / 5.0) * 30

    sentiment = product.get('sentiment_score', 0)
    sentiment_score = ((sentiment + 1) / 2) * 20

    discount = product.get('discount_percent', 0) or 0
    discount_bonus = min(discount / 25 * 10, 10)

    num_reviews = product.get('num_reviews') or 0
    if num_reviews > 0:
        review_score = min((min(num_reviews, 10000) / 10000) * 10, 10)
    else:
        review_score = 3

    final = price_score + rating_score + sentiment_score + discount_bonus + review_score
    product['score_components'] = {
        'price_score': round(price_score, 2),
        'rating_score': round(rating_score, 2),
        'sentiment_score': round(sentiment_score, 2),
        'discount_bonus': round(discount_bonus, 2),
        'review_score': round(review_score, 2),
    }
    return round(final, 2)


def process_products(products_list):
    """
    Process all products: run sentiment analysis and calculate scores.
    Returns the processed list sorted by final score (best first).
    """
    processed = []

    valid_prices = [p['price'] for p in products_list if p.get('price')]
    min_price = min(valid_prices) if valid_prices else 0
    max_price = max(valid_prices) if valid_prices else 0

    for product in products_list:
        sentiment = analyze_sentiment(product.get('review_text', ''))
        product['sentiment_score'] = sentiment
        product['sentiment_label'] = get_sentiment_label(sentiment)

        product['final_score'] = calculate_final_score(product, min_price, max_price)

        reasons = []
        if product['sentiment_label'] == 'Positive':
            reasons.append('Very positive sentiment from customer feedback.')
        elif product['sentiment_label'] == 'Neutral':
            reasons.append('Balanced sentiment suggests reliable expectations.')
        else:
            reasons.append('Mixed sentiment; consider this with price and discount.')

        if product.get('discount_percent', 0) >= 20:
            reasons.append(f'Attractive markdown of {product["discount_percent"]}%')
        elif product.get('discount_percent', 0) > 0:
            reasons.append(f'Moderate discount of {product["discount_percent"]}%')

        if product.get('rating', 0) >= 4.5:
            reasons.append('Excellent customer ratings.')
        elif product.get('rating', 0) >= 4.0:
            reasons.append('Strong average rating among shoppers.')

        if product.get('num_reviews', 0) >= 1000:
            reasons.append('High review volume indicates strong social proof.')
        elif product.get('num_reviews', 0) >= 200:
            reasons.append('Good review count for trustworthy comparison.')

        if product.get('price') and product['price'] == min_price:
            reasons.append('Best price found in this result set.')

        if not reasons:
            reasons.append('Recommended by the AI ranking engine.')

        product['explanation'] = ' '.join(reasons)
        product['recommendation_strength'] = 'Excellent' if product['final_score'] >= 80 else 'Good' if product['final_score'] >= 60 else 'Fair'
        product['trust_level'] = 'High' if product.get('num_reviews', 0) >= 500 else 'Medium' if product.get('num_reviews', 0) >= 100 else 'Low'

        processed.append(product)

    processed.sort(key=lambda x: x['final_score'], reverse=True)
    return processed
