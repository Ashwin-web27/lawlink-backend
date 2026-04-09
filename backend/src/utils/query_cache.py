"""
Query Cache and Analytics for JSON Query Engine
Provides caching and usage analytics for better performance and insights
"""

import json
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from pathlib import Path
import hashlib
import logging

logger = logging.getLogger(__name__)


class QueryCache:
    """
    In-memory cache for query results with LRU eviction and analytics
    """
    
    def __init__(self, max_cache_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize the query cache
        
        Args:
            max_cache_size: Maximum number of cached queries
            ttl_seconds: Time-to-live for cached results in seconds
        """
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}  # query_hash -> (timestamp, results)
        self.access_order = []  # For LRU eviction
        self.analytics = QueryAnalytics()
        
    def _get_query_hash(self, query: str, params: Dict[str, Any] = None) -> str:
        """Generate a hash for the query and parameters"""
        query_data = {
            'query': query.lower().strip(),
            'params': params or {}
        }
        query_string = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(query_string.encode()).hexdigest()
    
    def get(self, query: str, params: Dict[str, Any] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results for a query
        
        Args:
            query: Search query string
            params: Additional query parameters
            
        Returns:
            Cached results or None if not found/expired
        """
        query_hash = self._get_query_hash(query, params)
        
        if query_hash in self.cache:
            timestamp, results = self.cache[query_hash]
            
            # Check if cache entry has expired
            if time.time() - timestamp < self.ttl_seconds:
                # Update access order (move to end)
                if query_hash in self.access_order:
                    self.access_order.remove(query_hash)
                self.access_order.append(query_hash)
                
                # Record cache hit
                self.analytics.record_cache_hit(query, len(results))
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return results
            else:
                # Remove expired entry
                self._remove_from_cache(query_hash)
        
        # Record cache miss
        self.analytics.record_cache_miss(query)
        return None
    
    def set(self, query: str, results: List[Dict[str, Any]], params: Dict[str, Any] = None):
        """
        Cache query results
        
        Args:
            query: Search query string
            results: Query results to cache
            params: Additional query parameters
        """
        query_hash = self._get_query_hash(query, params)
        
        # Remove existing entry if present
        if query_hash in self.cache:
            self._remove_from_cache(query_hash)
        
        # Check cache size and evict if necessary
        while len(self.cache) >= self.max_cache_size:
            self._evict_lru()
        
        # Add to cache
        self.cache[query_hash] = (time.time(), results)
        self.access_order.append(query_hash)
        
        logger.debug(f"Cached results for query: {query[:50]}... (size: {len(results)})")
    
    def _remove_from_cache(self, query_hash: str):
        """Remove a query from cache and access order"""
        if query_hash in self.cache:
            del self.cache[query_hash]
        if query_hash in self.access_order:
            self.access_order.remove(query_hash)
    
    def _evict_lru(self):
        """Evict the least recently used cache entry"""
        if self.access_order:
            lru_hash = self.access_order.pop(0)
            if lru_hash in self.cache:
                del self.cache[lru_hash]
    
    def clear(self):
        """Clear all cached data"""
        self.cache.clear()
        self.access_order.clear()
        logger.info("Query cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'max_cache_size': self.max_cache_size,
            'cache_utilization': len(self.cache) / self.max_cache_size,
            'analytics': self.analytics.get_stats()
        }


class QueryAnalytics:
    """
    Analytics tracking for query patterns and performance
    """
    
    def __init__(self):
        """Initialize analytics tracking"""
        self.query_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.query_patterns = Counter()
        self.popular_queries = Counter()
        self.query_performance = defaultdict(list)  # query -> [response_times]
        self.document_access = Counter()  # doc_id -> access_count
        self.topic_interests = Counter()  # topic -> query_count
        self.start_time = time.time()
        
    def record_query(self, query: str, results: List[Dict[str, Any]], 
                    response_time: float, match_types: List[str] = None):
        """
        Record a query execution
        
        Args:
            query: The search query
            results: Query results
            response_time: Time taken to execute query
            match_types: Types of matches found
        """
        self.query_count += 1
        self.popular_queries[query.lower().strip()] += 1
        self.query_performance[query.lower().strip()].append(response_time)
        
        # Analyze query patterns
        words = query.lower().split()
        for word in words:
            if len(word) > 2:
                self.query_patterns[word] += 1
        
        # Track document access
        for result in results:
            if 'document' in result and 'doc_id' in result['document']:
                doc_id = result['document']['doc_id']
                self.document_access[doc_id] += 1
        
        # Track match types
        if match_types:
            for match_type in match_types:
                if 'topic_' in match_type:
                    topic = match_type.replace('topic_', '')
                    self.topic_interests[topic] += 1
    
    def record_cache_hit(self, query: str, result_count: int):
        """Record a cache hit"""
        self.cache_hits += 1
        
    def record_cache_miss(self, query: str):
        """Record a cache miss"""
        self.cache_misses += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive analytics statistics"""
        uptime = time.time() - self.start_time
        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / cache_total if cache_total > 0 else 0
        
        # Calculate average response times
        avg_response_times = {}
        for query, times in self.query_performance.items():
            if times:
                avg_response_times[query] = sum(times) / len(times)
        
        return {
            'uptime_seconds': uptime,
            'total_queries': self.query_count,
            'cache_hit_rate': cache_hit_rate,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'top_queries': dict(self.popular_queries.most_common(10)),
            'top_query_patterns': dict(self.query_patterns.most_common(10)),
            'most_accessed_documents': dict(self.document_access.most_common(10)),
            'popular_topics': dict(self.topic_interests.most_common(10)),
            'average_response_time': sum(sum(times) for times in self.query_performance.values()) / 
                                   sum(len(times) for times in self.query_performance.values()) 
                                   if self.query_performance else 0
        }
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on analytics data"""
        recommendations = []
        
        # Cache performance recommendations
        cache_total = self.cache_hits + self.cache_misses
        if cache_total > 100:
            cache_hit_rate = self.cache_hits / cache_total
            if cache_hit_rate < 0.3:
                recommendations.append("Consider increasing cache size or TTL - low cache hit rate detected")
        
        # Popular query recommendations
        if len(self.popular_queries) > 20:
            top_queries = self.popular_queries.most_common(5)
            recommendations.append(f"Consider optimizing these frequent queries: {[q[0] for q in top_queries]}")
        
        # Document access recommendations
        if len(self.document_access) > 10:
            top_docs = self.document_access.most_common(3)
            recommendations.append(f"Most accessed documents: {[d[0] for d in top_docs]} - ensure they have quality content")
        
        # Performance recommendations
        slow_queries = []
        for query, times in self.query_performance.items():
            if times:
                avg_time = sum(times) / len(times)
                if avg_time > 1.0:  # Queries taking more than 1 second
                    slow_queries.append(query)
        
        if slow_queries:
            recommendations.append(f"Consider optimizing these slow queries: {slow_queries[:3]}")
        
        return recommendations
    
    def export_data(self, filepath: str):
        """Export analytics data to JSON file"""
        data = self.get_stats()
        data['export_timestamp'] = time.time()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analytics data exported to {filepath}")


class CachedJsonQueryEngine:
    """
    JSON Query Engine with integrated caching and analytics
    """
    
    def __init__(self, base_engine, cache_size: int = 1000, cache_ttl: int = 3600):
        """
        Initialize cached query engine
        
        Args:
            base_engine: The underlying JSON query engine
            cache_size: Maximum number of cached queries
            cache_ttl: Cache time-to-live in seconds
        """
        self.base_engine = base_engine
        self.cache = QueryCache(cache_size, cache_ttl)
    
    def query(self, query_text: str, max_results: int = 5, 
             min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Query with caching support
        
        Args:
            query_text: Search query
            max_results: Maximum results to return
            min_score: Minimum score threshold
            
        Returns:
            Query results with caching
        """
        params = {'max_results': max_results, 'min_score': min_score}
        
        # Try cache first
        start_time = time.time()
        cached_results = self.cache.get(query_text, params)
        
        if cached_results is not None:
            return cached_results
        
        # Execute query
        results = self.base_engine.query(query_text, max_results, min_score)
        response_time = time.time() - start_time
        
        # Cache results
        self.cache.set(query_text, results, params)
        
        # Record analytics
        match_types = [r.get('match_type', 'unknown') for r in results]
        self.cache.analytics.record_query(query_text, results, response_time, match_types)
        
        return results
    
    def suggest_related_queries(self, query_text: str) -> List[str]:
        """Get query suggestions (no caching for suggestions)"""
        return self.base_engine.suggest_related_queries(query_text)
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get query analytics and cache statistics"""
        return self.cache.get_stats()
    
    def clear_cache(self):
        """Clear the query cache"""
        self.cache.clear()


def test_cached_engine():
    """Test function for the cached query engine"""
    from json_query_engine import JsonQueryEngine
    
    # Sample test documents
    test_docs = [
        {
            "doc_id": "Article_21",
            "title": "Constitution of India",
            "section": "Article 21", 
            "year": "1950",
            "content": "No person shall be deprived of his life or personal liberty except according to procedure established by law."
        }
    ]
    
    base_engine = JsonQueryEngine(test_docs)
    cached_engine = CachedJsonQueryEngine(base_engine)
    
    # Test caching
    query = "Article 21"
    
    print("First query (cache miss):")
    start = time.time()
    results1 = cached_engine.query(query)
    time1 = time.time() - start
    print(f"Time: {time1:.3f}s, Results: {len(results1)}")
    
    print("Second query (cache hit):")
    start = time.time()
    results2 = cached_engine.query(query)
    time2 = time.time() - start
    print(f"Time: {time2:.3f}s, Results: {len(results2)}")
    
    print("Analytics:")
    analytics = cached_engine.get_analytics()
    print(f"Cache hit rate: {analytics['analytics']['cache_hit_rate']:.2f}")
    print(f"Total queries: {analytics['analytics']['total_queries']}")


if __name__ == "__main__":
    test_cached_engine()