"""
A/B Testing System for Recommendation Algorithms
"""

import uuid
import random
import json
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import pandas as pd
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class RecommendationAlgorithm(Enum):
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    POPULARITY_BASED = "popularity_based"
    ENHANCED_ML = "enhanced_ml"

@dataclass
class ExperimentConfig:
    """Configuration for A/B test experiment"""
    experiment_id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    algorithms: Dict[str, RecommendationAlgorithm]  # variant_name -> algorithm
    traffic_allocation: Dict[str, float]  # variant_name -> percentage
    success_metrics: List[str]
    minimum_sample_size: int = 100
    confidence_level: float = 0.95

@dataclass
class UserAssignment:
    """User assignment to experiment variant"""
    user_id: str
    experiment_id: str
    variant: str
    assigned_at: datetime
    algorithm: RecommendationAlgorithm

@dataclass
class ExperimentEvent:
    """Event tracking for A/B test"""
    event_id: str
    user_id: str
    experiment_id: str
    variant: str
    event_type: str  # 'view', 'click', 'purchase', 'rating'
    event_data: Dict[str, Any]
    timestamp: datetime

@dataclass
class ExperimentResults:
    """Results of A/B test experiment"""
    experiment_id: str
    variant_results: Dict[str, Dict[str, float]]  # variant -> metric -> value
    statistical_significance: Dict[str, bool]  # metric -> is_significant
    confidence_intervals: Dict[str, Dict[str, Tuple[float, float]]]  # variant -> metric -> (lower, upper)
    sample_sizes: Dict[str, int]  # variant -> sample_size
    winner: Optional[str] = None

class ABTestingSystem:
    """A/B Testing system for recommendation algorithms"""
    
    def __init__(self):
        self.experiments: Dict[str, ExperimentConfig] = {}
        self.user_assignments: Dict[str, List[UserAssignment]] = {}
        self.experiment_events: Dict[str, List[ExperimentEvent]] = {}
        self.results: Dict[str, ExperimentResults] = {}
        
        # Algorithm implementations
        self.algorithm_implementations = {
            RecommendationAlgorithm.COLLABORATIVE_FILTERING: self._collaborative_filtering_recommendations,
            RecommendationAlgorithm.CONTENT_BASED: self._content_based_recommendations,
            RecommendationAlgorithm.HYBRID: self._hybrid_recommendations,
            RecommendationAlgorithm.POPULARITY_BASED: self._popularity_based_recommendations,
            RecommendationAlgorithm.ENHANCED_ML: self._enhanced_ml_recommendations
        }
    
    def create_experiment(self, config: ExperimentConfig) -> str:
        """Create a new A/B test experiment"""
        # Validate configuration
        if sum(config.traffic_allocation.values()) != 1.0:
            raise ValueError("Traffic allocation must sum to 1.0")
        
        if len(config.algorithms) != len(config.traffic_allocation):
            raise ValueError("Number of algorithms must match number of traffic allocations")
        
        # Store experiment
        self.experiments[config.experiment_id] = config
        self.experiment_events[config.experiment_id] = []
        
        logger.info(f"Created A/B test experiment: {config.name} ({config.experiment_id})")
        return config.experiment_id
    
    def assign_user_to_variant(self, user_id: str, experiment_id: str) -> UserAssignment:
        """Assign user to experiment variant using consistent hashing"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        # Check if user already assigned
        if user_id in self.user_assignments:
            for assignment in self.user_assignments[user_id]:
                if assignment.experiment_id == experiment_id:
                    return assignment
        
        # Use consistent hashing for assignment
        hash_input = f"{user_id}:{experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) / (16**32)
        
        # Determine variant based on traffic allocation
        cumulative_allocation = 0
        selected_variant = None
        
        for variant, allocation in experiment.traffic_allocation.items():
            cumulative_allocation += allocation
            if hash_value <= cumulative_allocation:
                selected_variant = variant
                break
        
        if not selected_variant:
            selected_variant = list(experiment.traffic_allocation.keys())[-1]
        
        # Create assignment
        assignment = UserAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant=selected_variant,
            assigned_at=datetime.now(),
            algorithm=experiment.algorithms[selected_variant]
        )
        
        # Store assignment
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = []
        self.user_assignments[user_id].append(assignment)
        
        logger.debug(f"Assigned user {user_id} to variant {selected_variant} in experiment {experiment_id}")
        return assignment
    
    def get_recommendations_for_user(self, user_id: str, experiment_id: str, 
                                   skin_tone: str, user_preferences: Dict,
                                   n_recommendations: int = 10) -> Dict[str, Any]:
        """Get recommendations for user based on their A/B test assignment"""
        # Get user assignment
        assignment = self.assign_user_to_variant(user_id, experiment_id)
        
        # Get recommendations using assigned algorithm
        algorithm_func = self.algorithm_implementations[assignment.algorithm]
        recommendations = algorithm_func(skin_tone, user_preferences, n_recommendations)
        
        # Track view event
        self.track_event(
            user_id=user_id,
            experiment_id=experiment_id,
            event_type='view',
            event_data={
                'n_recommendations': n_recommendations,
                'skin_tone': skin_tone
            }
        )
        
        return {
            'recommendations': recommendations,
            'variant': assignment.variant,
            'algorithm': assignment.algorithm.value,
            'experiment_id': experiment_id
        }
    
    def track_event(self, user_id: str, experiment_id: str, event_type: str,
                   event_data: Dict[str, Any] = None) -> str:
        """Track an event for A/B testing analysis"""
        if experiment_id not in self.experiments:
            logger.warning(f"Attempt to track event for unknown experiment: {experiment_id}")
            return None
        
        # Get user assignment
        assignment = None
        if user_id in self.user_assignments:
            for assign in self.user_assignments[user_id]:
                if assign.experiment_id == experiment_id:
                    assignment = assign
                    break
        
        if not assignment:
            logger.warning(f"User {user_id} not assigned to experiment {experiment_id}")
            return None
        
        # Create event
        event = ExperimentEvent(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            experiment_id=experiment_id,
            variant=assignment.variant,
            event_type=event_type,
            event_data=event_data or {},
            timestamp=datetime.now()
        )
        
        # Store event
        self.experiment_events[experiment_id].append(event)
        
        logger.debug(f"Tracked {event_type} event for user {user_id} in experiment {experiment_id}")
        return event.event_id
    
    def analyze_experiment(self, experiment_id: str) -> ExperimentResults:
        """Analyze A/B test experiment results"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        events = self.experiment_events.get(experiment_id, [])
        
        # Convert events to DataFrame for analysis
        events_data = []
        for event in events:
            events_data.append({
                'user_id': event.user_id,
                'variant': event.variant,
                'event_type': event.event_type,
                'timestamp': event.timestamp,
                **event.event_data
            })
        
        if not events_data:
            logger.warning(f"No events found for experiment {experiment_id}")
            return ExperimentResults(
                experiment_id=experiment_id,
                variant_results={},
                statistical_significance={},
                confidence_intervals={},
                sample_sizes={}
            )
        
        df = pd.DataFrame(events_data)
        
        # Calculate metrics for each variant
        variant_results = {}
        sample_sizes = {}
        
        for variant in experiment.traffic_allocation.keys():
            variant_data = df[df['variant'] == variant]
            sample_sizes[variant] = len(variant_data['user_id'].unique())
            
            # Calculate conversion metrics
            total_views = len(variant_data[variant_data['event_type'] == 'view'])
            total_clicks = len(variant_data[variant_data['event_type'] == 'click'])
            total_purchases = len(variant_data[variant_data['event_type'] == 'purchase'])
            
            click_through_rate = (total_clicks / total_views) if total_views > 0 else 0
            conversion_rate = (total_purchases / total_views) if total_views > 0 else 0
            
            # Calculate engagement metrics
            avg_rating = variant_data[variant_data['event_type'] == 'rating']['rating'].mean() if 'rating' in variant_data.columns else 0
            
            variant_results[variant] = {
                'click_through_rate': click_through_rate,
                'conversion_rate': conversion_rate,
                'average_rating': avg_rating or 0,
                'total_views': total_views,
                'total_clicks': total_clicks,
                'total_purchases': total_purchases
            }
        
        # Perform statistical significance testing
        statistical_significance = {}
        confidence_intervals = {}
        
        for metric in ['click_through_rate', 'conversion_rate', 'average_rating']:
            statistical_significance[metric] = self._test_statistical_significance(
                variant_results, metric, sample_sizes, experiment.confidence_level
            )
            confidence_intervals[metric] = self._calculate_confidence_intervals(
                variant_results, metric, sample_sizes, experiment.confidence_level
            )
        
        # Determine winner
        winner = self._determine_winner(variant_results, statistical_significance)
        
        results = ExperimentResults(
            experiment_id=experiment_id,
            variant_results=variant_results,
            statistical_significance=statistical_significance,
            confidence_intervals=confidence_intervals,
            sample_sizes=sample_sizes,
            winner=winner
        )
        
        self.results[experiment_id] = results
        return results
    
    def _test_statistical_significance(self, variant_results: Dict, metric: str,
                                     sample_sizes: Dict, confidence_level: float) -> bool:
        """Test statistical significance using chi-square test (simplified)"""
        # This is a simplified implementation
        # In production, use proper statistical tests like t-test or chi-square
        
        if len(variant_results) != 2:
            return False  # Only handle 2-variant tests for now
        
        variants = list(variant_results.keys())
        value1 = variant_results[variants[0]][metric]
        value2 = variant_results[variants[1]][metric]
        
        # Simple check: difference > 5% with reasonable sample size
        min_sample_size = min(sample_sizes.values())
        difference = abs(value1 - value2)
        
        return difference > 0.05 and min_sample_size >= 50
    
    def _calculate_confidence_intervals(self, variant_results: Dict, metric: str,
                                      sample_sizes: Dict, confidence_level: float) -> Dict:
        """Calculate confidence intervals for metrics (simplified)"""
        confidence_intervals = {}
        
        for variant, results in variant_results.items():
            value = results[metric]
            sample_size = sample_sizes[variant]
            
            # Simplified confidence interval calculation
            if sample_size > 0:
                margin_of_error = 1.96 * (value * (1 - value) / sample_size) ** 0.5
                confidence_intervals[variant] = (
                    max(0, value - margin_of_error),
                    min(1, value + margin_of_error)
                )
            else:
                confidence_intervals[variant] = (0, 0)
        
        return confidence_intervals
    
    def _determine_winner(self, variant_results: Dict, statistical_significance: Dict) -> Optional[str]:
        """Determine the winning variant based on results"""
        # Simple winner determination based on conversion rate
        if not statistical_significance.get('conversion_rate', False):
            return None  # No statistically significant winner
        
        best_variant = None
        best_conversion = -1
        
        for variant, results in variant_results.items():
            if results['conversion_rate'] > best_conversion:
                best_conversion = results['conversion_rate']
                best_variant = variant
        
        return best_variant
    
    # Algorithm implementations for A/B testing
    def _collaborative_filtering_recommendations(self, skin_tone: str, user_preferences: Dict,
                                               n_recommendations: int) -> Dict:
        """Collaborative filtering algorithm implementation"""
        from advanced_recommendation_engine import get_recommendation_engine
        rec_engine = get_recommendation_engine()
        return rec_engine.collaborative_filtering_recommendations("user_123", n_recommendations)
    
    def _content_based_recommendations(self, skin_tone: str, user_preferences: Dict,
                                     n_recommendations: int) -> Dict:
        """Content-based filtering algorithm implementation"""
        from advanced_recommendation_engine import get_recommendation_engine
        rec_engine = get_recommendation_engine()
        return rec_engine.content_based_recommendations('makeup', 0, n_recommendations)
    
    def _hybrid_recommendations(self, skin_tone: str, user_preferences: Dict,
                              n_recommendations: int) -> Dict:
        """Hybrid algorithm implementation"""
        from advanced_recommendation_engine import get_recommendation_engine
        rec_engine = get_recommendation_engine()
        return rec_engine.get_personalized_recommendations(skin_tone, user_preferences, n_recommendations)
    
    def _popularity_based_recommendations(self, skin_tone: str, user_preferences: Dict,
                                        n_recommendations: int) -> Dict:
        """Popularity-based algorithm implementation"""
        from advanced_recommendation_engine import get_recommendation_engine
        rec_engine = get_recommendation_engine()
        return rec_engine.get_trending_items('makeup', n_recommendations)
    
    def _enhanced_ml_recommendations(self, skin_tone: str, user_preferences: Dict,
                                   n_recommendations: int) -> Dict:
        """Enhanced ML algorithm implementation"""
        # This would be your most advanced algorithm
        from advanced_recommendation_engine import get_recommendation_engine
        rec_engine = get_recommendation_engine()
        
        # Enhanced version with additional ML features
        recommendations = rec_engine.get_personalized_recommendations(skin_tone, user_preferences, n_recommendations)
        
        # Add ML enhancements (placeholder)
        if 'recommendations' in recommendations:
            for category in recommendations['recommendations']:
                for item in recommendations['recommendations'][category]:
                    item['ml_score'] = random.uniform(0.8, 1.0)  # Enhanced ML score
        
        return recommendations
    
    def get_experiment_summary(self, experiment_id: str) -> Dict:
        """Get summary of experiment status and key metrics"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        # Count users per variant
        variant_counts = {}
        for variant in experiment.traffic_allocation.keys():
            variant_counts[variant] = 0
        
        if experiment_id in self.user_assignments:
            for assignments in self.user_assignments.values():
                for assignment in assignments:
                    if assignment.experiment_id == experiment_id:
                        variant_counts[assignment.variant] += 1
        
        # Get latest results if available
        results = self.results.get(experiment_id)
        
        return {
            'experiment_id': experiment_id,
            'name': experiment.name,
            'status': 'running' if datetime.now() < experiment.end_date else 'completed',
            'start_date': experiment.start_date.isoformat(),
            'end_date': experiment.end_date.isoformat(),
            'variants': list(experiment.algorithms.keys()),
            'user_counts': variant_counts,
            'total_events': len(self.experiment_events.get(experiment_id, [])),
            'has_results': results is not None,
            'winner': results.winner if results else None
        }

# Global A/B testing system instance
ab_testing_system = ABTestingSystem()

# Helper functions for easy integration
def create_ab_test(name: str, description: str, variants: Dict[str, RecommendationAlgorithm],
                   traffic_split: Dict[str, float], duration_days: int = 30) -> str:
    """Create an A/B test experiment"""
    experiment_id = str(uuid.uuid4())
    
    config = ExperimentConfig(
        experiment_id=experiment_id,
        name=name,
        description=description,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=duration_days),
        algorithms=variants,
        traffic_allocation=traffic_split,
        success_metrics=['click_through_rate', 'conversion_rate', 'average_rating'],
        minimum_sample_size=100
    )
    
    return ab_testing_system.create_experiment(config)

def get_ab_test_recommendations(user_id: str, experiment_id: str, skin_tone: str,
                               user_preferences: Dict, n_recommendations: int = 10) -> Dict:
    """Get recommendations for A/B test"""
    return ab_testing_system.get_recommendations_for_user(
        user_id, experiment_id, skin_tone, user_preferences, n_recommendations
    )

def track_ab_test_event(user_id: str, experiment_id: str, event_type: str,
                       event_data: Dict = None) -> str:
    """Track an A/B test event"""
    return ab_testing_system.track_event(user_id, experiment_id, event_type, event_data)

if __name__ == "__main__":
    # Example usage
    ab_system = ABTestingSystem()
    
    # Create experiment
    experiment_id = create_ab_test(
        name="Recommendation Algorithm Test",
        description="Test hybrid vs collaborative filtering",
        variants={
            'control': RecommendationAlgorithm.COLLABORATIVE_FILTERING,
            'treatment': RecommendationAlgorithm.HYBRID
        },
        traffic_split={
            'control': 0.5,
            'treatment': 0.5
        },
        duration_days=14
    )
    
    print(f"Created experiment: {experiment_id}")
    
    # Test user assignment
    user_id = "test_user_123"
    recommendations = get_ab_test_recommendations(
        user_id=user_id,
        experiment_id=experiment_id,
        skin_tone="Monk 3",
        user_preferences={'season': 'Summer', 'style': 'casual'},
        n_recommendations=5
    )
    
    print(f"User assigned to variant: {recommendations['variant']}")
    
    # Track events
    track_ab_test_event(user_id, experiment_id, 'click', {'item_id': 'product_123'})
    track_ab_test_event(user_id, experiment_id, 'purchase', {'item_id': 'product_123', 'price': 29.99})
    
    # Get experiment summary
    summary = ab_system.get_experiment_summary(experiment_id)
    print("Experiment summary:", json.dumps(summary, indent=2))
