"""
STEP 1: MODEL PREPARATION FOR PRODUCTION
==========================================
Prepare your trained model for deployment by saving it in production format
"""

import pickle
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class RecommendationModelPrep:
    """
    Prepare recommendation model for production deployment
    """
    
    def __init__(self, model_type='collaborative'):
        """
        model_type: 'collaborative', 'content_based', or 'hybrid'
        """
        self.model_type = model_type
        self.model = None
        self.user_item_matrix = None
        self.item_features = None
        self.metadata = {}
        
    def save_collaborative_model(self, model, user_item_matrix, item_metadata, 
                                 output_dir='models'):
        """
        Save collaborative filtering model (e.g., matrix factorization, ALS)
        
        Args:
            model: Trained model object
            user_item_matrix: User-item interaction matrix
            item_metadata: Product information (id, name, category, etc.)
            output_dir: Directory to save model files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save model
        model_path = f"{output_dir}/recommendation_model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f" Model saved to {model_path}")
        
        # Save user-item matrix
        matrix_path = f"{output_dir}/user_item_matrix.npz"
        if hasattr(user_item_matrix, 'tocsr'):
            # Sparse matrix
            from scipy.sparse import save_npz
            save_npz(matrix_path, user_item_matrix.tocsr())
        else:
            # Dense matrix
            np.savez_compressed(matrix_path, matrix=user_item_matrix)
        print(f" User-item matrix saved to {matrix_path}")
        
        # Save item metadata
        metadata_path = f"{output_dir}/item_metadata.pkl"
        item_metadata.to_pickle(metadata_path)
        print(f"Item metadata saved to {metadata_path}")
        
        # Save configuration
        config = {
            'model_type': self.model_type,
            'created_at': datetime.now().isoformat(),
            'n_users': user_item_matrix.shape[0],
            'n_items': user_item_matrix.shape[1],
            'features': list(item_metadata.columns)
        }
        
        config_path = f"{output_dir}/model_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f" Configuration saved to {config_path}")
        
        return {
            'model_path': model_path,
            'matrix_path': matrix_path,
            'metadata_path': metadata_path,
            'config_path': config_path
        }
    
    def save_content_based_model(self, item_features, similarity_matrix, 
                                 item_metadata, output_dir='models'):
        """
        Save content-based model
        
        Args:
            item_features: Feature vectors for each item
            similarity_matrix: Item-item similarity matrix
            item_metadata: Product information
            output_dir: Directory to save model files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save item features
        features_path = f"{output_dir}/item_features.npz"
        np.savez_compressed(features_path, features=item_features)
        print(f" Item features saved to {features_path}")
        
        # Save similarity matrix
        similarity_path = f"{output_dir}/similarity_matrix.npz"
        if hasattr(similarity_matrix, 'tocsr'):
            from scipy.sparse import save_npz
            save_npz(similarity_path, similarity_matrix.tocsr())
        else:
            np.savez_compressed(similarity_path, matrix=similarity_matrix)
        print(f" Similarity matrix saved to {similarity_path}")
        
        # Save metadata
        metadata_path = f"{output_dir}/item_metadata.pkl"
        item_metadata.to_pickle(metadata_path)
        print(f"Item metadata saved to {metadata_path}")
        
        config = {
            'model_type': 'content_based',
            'created_at': datetime.now().isoformat(),
            'n_items': item_features.shape[0],
            'feature_dim': item_features.shape[1]
        }
        
        config_path = f"{output_dir}/model_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f" Configuration saved to {config_path}")
        
    def load_model(self, model_dir='models'):
        """
        Load saved model for deployment
        """
        # Load configuration
        with open(f"{model_dir}/model_config.json", 'r') as f:
            config = json.load(f)
        
        self.model_type = config['model_type']
        
        if self.model_type == 'collaborative':
            # Load model
            with open(f"{model_dir}/recommendation_model.pkl", 'rb') as f:
                self.model = pickle.load(f)
            
            # Load matrix
            try:
                from scipy.sparse import load_npz
                self.user_item_matrix = load_npz(f"{model_dir}/user_item_matrix.npz")
            except:
                data = np.load(f"{model_dir}/user_item_matrix.npz")
                self.user_item_matrix = data['matrix']
        
        elif self.model_type == 'content_based':
            # Load features and similarity
            features_data = np.load(f"{model_dir}/item_features.npz")
            self.item_features = features_data['features']
            
            try:
                from scipy.sparse import load_npz
                self.similarity_matrix = load_npz(f"{model_dir}/similarity_matrix.npz")
            except:
                sim_data = np.load(f"{model_dir}/similarity_matrix.npz")
                self.similarity_matrix = sim_data['matrix']
        
        # Load metadata
        self.item_metadata = pd.read_pickle(f"{model_dir}/item_metadata.pkl")
        
        print(f" Model loaded successfully ({self.model_type})")
        return self


# Example Usage
if __name__ == "__main__":
    """
    EXAMPLE: How to prepare and save your model
    """
    
    # Example 1: Collaborative Filtering Model
    print("\n=== Example 1: Saving Collaborative Filtering Model ===")
    
    # Simulate a trained model (replace with your actual model)
    from sklearn.decomposition import NMF
    
    # Create dummy data for demonstration
    user_item_matrix = np.random.rand(1000, 500)  # 1000 users, 500 items
    model = NMF(n_components=50, random_state=42)
    model.fit(user_item_matrix)
    
    # Create item metadata
    item_metadata = pd.DataFrame({
        'item_id': range(500),
        'name': [f'Product {i}' for i in range(500)],
        'category': np.random.choice(['Electronics', 'Clothing', 'Books'], 500),
        'price': np.random.uniform(10, 1000, 500)
    })
    
    # Save the model
    prep = RecommendationModelPrep(model_type='collaborative')
    saved_paths = prep.save_collaborative_model(
        model=model,
        user_item_matrix=user_item_matrix,
        item_metadata=item_metadata,
        output_dir='models/production'
    )
    
    print("\n Model saved successfully!")
    print("Saved files:", json.dumps(saved_paths, indent=2))
    
    # Example 2: Load the model back
    print("\n=== Example 2: Loading Model ===")
    loaded_prep = RecommendationModelPrep()
    loaded_prep.load_model('models/production')
    print(f"Model type: {loaded_prep.model_type}")
    print(f"Number of items: {len(loaded_prep.item_metadata)}")
