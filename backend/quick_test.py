#!/usr/bin/env python3
"""
Quick test to verify the JSON query system works offline.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.json_query_engine import CachedJSONQueryEngine

def main():
    print("=== Testing JSON Query Engine ===")
    
    # Initialize the engine
    dataset_path = "../dataset/processed-data"
    try:
        engine = CachedJSONQueryEngine(dataset_path)
        print(f"✅ Successfully loaded JSON Query Engine with {len(engine.documents)} documents")
    except Exception as e:
        print(f"❌ Failed to load JSON Query Engine: {e}")
        return
    
    # Test queries
    test_queries = [
        "What is Article 21A about?",
        "education rights",
        "fundamental rights",
        "directive principles"
    ]
    
    print("\n=== Running Test Queries ===")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        try:
            results = engine.query(query, limit=2)
            if results:
                print(f"   ✅ Found {len(results)} results:")
                for j, result in enumerate(results, 1):
                    title = result.get('title', 'Unknown')
                    snippet = result.get('content', '')[:100] + '...' if result.get('content') else ''
                    score = result.get('score', 0)
                    print(f"      {j}. {title} (score: {score:.3f})")
                    print(f"         {snippet}")
            else:
                print("   ⚠️ No results found")
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
    
    # Test caching
    print(f"\n=== Cache Statistics ===")
    cache_stats = engine.get_cache_stats()
    print(f"Cache hits: {cache_stats['hits']}")
    print(f"Cache misses: {cache_stats['misses']}")
    print(f"Cache size: {cache_stats['size']}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()