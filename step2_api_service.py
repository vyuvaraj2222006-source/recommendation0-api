"""
STEP 2: CREATE RECOMMENDATION API SERVICE
=========================================
Flask API to serve real-time recommendations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
import pickle
import json
import logging
from functools import lru_cache
import redis
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for web integration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model
MODEL = None
USER_ITEM_MATRIX = None
ITEM_METADATA = None
SIMILARITY_MATRIX = None
CONFIG = None

# Redis cache configuration (optional but recommended)
REDIS_ENABLED = False
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_ENABLED = True
    logger.info(" Redis cache connected")
except:
    logger.warning(" Redis not available, running without cache")
    redis_client = None


def load_model(model_dir='models/production'):
    """Load model on startup"""
    global MODEL, USER_ITEM_MATRIX, ITEM_METADATA, SIMILARITY_MATRIX, CONFIG
    
    logger.info("Loading model...")
    
    # Load configuration
    with open(f"{model_dir}/model_config.json", 'r') as f:
        CONFIG = json.load(f)
    
    # Load item metadata
    ITEM_METADATA = pd.read_pickle(f"{model_dir}/item_metadata.pkl")
    
    # Load model based on type
    if CONFIG['model_type'] == 'collaborative':
        with open(f"{model_dir}/recommendation_model.pkl", 'rb') as f:
            MODEL = pickle.load(f)
        
        try:
            from scipy.sparse import load_npz
            USER_ITEM_MATRIX = load_npz(f"{model_dir}/user_item_matrix.npz")
        except:
            data = np.load(f"{model_dir}/user_item_matrix.npz")
            USER_ITEM_MATRIX = data['matrix']
    
    elif CONFIG['model_type'] == 'content_based':
        features_data = np.load(f"{model_dir}/item_features.npz")
        try:
            from scipy.sparse import load_npz
            SIMILARITY_MATRIX = load_npz(f"{model_dir}/similarity_matrix.npz")
        except:
            sim_data = np.load(f"{model_dir}/similarity_matrix.npz")
            SIMILARITY_MATRIX = sim_data['matrix']
    
    logger.info(f"✓ Model loaded successfully ({CONFIG['model_type']})")


def get_cached_recommendations(cache_key):
    """Get recommendations from cache"""
    if not REDIS_ENABLED:
        return None
    
    try:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return json.loads(cached)
    except Exception as e:
        logger.error(f"Cache retrieval error: {e}")
    
    return None


def set_cached_recommendations(cache_key, recommendations, ttl=3600):
    """Cache recommendations for 1 hour"""
    if not REDIS_ENABLED:
        return
    
    try:
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(recommendations)
        )
    except Exception as e:
        logger.error(f"Cache storage error: {e}")


def get_collaborative_recommendations(user_id, n_recommendations=10, exclude_items=None):
    """
    Get recommendations using collaborative filtering
    """
    if user_id >= USER_ITEM_MATRIX.shape[0]:
        # New user - return popular items
        return get_popular_items(n_recommendations)
    
    # Get user's row from matrix
    user_vector = USER_ITEM_MATRIX[user_id].toarray().flatten() if hasattr(USER_ITEM_MATRIX, 'toarray') else USER_ITEM_MATRIX[user_id]
    
    # Get user and item factors from model
    if hasattr(MODEL, 'components_'):
        # NMF or similar
        user_factors = MODEL.transform(user_vector.reshape(1, -1))
        item_factors = MODEL.components_.T
        scores = user_factors.dot(item_factors.T).flatten()
    elif hasattr(MODEL, 'predict'):
        # Custom model with predict method
        scores = np.array([MODEL.predict(user_id, item_id) for item_id in range(USER_ITEM_MATRIX.shape[1])])
    else:
        # Fallback: use similarity-based approach
        scores = user_vector
    
    # Exclude already interacted items
    interacted_items = np.where(user_vector > 0)[0]
    scores[interacted_items] = -np.inf
    
    # Exclude specific items if provided
    if exclude_items:
        scores[exclude_items] = -np.inf
    
    # Get top N items
    top_items = np.argsort(scores)[::-1][:n_recommendations]
    
    return top_items.tolist()


def get_content_based_recommendations(item_id, n_recommendations=10):
    """
    Get similar items using content-based filtering
    """
    if item_id >= SIMILARITY_MATRIX.shape[0]:
        return get_popular_items(n_recommendations)
    
    # Get similarity scores
    if hasattr(SIMILARITY_MATRIX, 'toarray'):
        similarities = SIMILARITY_MATRIX[item_id].toarray().flatten()
    else:
        similarities = SIMILARITY_MATRIX[item_id]
    
    # Exclude the item itself
    similarities[item_id] = -np.inf
    
    # Get top N similar items
    top_items = np.argsort(similarities)[::-1][:n_recommendations]
    
    return top_items.tolist()


def get_popular_items(n_items=10):
    """
    Fallback: Get most popular items (for cold start)
    """
    # Simple popularity based on metadata (you can enhance this)
    if 'popularity_score' in ITEM_METADATA.columns:
        popular = ITEM_METADATA.nlargest(n_items, 'popularity_score')
    else:
        popular = ITEM_METADATA.head(n_items)
    
    return popular['item_id'].tolist()


def format_recommendations(item_ids):
    """
    Format item IDs into full product details
    """
    recommendations = []
    
    for item_id in item_ids:
        if item_id < len(ITEM_METADATA):
            item = ITEM_METADATA.iloc[item_id]
            recommendations.append({
                'item_id': int(item_id),
                'name': item.get('name', f'Product {item_id}'),
                'category': item.get('category', 'Unknown'),
                'price': float(item.get('price', 0)),
                'image_url': item.get('image_url', ''),
                'rating': float(item.get('rating', 0)) if 'rating' in item else None
            })
    
    return recommendations


# ============ API ENDPOINTS ============

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_type': CONFIG['model_type'] if CONFIG else 'not_loaded',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/recommendations/user/<int:user_id>', methods=['GET'])
def recommend_for_user(user_id):
    """
    Get personalized recommendations for a user
    
    Query params:
        - n: number of recommendations (default: 10)
        - exclude: comma-separated list of item IDs to exclude
    """
    try:
        # Parse parameters
        n_recommendations = int(request.args.get('n', 10))
        exclude_items = request.args.get('exclude', '')
        exclude_list = [int(x) for x in exclude_items.split(',') if x.strip()] if exclude_items else None
        
        # Check cache
        cache_key = f"user:{user_id}:n:{n_recommendations}:exclude:{exclude_items}"
        cached = get_cached_recommendations(cache_key)
        if cached:
            return jsonify(cached)
        
        # Get recommendations
        if CONFIG['model_type'] == 'collaborative':
            item_ids = get_collaborative_recommendations(user_id, n_recommendations, exclude_list)
        else:
            # For content-based, we need a seed item (use popular as fallback)
            item_ids = get_popular_items(n_recommendations)
        
        recommendations = format_recommendations(item_ids)
        
        response = {
            'user_id': user_id,
            'recommendations': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache the result
        set_cached_recommendations(cache_key, response)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in recommend_for_user: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/recommendations/similar/<int:item_id>', methods=['GET'])
def recommend_similar_items(item_id):
    """
    Get similar items (for "customers who viewed this also viewed")
    
    Query params:
        - n: number of recommendations (default: 10)
    """
    try:
        n_recommendations = int(request.args.get('n', 10))
        
        # Check cache
        cache_key = f"similar:{item_id}:n:{n_recommendations}"
        cached = get_cached_recommendations(cache_key)
        if cached:
            return jsonify(cached)
        
        # Get similar items
        if CONFIG['model_type'] == 'content_based' and SIMILARITY_MATRIX is not None:
            item_ids = get_content_based_recommendations(item_id, n_recommendations)
        else:
            # Fallback to popular items
            item_ids = get_popular_items(n_recommendations)
        
        recommendations = format_recommendations(item_ids)
        
        response = {
            'item_id': item_id,
            'similar_items': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache the result
        set_cached_recommendations(cache_key, response)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in recommend_similar_items: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/recommendations/popular', methods=['GET'])
def recommend_popular():
    """
    Get popular items (for homepage, new users)
    """
    try:
        n_recommendations = int(request.args.get('n', 10))
        category = request.args.get('category', None)
        
        # Check cache
        cache_key = f"popular:n:{n_recommendations}:cat:{category}"
        cached = get_cached_recommendations(cache_key)
        if cached:
            return jsonify(cached)
        
        # Filter by category if specified
        if category:
            filtered_items = ITEM_METADATA[ITEM_METADATA['category'] == category]
            item_ids = filtered_items.head(n_recommendations)['item_id'].tolist()
        else:
            item_ids = get_popular_items(n_recommendations)
        
        recommendations = format_recommendations(item_ids)
        
        response = {
            'type': 'popular',
            'category': category,
            'recommendations': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache the result
        set_cached_recommendations(cache_key, response, ttl=7200)  # 2 hours
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in recommend_popular: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/batch_recommendations', methods=['POST'])
def batch_recommendations():
    """
    Get recommendations for multiple users at once
    
    Request body:
    {
        "user_ids": [1, 2, 3, 4],
        "n": 5
    }
    """
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        n_recommendations = data.get('n', 10)
        
        results = {}
        for user_id in user_ids:
            if CONFIG['model_type'] == 'collaborative':
                item_ids = get_collaborative_recommendations(user_id, n_recommendations)
            else:
                item_ids = get_popular_items(n_recommendations)
            
            results[user_id] = format_recommendations(item_ids)
        
        return jsonify({
            'results': results,
            'count': len(results),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in batch_recommendations: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Load model on startup
    load_model('models/production')
    
    # Run the Flask app
    # For production, use gunicorn or uwsgi instead
    app.run(host='0.0.0.0', port=5000, debug=False)
