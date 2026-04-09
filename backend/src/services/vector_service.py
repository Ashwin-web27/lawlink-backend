"""
Vector Embedding Service for Indian Education Law Chatbot
Handles text embedding creation and vector database operations using FAISS
"""

import os
import json
import pickle
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging
import numpy as np
from datetime import datetime

# Import ML libraries
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    import torch
except ImportError as e:
    raise ImportError(f"Required packages not installed: {e}")

logger = logging.getLogger(__name__)


class VectorEmbeddingService:
    """
    Service for creating and managing vector embeddings for legal documents
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 dataset_path: str = None):
        """
        Initialize the vector embedding service
        
        Args:
            model_name: Name of the sentence transformer model
            dataset_path: Path to the dataset directory
        """
        self.model_name = model_name
        
        # Set up paths
        if dataset_path is None:
            # Prefer project root dataset if exists; else fallback to backend/dataset
            backend_dir = Path(__file__).parent.parent.parent  # backend
            project_root = backend_dir.parent
            root_dataset = project_root / "dataset"
            if root_dataset.exists():
                self.dataset_path = root_dataset
            else:
                self.dataset_path = backend_dir / "dataset"
        else:
            self.dataset_path = Path(dataset_path)
            
        self.vector_db_path = self.dataset_path / "vector-database"
        self.models_path = self.dataset_path / "models"
        self.embeddings_path = self.dataset_path / "training-data" / "embeddings"
        
        # Create directories
        self.vector_db_path.mkdir(exist_ok=True, parents=True)
        self.models_path.mkdir(exist_ok=True, parents=True)
        self.embeddings_path.mkdir(exist_ok=True, parents=True)
        
        # Initialize model
        self.model = None
        self.faiss_index = None
        self.document_metadata = []
        
        # Load or create model
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Save model to local directory for future use
            model_save_path = self.models_path / f"sentence_transformer_{self.model_name.replace('/', '_')}"
            if not model_save_path.exists():
                self.model.save(str(model_save_path))
                logger.info(f"Saved model to {model_save_path}")
                
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}")
            raise
    
    def create_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Create embeddings for a list of texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        if not self.model:
            raise RuntimeError("Model not initialized")
            
        logger.info(f"Creating embeddings for {len(texts)} texts")
        
        try:
            # Create embeddings in batches
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(batch_texts, show_progress_bar=True)
                embeddings.append(batch_embeddings)
                
            # Combine all embeddings
            all_embeddings = np.vstack(embeddings)
            logger.info(f"Created embeddings with shape: {all_embeddings.shape}")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise
    
    def build_vector_index(self, 
                          embeddings: np.ndarray, 
                          use_gpu: bool = False,
                          index_type: str = "Flat") -> faiss.Index:
        """
        Build FAISS vector index from embeddings
        
        Args:
            embeddings: Numpy array of embeddings
            use_gpu: Whether to use GPU for index
            index_type: Type of FAISS index ("Flat", "IVF", "HNSW")
            
        Returns:
            FAISS index
        """
        dimension = embeddings.shape[1]
        n_vectors = embeddings.shape[0]
        
        logger.info(f"Building FAISS index with {n_vectors} vectors of dimension {dimension}")
        
        try:
            # Create appropriate index type
            if index_type == "Flat":
                index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
                
            elif index_type == "IVF":
                # IVF index for faster search on large datasets
                nlist = min(100, n_vectors // 10)  # Number of clusters
                quantizer = faiss.IndexFlatIP(dimension)
                index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
                index.train(embeddings)
                
            elif index_type == "HNSW":
                # HNSW index for very fast approximate search
                index = faiss.IndexHNSWFlat(dimension, 32)
                index.hnsw.efConstruction = 40
                
            else:
                raise ValueError(f"Unsupported index type: {index_type}")
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add vectors to index
            index.add(embeddings.astype(np.float32))
            
            logger.info(f"Built {index_type} index with {index.ntotal} vectors")
            
            # Use GPU if available and requested
            if use_gpu and faiss.get_num_gpus() > 0:
                logger.info("Moving index to GPU")
                gpu_index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, index)
                return gpu_index
            
            return index
            
        except Exception as e:
            logger.error(f"Error building vector index: {str(e)}")
            raise
    
    def save_vector_index(self, 
                         index: faiss.Index, 
                         metadata: List[Dict[str, Any]],
                         filename: str = "legal_docs_index"):
        """
        Save FAISS index and metadata to disk
        
        Args:
            index: FAISS index to save
            metadata: Document metadata
            filename: Base filename for saved files
        """
        try:
            # Save FAISS index
            index_path = self.vector_db_path / f"{filename}.index"
            faiss.write_index(index, str(index_path))
            
            # Save metadata
            metadata_path = self.vector_db_path / f"{filename}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Save embeddings if needed
            embeddings_path = self.embeddings_path / f"{filename}_embeddings.npy"
            # Note: We would need to store embeddings separately if we want to save them
            
            logger.info(f"Saved vector index to {index_path}")
            logger.info(f"Saved metadata to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error saving vector index: {str(e)}")
            raise
    
    def load_vector_index(self, filename: str = "legal_docs_index") -> Tuple[faiss.Index, List[Dict[str, Any]]]:
        """
        Load FAISS index and metadata from disk
        
        Args:
            filename: Base filename for saved files
            
        Returns:
            Tuple of (FAISS index, metadata list)
        """
        try:
            # Load FAISS index
            index_path = self.vector_db_path / f"{filename}.index"
            if not index_path.exists():
                raise FileNotFoundError(f"Index file not found: {index_path}")
                
            index = faiss.read_index(str(index_path))
            
            # Load metadata
            metadata_path = self.vector_db_path / f"{filename}_metadata.json"
            if not metadata_path.exists():
                raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
                
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            logger.info(f"Loaded vector index with {index.ntotal} vectors")
            logger.info(f"Loaded {len(metadata)} metadata entries")
            
            return index, metadata
            
        except Exception as e:
            logger.error(f"Error loading vector index: {str(e)}")
            raise
    
    def search_similar_documents(self, 
                               query: str, 
                               k: int = 5,
                               score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Search query text
            k: Number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of similar documents with scores
        """
        if not self.faiss_index or not self.document_metadata:
            raise RuntimeError("Vector index not loaded. Call build_and_save_index first.")
        
        try:
            # Create query embedding
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding.astype(np.float32))
            
            # Search in FAISS index
            scores, indices = self.faiss_index.search(query_embedding.astype(np.float32), k)
            
            # Prepare results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score >= score_threshold and idx < len(self.document_metadata):
                    result = {
                        'rank': i + 1,
                        'score': float(score),
                        'document': self.document_metadata[idx],
                        'query': query
                    }
                    results.append(result)
            
            logger.info(f"Found {len(results)} similar documents for query: '{query[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise
    
    def build_and_save_index(self, documents: List[Dict[str, Any]], 
                           index_type: str = "Flat",
                           filename: str = "legal_docs_index"):
        """
        Complete pipeline to build and save vector index from documents
        
        Args:
            documents: List of processed documents
            index_type: Type of FAISS index to create
            filename: Base filename for saved files
        """
        try:
            logger.info("Starting vector index build pipeline...")
            
            # Extract texts and metadata
            texts = []
            metadata = []
            
            for doc in documents:
                # Create searchable text combining title, section, and content
                searchable_text = f"{doc.get('title', '')} {doc.get('section', '')} {doc.get('content', '')}"
                texts.append(searchable_text.strip())
                
                # Store metadata for retrieval
                metadata.append({
                    'id': doc.get('id'),
                    'title': doc.get('title'),
                    'section': doc.get('section'),
                    'year': doc.get('year'),
                    'content': doc.get('content'),
                    'source_file': doc.get('source_file'),
                    'metadata': doc.get('metadata', {}),
                    'indexed_at': datetime.now().isoformat()
                })
            
            # Create embeddings
            embeddings = self.create_embeddings(texts)
            
            # Build FAISS index
            index = self.build_vector_index(embeddings, index_type=index_type)
            
            # Save index and metadata
            self.save_vector_index(index, metadata, filename)
            
            # Store in memory for immediate use
            self.faiss_index = index
            self.document_metadata = metadata
            
            logger.info("Vector index build pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Error in build_and_save_index pipeline: {str(e)}")
            raise
    
    def load_index_for_search(self, filename: str = "legal_docs_index"):
        """
        Load vector index for search operations
        
        Args:
            filename: Base filename for saved files
        """
        try:
            self.faiss_index, self.document_metadata = self.load_vector_index(filename)
            logger.info("Vector index loaded and ready for search")
            
        except Exception as e:
            logger.error(f"Error loading index for search: {str(e)}")
            raise
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current vector index
        
        Returns:
            Dictionary of index statistics
        """
        if not self.faiss_index or not self.document_metadata:
            return {"status": "No index loaded"}
        
        stats = {
            "index_type": type(self.faiss_index).__name__,
            "total_vectors": self.faiss_index.ntotal,
            "vector_dimension": self.faiss_index.d,
            "metadata_entries": len(self.document_metadata),
            "model_name": self.model_name,
            "gpu_enabled": hasattr(self.faiss_index, 'getGpuResources'),
        }
        
        return stats


def main():
    """
    Main function for testing the vector service
    """
    logging.basicConfig(level=logging.INFO)
    
    # Import data loader
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.data_loader import LegalDocumentLoader
    
    # Load processed documents
    loader = LegalDocumentLoader()
    
    # Try to load existing processed documents first
    processed_docs = loader.load_processed_documents()
    
    if not processed_docs:
        print("No processed documents found. Processing raw documents...")
        raw_docs = loader.load_json_documents()
        processed_docs = loader.process_documents(raw_docs)
        loader.save_processed_documents(processed_docs)
    
    if not processed_docs:
        print("No documents available for vector indexing")
        return
    
    # Initialize vector service
    print("Initializing vector service...")
    vector_service = VectorEmbeddingService()
    
    # Build and save vector index
    print("Building vector index...")
    vector_service.build_and_save_index(processed_docs)
    
    # Test search
    print("\\nTesting search functionality...")
    test_queries = [
        "Article 21",
        "Constitution of India",
        "fundamental rights",
        "legal text"
    ]
    
    for query in test_queries:
        print(f"\\nSearching for: '{query}'")
        results = vector_service.search_similar_documents(query, k=3)
        
        for result in results:
            print(f"  - {result['document']['section']} (Score: {result['score']:.3f})")
    
    # Print statistics
    stats = vector_service.get_index_statistics()
    print("\\nVector Index Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()