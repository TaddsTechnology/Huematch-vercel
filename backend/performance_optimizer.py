"""
Performance optimization module with caching, batch processing, and memory management
"""

import redis
import pickle
import hashlib
import time
from typing import Any, Dict, List, Optional, Callable
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from functools import wraps
import json
import numpy as np
from dataclasses import dataclass
import threading
import os

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Configuration for caching system"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    default_expiry: int = 3600  # 1 hour
    max_memory: str = "512mb"
    
class PerformanceOptimizer:
    """Performance optimization with caching and batch processing"""
    
    def __init__(self, cache_config: Optional[CacheConfig] = None):
        self.cache_config = cache_config or CacheConfig()
        self.redis_client = None
        self.local_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}
        self.batch_queue = []
        self.batch_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize Redis connection
        self._init_redis()
        
    def _init_redis(self):
        """Initialize Redis connection with fallback to local cache"""
        try:
            self.redis_client = redis.Redis(
                host=self.cache_config.redis_host,
                port=self.cache_config.redis_port,
                db=self.cache_config.redis_db,
                decode_responses=False
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            # Silently fall back to local cache for production deployment
            if "production" not in os.environ.get("ENV", "").lower():
                logger.info(f"Redis not available, using local cache: {e}")
            self.redis_client = None
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate unique cache key from arguments"""
        # Create a string representation of all arguments
        key_data = str(args) + str(sorted(kwargs.items()))
        # Hash for consistent length and avoid special characters
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or local)"""
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    self.cache_stats["hits"] += 1
                    return pickle.loads(cached_data)
            else:
                if key in self.local_cache:
                    # Check expiry for local cache
                    cached_item = self.local_cache[key]
                    if time.time() < cached_item["expiry"]:
                        self.cache_stats["hits"] += 1
                        return cached_item["data"]
                    else:
                        del self.local_cache[key]
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    def set_cache(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """Set value in cache"""
        expiry = expiry or self.cache_config.default_expiry
        
        try:
            if self.redis_client:
                pickled_data = pickle.dumps(value)
                return self.redis_client.setex(key, expiry, pickled_data)
            else:
                # Local cache with expiry
                self.local_cache[key] = {
                    "data": value,
                    "expiry": time.time() + expiry
                }
                # Cleanup old entries if cache gets too large
                if len(self.local_cache) > 1000:
                    self._cleanup_local_cache()
                return True
                
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def _cleanup_local_cache(self):
        """Clean up expired entries from local cache"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.local_cache.items()
            if current_time >= item["expiry"]
        ]
        for key in expired_keys:
            del self.local_cache[key]
    
    def cached_function(self, expiry: int = None):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{func.__name__}:{self.generate_cache_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached_result = self.get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set_cache(cache_key, result, expiry)
                return result
            
            return wrapper
        return decorator
    
    def batch_process(self, items: List[Any], process_func: Callable, 
                     batch_size: int = 10) -> List[Any]:
        """Process items in batches for better performance"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch in parallel
            with ThreadPoolExecutor(max_workers=min(len(batch), 4)) as executor:
                batch_results = list(executor.map(process_func, batch))
            
            results.extend(batch_results)
            
        return results
    
    async def async_batch_process(self, items: List[Any], 
                                 async_process_func: Callable,
                                 batch_size: int = 10) -> List[Any]:
        """Asynchronous batch processing"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch asynchronously
            tasks = [async_process_func(item) for item in batch]
            batch_results = await asyncio.gather(*tasks)
            
            results.extend(batch_results)
            
        return results
    
    def precompute_recommendations(self, user_profiles: List[Dict], 
                                 skin_tones: List[str]):
        """Precompute and cache recommendations for common combinations"""
        from advanced_recommendation_engine import get_recommendation_engine
        
        rec_engine = get_recommendation_engine()
        
        def compute_recommendations(params):
            user_profile, skin_tone = params
            return rec_engine.get_personalized_recommendations(
                skin_tone=skin_tone,
                user_preferences=user_profile,
                n_recommendations=10
            )
        
        # Create parameter combinations
        param_combinations = [
            (profile, tone) for profile in user_profiles for tone in skin_tones
        ]
        
        # Batch process recommendations
        logger.info(f"Precomputing {len(param_combinations)} recommendation combinations")
        recommendations = self.batch_process(param_combinations, compute_recommendations)
        
        # Cache results
        for (profile, tone), rec in zip(param_combinations, recommendations):
            cache_key = f"precomputed_rec:{self.generate_cache_key(profile, tone)}"
            self.set_cache(cache_key, rec, expiry=7200)  # 2 hours
        
        logger.info("Precomputation completed")
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "cache_size": len(self.local_cache) if not self.redis_client else "Redis",
            "redis_available": self.redis_client is not None
        }
    
    def clear_cache(self, pattern: str = None):
        """Clear cache entries"""
        if self.redis_client:
            if pattern:
                # Clear keys matching pattern
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                self.redis_client.flushdb()
        else:
            if pattern:
                # Clear local cache entries matching pattern
                keys_to_delete = [key for key in self.local_cache.keys() if pattern in key]
                for key in keys_to_delete:
                    del self.local_cache[key]
            else:
                self.local_cache.clear()

# Global optimizer instance
performance_optimizer = PerformanceOptimizer()

# Decorators for easy use
def cached(expiry: int = 3600):
    """Simple decorator for caching function results"""
    return performance_optimizer.cached_function(expiry)

def batch_process(items: List[Any], batch_size: int = 10):
    """Simple function for batch processing"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            return performance_optimizer.batch_process(items, func, batch_size)
        return wrapper
    return decorator

# Memory-efficient image processing
class ImageBatchProcessor:
    """Batch processor for image analysis to optimize memory usage"""
    
    def __init__(self, max_batch_size: int = 5):
        self.max_batch_size = max_batch_size
    
    def process_images_batch(self, image_paths: List[str], 
                           analysis_func: Callable) -> List[Dict]:
        """Process multiple images in memory-efficient batches"""
        results = []
        
        for i in range(0, len(image_paths), self.max_batch_size):
            batch_paths = image_paths[i:i + self.max_batch_size]
            batch_results = []
            
            for path in batch_paths:
                try:
                    result = analysis_func(path)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing image {path}: {e}")
                    batch_results.append({"error": str(e)})
            
            results.extend(batch_results)
            
            # Force garbage collection between batches
            import gc
            gc.collect()
        
        return results

# Smart caching for skin tone analysis results
class SkinToneCache:
    """Specialized cache for skin tone analysis results"""
    
    def __init__(self):
        self.optimizer = performance_optimizer
    
    def get_or_analyze(self, image_hash: str, analysis_func: Callable, 
                      *args, **kwargs) -> Dict:
        """Get cached result or perform analysis"""
        cache_key = f"skin_analysis:{image_hash}"
        
        cached_result = self.optimizer.get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for skin analysis: {image_hash}")
            return cached_result
        
        # Perform analysis
        result = analysis_func(*args, **kwargs)
        
        # Cache result for 24 hours
        self.optimizer.set_cache(cache_key, result, expiry=86400)
        
        return result
    
    def generate_image_hash(self, image_data: np.ndarray) -> str:
        """Generate hash for image data"""
        return hashlib.md5(image_data.tobytes()).hexdigest()

# Global instances
image_batch_processor = ImageBatchProcessor()
skin_tone_cache = SkinToneCache()

if __name__ == "__main__":
    # Test the performance optimizer
    optimizer = PerformanceOptimizer()
    
    # Test caching
    @optimizer.cached_function(expiry=60)
    def expensive_computation(x: int) -> int:
        time.sleep(1)  # Simulate expensive operation
        return x * x
    
    start_time = time.time()
    result1 = expensive_computation(10)  # Should take ~1 second
    print(f"First call took: {time.time() - start_time:.2f}s, result: {result1}")
    
    start_time = time.time()
    result2 = expensive_computation(10)  # Should be instant (cached)
    print(f"Second call took: {time.time() - start_time:.2f}s, result: {result2}")
    
    # Print cache stats
    print("Cache stats:", optimizer.get_cache_stats())
