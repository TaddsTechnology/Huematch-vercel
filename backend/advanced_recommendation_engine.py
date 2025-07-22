import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import NMF
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
from typing import Dict, List, Tuple, Optional
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedRecommendationEngine:
    def __init__(self, data_dir: str = "processed_data"):
        """Initialize the advanced recommendation engine."""
        self.data_dir = Path(data_dir)
        self.makeup_data = None
        self.outfit_data = None
        self.user_interactions = {}
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.content_similarity_matrix = None
        self.nmf_model = None
        self.scaler = StandardScaler()
        
        # Load data
        self._load_data()
        self._prepare_features()
        
    def _load_data(self):
        """Load makeup and outfit data."""
        try:
            # Load makeup data
            makeup_file = self.data_dir / "all_makeup_products.csv"
            if makeup_file.exists():
                self.makeup_data = pd.read_csv(makeup_file)
                logger.info(f"Loaded {len(self.makeup_data)} makeup products")
            
            # Load outfit data
            outfit_file = self.data_dir / "all_combined_outfits.csv"
            if outfit_file.exists():
                self.outfit_data = pd.read_csv(outfit_file)
                logger.info(f"Loaded {len(self.outfit_data)} outfit items")
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            
    def _prepare_features(self):
        """Prepare features for content-based filtering."""
        if self.makeup_data is not None:
            self._prepare_makeup_features()
        if self.outfit_data is not None:
            self._prepare_outfit_features()
            
    def _prepare_makeup_features(self):
        """Prepare features for makeup products."""
        try:
            # Create text features from product information
            text_features = []
            for _, row in self.makeup_data.iterrows():
                text = ""
                if 'product_type' in row and pd.notna(row['product_type']):
                    text += str(row['product_type']) + " "
                if 'brand' in row and pd.notna(row['brand']):
                    text += str(row['brand']) + " "
                if 'category' in row and pd.notna(row['category']):
                    text += str(row['category']) + " "
                text_features.append(text.strip())
            
            # Create TF-IDF matrix
            if text_features:
                self.makeup_tfidf_matrix = self.tfidf_vectorizer.fit_transform(text_features)
                self.makeup_similarity_matrix = cosine_similarity(self.makeup_tfidf_matrix)
                logger.info("Prepared makeup content features")
                
        except Exception as e:
            logger.error(f"Error preparing makeup features: {e}")
            
    def _prepare_outfit_features(self):
        """Prepare features for outfit items."""
        try:
            # Create text features from outfit information
            text_features = []
            for _, row in self.outfit_data.iterrows():
                text = ""
                if 'category' in row and pd.notna(row['category']):
                    text += str(row['category']) + " "
                if 'color' in row and pd.notna(row['color']):
                    text += str(row['color']) + " "
                if 'brand' in row and pd.notna(row['brand']):
                    text += str(row['brand']) + " "
                text_features.append(text.strip())
            
            # Create TF-IDF matrix for outfits
            if text_features:
                outfit_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                self.outfit_tfidf_matrix = outfit_vectorizer.fit_transform(text_features)
                self.outfit_similarity_matrix = cosine_similarity(self.outfit_tfidf_matrix)
                logger.info("Prepared outfit content features")
                
        except Exception as e:
            logger.error(f"Error preparing outfit features: {e}")
            
    def content_based_recommendations(self, product_type: str, item_idx: int, 
                                    n_recommendations: int = 10) -> List[Dict]:
        """Get content-based recommendations."""
        try:
            if product_type == 'makeup' and hasattr(self, 'makeup_similarity_matrix'):
                similarity_matrix = self.makeup_similarity_matrix
                data = self.makeup_data
            elif product_type == 'outfit' and hasattr(self, 'outfit_similarity_matrix'):
                similarity_matrix = self.outfit_similarity_matrix
                data = self.outfit_data
            else:
                return []
            
            if item_idx >= len(similarity_matrix):
                return []
                
            # Get similarity scores
            similarity_scores = similarity_matrix[item_idx]
            
            # Get top similar items
            similar_indices = np.argsort(similarity_scores)[::-1][1:n_recommendations+1]
            
            recommendations = []
            for idx in similar_indices:
                if idx < len(data):
                    item = data.iloc[idx].to_dict()
                    item['similarity_score'] = float(similarity_scores[idx])
                    recommendations.append(item)
                    
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in content-based recommendations: {e}")
            return []
            
    def collaborative_filtering_recommendations(self, user_id: str, 
                                             n_recommendations: int = 10) -> List[Dict]:
        """Get collaborative filtering recommendations."""
        try:
            # This is a simplified version - in production, you'd have user interaction data
            # For now, we'll use a hybrid approach with popularity and content similarity
            
            if self.makeup_data is not None:
                # Get popular items (simplified popularity score)
                popular_items = self.makeup_data.sample(n=min(n_recommendations, len(self.makeup_data)))
                
                recommendations = []
                for _, item in popular_items.iterrows():
                    item_dict = item.to_dict()
                    item_dict['recommendation_score'] = 0.8  # Placeholder score
                    recommendations.append(item_dict)
                    
                return recommendations
            
            return []
            
        except Exception as e:
            logger.error(f"Error in collaborative filtering: {e}")
            return []
            
    def hybrid_recommendations(self, user_profile: Dict, skin_tone: str, 
                             n_recommendations: int = 10) -> Dict[str, List[Dict]]:
        """Get hybrid recommendations combining multiple approaches."""
        try:
            recommendations = {
                'makeup': [],
                'outfits': []
            }
            
            # Filter by skin tone for makeup
            if self.makeup_data is not None:
                makeup_filtered = self._filter_by_skin_tone(self.makeup_data, skin_tone)
                
                # Add diversity in recommendations
                if len(makeup_filtered) > 0:
                    # Get different product types
                    product_types = makeup_filtered['product_type'].unique() if 'product_type' in makeup_filtered.columns else []
                    
                    for product_type in product_types[:3]:  # Limit to 3 different types
                        type_items = makeup_filtered[makeup_filtered['product_type'] == product_type]
                        if len(type_items) > 0:
                            # Get top items for this type
                            sample_size = min(3, len(type_items))
                            selected_items = type_items.sample(n=sample_size)
                            
                            for _, item in selected_items.iterrows():
                                item_dict = item.to_dict()
                                item_dict['recommendation_reason'] = f'Matches {skin_tone} skin tone'
                                item_dict['confidence_score'] = self._calculate_confidence_score(item_dict, user_profile)
                                recommendations['makeup'].append(item_dict)
            
            # Get outfit recommendations
            if self.outfit_data is not None:
                # Consider season and style preferences
                season = user_profile.get('season', 'Spring')
                style = user_profile.get('style', 'casual')
                
                outfit_filtered = self._filter_outfits_by_preferences(self.outfit_data, season, style)
                
                if len(outfit_filtered) > 0:
                    sample_size = min(n_recommendations, len(outfit_filtered))
                    selected_outfits = outfit_filtered.sample(n=sample_size)
                    
                    for _, item in selected_outfits.iterrows():
                        item_dict = item.to_dict()
                        item_dict['recommendation_reason'] = f'Matches {season} season and {style} style'
                        item_dict['confidence_score'] = self._calculate_confidence_score(item_dict, user_profile)
                        recommendations['outfits'].append(item_dict)
            
            # Sort by confidence score
            recommendations['makeup'] = sorted(recommendations['makeup'], 
                                             key=lambda x: x.get('confidence_score', 0), reverse=True)
            recommendations['outfits'] = sorted(recommendations['outfits'], 
                                              key=lambda x: x.get('confidence_score', 0), reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in hybrid recommendations: {e}")
            return {'makeup': [], 'outfits': []}
            
    def _filter_by_skin_tone(self, data: pd.DataFrame, skin_tone: str) -> pd.DataFrame:
        """Filter products by skin tone compatibility."""
        try:
            # Map Monk skin tones to categories
            tone_mapping = {
                'Monk 1': 'light', 'Monk 2': 'light', 'Monk 3': 'light',
                'Monk 4': 'medium', 'Monk 5': 'medium', 'Monk 6': 'medium',
                'Monk 7': 'deep', 'Monk 8': 'deep', 'Monk 9': 'deep', 'Monk 10': 'deep'
            }
            
            skin_category = tone_mapping.get(skin_tone, 'medium')
            
            # Filter based on skin tone (if column exists)
            if 'skin_tone' in data.columns:
                filtered = data[data['skin_tone'].str.contains(skin_category, case=False, na=False)]
            else:
                # If no specific skin tone column, return all (could be enhanced with color matching)
                filtered = data
                
            return filtered if len(filtered) > 0 else data.sample(n=min(10, len(data)))
            
        except Exception as e:
            logger.error(f"Error filtering by skin tone: {e}")
            return data
            
    def _filter_outfits_by_preferences(self, data: pd.DataFrame, season: str, style: str) -> pd.DataFrame:
        """Filter outfits by seasonal and style preferences."""
        try:
            filtered = data.copy()
            
            # Filter by season if column exists
            if 'season' in data.columns:
                filtered = filtered[filtered['season'].str.contains(season, case=False, na=False)]
            
            # Filter by style if column exists  
            if 'style' in data.columns:
                filtered = filtered[filtered['style'].str.contains(style, case=False, na=False)]
                
            return filtered if len(filtered) > 0 else data.sample(n=min(10, len(data)))
            
        except Exception as e:
            logger.error(f"Error filtering outfits: {e}")
            return data
            
    def _calculate_confidence_score(self, item: Dict, user_profile: Dict) -> float:
        """Calculate confidence score for recommendation."""
        try:
            score = 0.5  # Base score
            
            # Boost score based on matching criteria
            if 'brand' in item and 'preferred_brands' in user_profile:
                if item.get('brand') in user_profile['preferred_brands']:
                    score += 0.2
                    
            if 'price' in item and 'budget_range' in user_profile:
                price = float(item.get('price', 0))
                budget_min, budget_max = user_profile['budget_range']
                if budget_min <= price <= budget_max:
                    score += 0.15
                    
            # Add randomness to avoid identical scores
            score += np.random.uniform(-0.1, 0.1)
            
            return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
            
    def get_personalized_recommendations(self, skin_tone: str, user_preferences: Dict = None, 
                                       n_recommendations: int = 10) -> Dict:
        """Get personalized recommendations for a user."""
        try:
            if user_preferences is None:
                user_preferences = {
                    'season': 'Spring',
                    'style': 'casual',
                    'preferred_brands': [],
                    'budget_range': [0, 100]
                }
            
            # Get hybrid recommendations
            recommendations = self.hybrid_recommendations(
                user_profile=user_preferences,
                skin_tone=skin_tone,
                n_recommendations=n_recommendations
            )
            
            # Add metadata
            result = {
                'recommendations': recommendations,
                'metadata': {
                    'skin_tone': skin_tone,
                    'total_makeup_items': len(recommendations['makeup']),
                    'total_outfit_items': len(recommendations['outfits']),
                    'recommendation_method': 'hybrid',
                    'user_preferences': user_preferences
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return {'recommendations': {'makeup': [], 'outfits': []}, 'metadata': {}}
            
    def add_user_feedback(self, user_id: str, item_id: str, rating: float, 
                         interaction_type: str = 'rating'):
        """Add user feedback for collaborative filtering."""
        try:
            if user_id not in self.user_interactions:
                self.user_interactions[user_id] = {}
                
            self.user_interactions[user_id][item_id] = {
                'rating': rating,
                'interaction_type': interaction_type,
                'timestamp': pd.Timestamp.now()
            }
            
            logger.info(f"Added feedback for user {user_id}, item {item_id}")
            
        except Exception as e:
            logger.error(f"Error adding user feedback: {e}")
            
    def get_trending_items(self, product_type: str = 'makeup', n_items: int = 10) -> List[Dict]:
        """Get trending items (simplified version)."""
        try:
            if product_type == 'makeup' and self.makeup_data is not None:
                # For now, return random sample as "trending"
                # In production, this would use actual trend data
                trending = self.makeup_data.sample(n=min(n_items, len(self.makeup_data)))
                
                result = []
                for _, item in trending.iterrows():
                    item_dict = item.to_dict()
                    item_dict['trend_score'] = np.random.uniform(0.7, 1.0)
                    result.append(item_dict)
                    
                return sorted(result, key=lambda x: x['trend_score'], reverse=True)
            
            elif product_type == 'outfit' and self.outfit_data is not None:
                trending = self.outfit_data.sample(n=min(n_items, len(self.outfit_data)))
                
                result = []
                for _, item in trending.iterrows():
                    item_dict = item.to_dict()
                    item_dict['trend_score'] = np.random.uniform(0.7, 1.0)
                    result.append(item_dict)
                    
                return sorted(result, key=lambda x: x['trend_score'], reverse=True)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting trending items: {e}")
            return []

# Initialize global recommendation engine
recommendation_engine = None

def get_recommendation_engine():
    """Get global recommendation engine instance."""
    global recommendation_engine
    if recommendation_engine is None:
        recommendation_engine = AdvancedRecommendationEngine()
    return recommendation_engine

if __name__ == "__main__":
    # Test the recommendation engine
    engine = AdvancedRecommendationEngine()
    
    # Test personalized recommendations
    recommendations = engine.get_personalized_recommendations(
        skin_tone="Monk 3",
        user_preferences={
            'season': 'Summer',
            'style': 'professional',
            'preferred_brands': ['Sephora'],
            'budget_range': [20, 80]
        }
    )
    
    print("Personalized Recommendations:")
    print(f"Makeup items: {len(recommendations['recommendations']['makeup'])}")
    print(f"Outfit items: {len(recommendations['recommendations']['outfits'])}")
