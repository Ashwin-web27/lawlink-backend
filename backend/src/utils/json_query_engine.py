"""
Enhanced JSON Query Engine for Legal Documents
Provides advanced search capabilities specifically for JSON-based legal document retrieval
"""

import json
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import logging
from difflib import SequenceMatcher
from collections import defaultdict

logger = logging.getLogger(__name__)


class JsonQueryEngine:
    """
    Advanced JSON query engine for legal documents with:
    - Fuzzy matching
    - Semantic keyword grouping
    - Topic-based search
    - Legal citation recognition
    """
    
    def __init__(self, documents: List[Dict[str, Any]] = None):
        """
        Initialize the query engine with processed documents
        
        Args:
            documents: List of processed legal document dictionaries
        """
        self.documents = documents or []
        self.keyword_index = self._build_keyword_index()
        self.legal_topics = self._build_legal_topics()
        
    def set_documents(self, documents: List[Dict[str, Any]]):
        """Update the documents and rebuild indexes"""
        self.documents = documents
        self.keyword_index = self._build_keyword_index()
        
    def _build_keyword_index(self) -> Dict[str, Set[int]]:
        """Build an inverted index of keywords to document indices"""
        index = defaultdict(set)
        
        for i, doc in enumerate(self.documents):
            # Index all searchable text
            searchable_text = f"{doc.get('title', '')} {doc.get('section', '')} {doc.get('content', '')}"
            words = re.findall(r'\w+', searchable_text.lower())
            
            for word in words:
                if len(word) > 2:  # Skip very short words
                    index[word].add(i)
                    
        return dict(index)
    
    def _build_legal_topics(self) -> Dict[str, List[str]]:
        """Define legal topic categories and their associated keywords"""
        return {
            "education": [
                "education", "school", "student", "teacher", "university", "college",
                "academic", "curriculum", "examination", "degree", "admission",
                "learning", "educational", "study", "teaching", "literacy"
            ],
            "fundamental_rights": [
                "fundamental", "rights", "liberty", "equality", "freedom", "speech",
                "expression", "religion", "assembly", "association", "movement",
                "residence", "profession", "life", "personal"
            ],
            "citizenship": [
                "citizenship", "citizen", "naturalization", "domicile", "residence",
                "migration", "foreign", "state", "nationality", "birth", "parentage"
            ],
            "directive_principles": [
                "directive", "principles", "policy", "welfare", "social", "economic",
                "justice", "livelihood", "work", "health", "nutrition", "environment"
            ],
            "government": [
                "parliament", "government", "state", "union", "legislature", "executive",
                "judiciary", "administration", "official", "authority", "power"
            ],
            "legal_procedure": [
                "procedure", "court", "trial", "evidence", "witness", "judgment",
                "appeal", "jurisdiction", "legal", "law", "act", "section", "article"
            ]
        }
    
    def query(self, query_text: str, max_results: int = 5, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Main query method that combines multiple search strategies
        
        Args:
            query_text: User's search query
            max_results: Maximum number of results to return
            min_score: Minimum relevance score threshold
            
        Returns:
            List of results with scores and document data
        """
        results = []
        
        # Strategy 1: Direct article lookup
        article_results = self._search_articles(query_text)
        results.extend(article_results)
        
        # Strategy 2: Topic-based search
        topic_results = self._search_by_topics(query_text)
        results.extend(topic_results)
        
        # Strategy 3: Keyword search with fuzzy matching
        keyword_results = self._search_keywords(query_text)
        results.extend(keyword_results)
        
        # Strategy 4: Full-text search
        fulltext_results = self._search_fulltext(query_text)
        results.extend(fulltext_results)
        
        # Deduplicate and score results
        unique_results = self._deduplicate_results(results)
        
        # Filter by minimum score and limit results
        filtered_results = [r for r in unique_results if r['score'] >= min_score]
        filtered_results.sort(key=lambda x: x['score'], reverse=True)
        
        return filtered_results[:max_results]
    
    def _search_articles(self, query_text: str) -> List[Dict[str, Any]]:
        """Search for specific article references"""
        results = []
        
        # Extract article references
        article_pattern = r"(?i)\b(art(?:icle)?)\s*\.?\s*(\d+[A-Za-z]?)(?:\s*\([^)]+\))?\b"
        matches = re.finditer(article_pattern, query_text)
        
        for match in matches:
            article_num = match.group(2).upper()
            article_label = f"Article {article_num}"
            
            # Find exact matches
            for i, doc in enumerate(self.documents):
                if doc.get('section', '').strip().lower() == article_label.lower():
                    results.append({
                        'score': 1.0,
                        'document': doc,
                        'match_type': 'exact_article',
                        'doc_index': i
                    })
                    
                    # Add neighboring articles
                    try:
                        base_num = int(''.join(c for c in article_num if c.isdigit()))
                        for offset in [-1, 1]:
                            neighbor_num = base_num + offset
                            neighbor_label = f"Article {neighbor_num}"
                            
                            for j, neighbor_doc in enumerate(self.documents):
                                if neighbor_doc.get('section', '').strip().lower() == neighbor_label.lower():
                                    results.append({
                                        'score': 0.7,
                                        'document': neighbor_doc,
                                        'match_type': 'related_article',
                                        'doc_index': j
                                    })
                    except ValueError:
                        pass
        
        return results
    
    def _search_by_topics(self, query_text: str) -> List[Dict[str, Any]]:
        """Search documents by legal topic categories"""
        results = []
        query_words = set(re.findall(r'\w+', query_text.lower()))
        
        for topic, keywords in self.legal_topics.items():
            topic_score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in query_words:
                    topic_score += 1
                    matched_keywords.append(keyword)
                else:
                    # Check for partial matches
                    for query_word in query_words:
                        if self._fuzzy_match(query_word, keyword) > 0.8:
                            topic_score += 0.5
                            matched_keywords.append(keyword)
            
            if topic_score > 0:
                # Find documents related to this topic
                for i, doc in enumerate(self.documents):
                    doc_text = f"{doc.get('title', '')} {doc.get('content', '')}".lower()
                    doc_score = 0
                    
                    for keyword in matched_keywords:
                        if keyword in doc_text:
                            doc_score += 0.3
                    
                    if doc_score > 0:
                        results.append({
                            'score': min(doc_score * (topic_score / len(keywords)), 0.8),
                            'document': doc,
                            'match_type': f'topic_{topic}',
                            'doc_index': i,
                            'matched_keywords': matched_keywords
                        })
        
        return results
    
    def _search_keywords(self, query_text: str) -> List[Dict[str, Any]]:
        """Search using keyword index with fuzzy matching"""
        results = []
        query_words = [word for word in re.findall(r'\w+', query_text.lower()) if len(word) > 2]
        
        doc_scores = defaultdict(float)
        
        for query_word in query_words:
            # Exact match
            if query_word in self.keyword_index:
                for doc_idx in self.keyword_index[query_word]:
                    doc_scores[doc_idx] += 0.5
            
            # Fuzzy match
            for indexed_word in self.keyword_index:
                similarity = self._fuzzy_match(query_word, indexed_word)
                if similarity > 0.75:  # Threshold for fuzzy matches
                    for doc_idx in self.keyword_index[indexed_word]:
                        doc_scores[doc_idx] += similarity * 0.3
        
        # Convert scores to results
        for doc_idx, score in doc_scores.items():
            if score > 0:
                normalized_score = min(score / len(query_words), 0.9)
                results.append({
                    'score': normalized_score,
                    'document': self.documents[doc_idx],
                    'match_type': 'keyword',
                    'doc_index': doc_idx
                })
        
        return results
    
    def _search_fulltext(self, query_text: str) -> List[Dict[str, Any]]:
        """Full-text search across all document content"""
        results = []
        query_words = re.findall(r'\w+', query_text.lower())
        
        for i, doc in enumerate(self.documents):
            content = f"{doc.get('title', '')} {doc.get('section', '')} {doc.get('content', '')}".lower()
            
            # Count word matches
            matches = 0
            for word in query_words:
                if word in content:
                    matches += 1
                else:
                    # Check for word variations
                    for content_word in re.findall(r'\w+', content):
                        if self._fuzzy_match(word, content_word) > 0.8:
                            matches += 0.5
            
            if matches > 0:
                score = min(matches / len(query_words) * 0.4, 0.6)
                results.append({
                    'score': score,
                    'document': doc,
                    'match_type': 'fulltext',
                    'doc_index': i,
                    'word_matches': matches
                })
        
        return results
    
    def _fuzzy_match(self, word1: str, word2: str) -> float:
        """Calculate fuzzy string similarity"""
        return SequenceMatcher(None, word1, word2).ratio()
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents and combine scores"""
        doc_results = {}
        
        for result in results:
            doc_idx = result['doc_index']
            
            if doc_idx in doc_results:
                # Combine scores (take maximum)
                existing_score = doc_results[doc_idx]['score']
                new_score = result['score']
                doc_results[doc_idx]['score'] = max(existing_score, new_score)
                
                # Keep track of match types
                existing_types = doc_results[doc_idx].get('match_types', [])
                new_type = result['match_type']
                if new_type not in existing_types:
                    existing_types.append(new_type)
                doc_results[doc_idx]['match_types'] = existing_types
            else:
                result['match_types'] = [result['match_type']]
                doc_results[doc_idx] = result
        
        return list(doc_results.values())
    
    def suggest_related_queries(self, query_text: str) -> List[str]:
        """Suggest related queries based on the current query"""
        suggestions = []
        query_words = set(re.findall(r'\w+', query_text.lower()))
        
        # Find topic matches and suggest related terms
        for topic, keywords in self.legal_topics.items():
            topic_relevance = len(query_words.intersection(set(keywords)))
            if topic_relevance > 0:
                # Suggest other keywords from the same topic
                related_keywords = [kw for kw in keywords if kw not in query_words][:3]
                for keyword in related_keywords:
                    suggestions.append(f"{query_text} {keyword}")
        
        # Extract article numbers and suggest neighboring articles
        article_matches = re.finditer(r"(?i)\barticle\s*\.?\s*(\d+)", query_text)
        for match in article_matches:
            try:
                article_num = int(match.group(1))
                for offset in [-1, 1]:
                    neighbor_num = article_num + offset
                    if neighbor_num > 0:
                        suggestions.append(f"Article {neighbor_num}")
            except ValueError:
                pass
        
        return suggestions[:5]  # Limit to 5 suggestions


def test_query_engine():
    """Test function for the JSON query engine"""
    # Sample test documents
    test_docs = [
        {
            "doc_id": "Article_21",
            "title": "Constitution of India",
            "section": "Article 21",
            "year": "1950",
            "content": "No person shall be deprived of his life or personal liberty except according to procedure established by law."
        },
        {
            "doc_id": "Article_21A",
            "title": "Constitution of India", 
            "section": "Article 21A",
            "year": "2002",
            "content": "The State shall provide free and compulsory education to all children of the age of six to fourteen years."
        }
    ]
    
    engine = JsonQueryEngine(test_docs)
    
    # Test queries
    test_queries = [
        "Article 21",
        "education for children",
        "fundamental rights",
        "life and liberty"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = engine.query(query)
        for result in results:
            print(f"  Score: {result['score']:.2f}, Section: {result['document']['section']}")


if __name__ == "__main__":
    test_query_engine()