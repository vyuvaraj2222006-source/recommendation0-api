"""
STEP 2: API SERVICE - CLOUD DEPLOYMENT VERSION
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
import pickle
import json
import logging
from datetime import datetime
import traceback

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
MODEL = None
USER_ITEM_MATRIX = None
ITEM_METADATA = None
CONFIG = None

def load_model(model_dir='models/production'):
    """Load model on startup"""
    global MODEL, USER_ITEM_MATRIX, ITEM_METADATA, CONFIG
    
    logger.info("Loading model...")
    
    try:
        with open(f"{model_dir}/model_config.json", 'r') as f:
            CONFIG = json.load(f)
        
        ITEM_METADATA = pd.read_pickle(f"{model_dir}/item_metadata.pkl")
        logger.info(f"✓ Loaded {len(ITEM_METADATA)} items")
        
        if CONFIG['model_type'] == 'collaborative':
            with open(f"{model_dir}/recommendation_model.pkl", 'rb') as f:
                MODEL = pickle.load(f)
            
            try:
                from scipy.sparse import load_npz
                USER_ITEM_MATRIX = load_npz(f"{model_dir}/user_item_matrix.npz")
            except:
                data = np.load(f"{model_dir}/user_item_matrix.npz")
                USER_ITEM_MATRIX = data['matrix']
        
        logger.info(f"✓ Model loaded successfully ({CONFIG['model_type']})")
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        logger.error(traceback.format_exc())


def get_popular_items(n_items=10):
    """Get popular items"""
    try:
        if ITEM_METADATA is None:
            return []
        return list(range(min(n_items, len(ITEM_METADATA))))
    except:
        return list(range(10))


def get_collaborative_recommendations(user_id, n_recommendations=10, exclude_items=None):
    """Get collaborative filtering recommendations"""
    try:
        if USER_ITEM_MATRIX is None or user_id >= USER_ITEM_MATRIX.shape[0]:
            return get_popular_items(n_recommendations)
        
        user_vector = USER_ITEM_MATRIX[user_id].toarray().flatten() if hasattr(USER_ITEM_MATRIX, 'toarray') else USER_ITEM_MATRIX[user_id]
        
        if hasattr(MODEL, 'components_'):
            user_factors = MODEL.transform(user_vector.reshape(1, -1))
            item_factors = MODEL.components_.T
            scores = user_factors.dot(item_factors.T).flatten()
        else:
            scores = user_vector
        
        interacted_items = np.where(user_vector > 0)[0]
        scores[interacted_items] = -np.inf
        
        if exclude_items:
            for item in exclude_items:
                if item < len(scores):
                    scores[item] = -np.inf
        
        top_items = np.argsort(scores)[::-1][:n_recommendations]
        return top_items.tolist()
        
    except Exception as e:
        logger.error(f"Error in recommendations: {e}")
        return get_popular_items(n_recommendations)


def format_recommendations(item_ids):
    """Format recommendations"""
    recommendations = []
    
    try:
        if ITEM_METADATA is None:
            return recommendations
        
        for item_id in item_ids:
            if item_id < len(ITEM_METADATA):
                item = ITEM_METADATA.iloc[item_id]
                rec = {
                    'item_id': int(item_id),
                    'name': str(item.get('name', f'Product {item_id}')),
                    'category': str(item.get('category', 'Unknown')),
                }
                
                if 'price' in item:
                    try:
                        rec['price'] = float(item['price'])
                    except:
                        rec['price'] = 0.0
                
                recommendations.append(rec)
    except Exception as e:
        logger.error(f"Error formatting: {e}")
    
    return recommendations


@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': MODEL is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/recommendations/user/<int:user_id>', methods=['GET'])
def recommend_for_user(user_id):
    """Get user recommendations"""
    try:
        n_recommendations = int(request.args.get('n', 10))
        exclude_items = request.args.get('exclude', '')
        exclude_list = [int(x) for x in exclude_items.split(',') if x.strip()] if exclude_items else None
        
        if CONFIG and CONFIG['model_type'] == 'collaborative':
            item_ids = get_collaborative_recommendations(user_id, n_recommendations, exclude_list)
        else:
            item_ids = get_popular_items(n_recommendations)
        
        recommendations = format_recommendations(item_ids)
        
        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/recommendations/popular', methods=['GET'])
def recommend_popular():
    """Get popular items"""
    try:
        n_items = int(request.args.get('n', 12))
        item_ids = get_popular_items(n_items)
        recommendations = format_recommendations(item_ids)
        
        return jsonify({
            'popular_items': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/recommendations/similar/<int:item_id>', methods=['GET'])
def recommend_similar_items(item_id):
    """Get similar items"""
    try:
        n_recommendations = int(request.args.get('n', 8))
        item_ids = get_popular_items(n_recommendations)
        recommendations = format_recommendations(item_ids)
        
        return jsonify({
            'item_id': item_id,
            'similar_items': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    load_model()
    # Get port from environment variable (for cloud deployment)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
