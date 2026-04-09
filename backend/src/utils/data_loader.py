"""
Data Loader for Indian Education Law Chatbot
Handles loading and processing of JSON legal documents
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LegalDocumentLoader:
    """
    Loads and processes legal documents from JSON files
    """
    
    def __init__(self, dataset_path: str = None):
        """
        Initialize the document loader
        
        Args:
            dataset_path: Path to the dataset directory
        """
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
            
        self.legal_documents_path = self.dataset_path / "legal-documents"
        self.processed_data_path = self.dataset_path / "processed-data"
        self.training_data_path = self.dataset_path / "training-data"
        
        # Create directories if they don't exist
        self.processed_data_path.mkdir(exist_ok=True, parents=True)
        self.training_data_path.mkdir(exist_ok=True, parents=True)
        
    def load_json_documents(self, file_pattern: str = "*.json") -> List[Dict[str, Any]]:
        """
        Load all JSON documents from the legal documents directory
        
        Args:
            file_pattern: Pattern to match JSON files
            
        Returns:
            List of document dictionaries
        """
        documents = []
        json_files = list(self.legal_documents_path.rglob(file_pattern))
        
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Handle nested constitution structure (parts -> articles)
                if isinstance(data, dict) and 'parts' in data and isinstance(data['parts'], dict):
                    flattened = self._flatten_constitution_structure(data, source=str(json_file))
                    documents.extend(flattened)
                # Handle Indian Penal Code structure (sections with nested categories)
                elif isinstance(data, dict) and 'sections' in data and isinstance(data['sections'], dict):
                    flattened = self._flatten_ipc_structure(data, source=str(json_file))
                    documents.extend(flattened)
                # Handle arrays of documents
                elif isinstance(data, list):
                    for doc in data:
                        doc['source_file'] = str(json_file)
                        # Add source context to improve disambiguation
                        self._add_source_context(doc, json_file)
                        documents.append(doc)
                # Handle single document objects
                elif isinstance(data, dict):
                    data['source_file'] = str(json_file)
                    # Add source context to improve disambiguation
                    self._add_source_context(data, json_file)
                    documents.append(data)
                    
                logger.info(f"Loaded {len(data) if isinstance(data, list) else 1} documents from {json_file}")
                
            except Exception as e:
                logger.error(f"Error loading {json_file}: {str(e)}")
                continue
                
        logger.info(f"Successfully loaded {len(documents)} total documents")
        return documents

    def _flatten_constitution_structure(self, data: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        """
        Flatten nested constitution JSON with 'parts' and nested 'articles' into flat records.
        Expected article entries: key is section label (e.g., 'Article 14'), value has 'title' and 'content'.
        """
        flattened: List[Dict[str, Any]] = []
        parts = data.get('parts', {})
        default_title = data.get('dataset_name', 'Constitution of India')
        default_year = '1950'
        for part_key, part_val in parts.items():
            if not isinstance(part_val, dict):
                continue
            articles = part_val.get('articles', {})
            if not isinstance(articles, dict):
                continue
            for section_label, article_obj in articles.items():
                if not isinstance(article_obj, dict):
                    continue
                content = article_obj.get('content', '')
                title = article_obj.get('title', default_title) or default_title
                section = str(section_label)
                # Add source context to content
                if content and not content.startswith(section):
                    content = f"{section} of {default_title}: {content}"
                doc_id = f"CONST_{section.replace(' ', '_')}"
                flattened.append({
                    'doc_id': doc_id,
                    'title': default_title if title == section else default_title,
                    'section': section,
                    'year': default_year,
                    'content': content,
                    'source_file': source
                })
        return flattened
    
    def _flatten_ipc_structure(self, data: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        """
        Flatten nested Indian Penal Code JSON with 'sections' into flat records.
        Expected structure: sections -> categories -> Section number -> {title, content, punishment}
        """
        flattened: List[Dict[str, Any]] = []
        sections = data.get('sections', {})
        dataset_name = data.get('dataset_name', 'Indian Penal Code')
        default_year = '1860'  # IPC was enacted in 1860
        
        for category_key, category_val in sections.items():
            if not isinstance(category_val, dict):
                continue
            
            for section_key, section_obj in category_val.items():
                if not isinstance(section_obj, dict):
                    continue
                
                title = section_obj.get('title', section_key)
                content = section_obj.get('content', '')
                punishment = section_obj.get('punishment', '')
                
                # Combine content and punishment with source context
                full_content = f"{section_key} of {dataset_name}: {content}"
                if punishment:
                    full_content += f" Punishment: {punishment}"
                
                doc_id = f"IPC_{section_key.replace(' ', '_')}"
                
                flattened.append({
                    'doc_id': doc_id,
                    'title': dataset_name,
                    'section': section_key,
                    'year': default_year,
                    'content': full_content,
                    'source_file': source,
                    'category': category_key,  # Additional field for IPC categories
                    'punishment': punishment  # Keep punishment separate for reference
                })
        
        return flattened
    
    def _add_source_context(self, doc: Dict[str, Any], source_file: Path) -> None:
        """
        Add source context to document content for better disambiguation
        """
        file_name = source_file.name.lower()
        content = doc.get('content', '')
        section = doc.get('section', '')
        
        if not content or content.startswith(section):
            return  # Already has context or no content
        
        # Determine source law type and add context
        if 'criminal-procedure' in file_name or 'crpc' in file_name:
            law_name = "Code of Criminal Procedure (CrPC)"
            doc['content'] = f"{section} of {law_name}: {content}"
            if 'doc_id' in doc:
                doc['doc_id'] = f"CRPC_{doc['doc_id']}"
        elif 'education' in file_name:
            law_name = "Education Law"
            doc['content'] = f"{section} of {law_name}: {content}"
            if 'doc_id' in doc:
                doc['doc_id'] = f"EDU_{doc['doc_id']}"
    
    def validate_document_structure(self, document: Dict[str, Any]) -> bool:
        """
        Validate that a document has the required structure
        
        Args:
            document: Document dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['doc_id', 'title', 'section', 'content']
        
        for field in required_fields:
            if field not in document:
                logger.warning(f"Document missing required field: {field}")
                return False
                
        # Check that content is not empty
        if not document.get('content', '').strip():
            logger.warning(f"Document {document.get('doc_id')} has empty content")
            return False
            
        return True
    
    def clean_and_preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess text content
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Basic text cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with search
        text = re.sub(r'[^\w\s\.\,\;\:\(\)\[\]\-\']', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and clean documents for training
        
        Args:
            documents: List of raw documents
            
        Returns:
            List of processed documents
        """
        processed_docs = []
        
        for doc in documents:
            if not self.validate_document_structure(doc):
                continue
                
            processed_doc = {
                'id': doc.get('doc_id'),
                'title': doc.get('title', ''),
                'section': doc.get('section', ''),
                'year': doc.get('year', ''),
                'content': self.clean_and_preprocess_text(doc.get('content', '')),
                'source_file': doc.get('source_file', ''),
                'processed_at': datetime.now().isoformat(),
            }
            
            # Add metadata
            processed_doc['metadata'] = {
                'word_count': len(processed_doc['content'].split()),
                'char_count': len(processed_doc['content']),
                'title': processed_doc['title'],
                'section': processed_doc['section'],
                'year': processed_doc['year']
            }
            
            processed_docs.append(processed_doc)
            
        logger.info(f"Processed {len(processed_docs)} documents successfully")
        return processed_docs
    
    def save_processed_documents(self, documents: List[Dict[str, Any]], filename: str = "processed_legal_docs.json"):
        """
        Save processed documents to file
        
        Args:
            documents: List of processed documents
            filename: Output filename
        """
        output_path = self.processed_data_path / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(documents)} processed documents to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving processed documents: {str(e)}")
            
    def load_processed_documents(self, filename: str = "processed_legal_docs.json") -> List[Dict[str, Any]]:
        """
        Load previously processed documents
        
        Args:
            filename: Input filename
            
        Returns:
            List of processed documents
        """
        input_path = self.processed_data_path / filename
        
        if not input_path.exists():
            logger.warning(f"Processed documents file not found: {input_path}")
            return []
            
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
                
            logger.info(f"Loaded {len(documents)} processed documents from {input_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading processed documents: {str(e)}")
            return []
    
    def get_document_statistics(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about the document collection
        
        Args:
            documents: List of documents
            
        Returns:
            Dictionary of statistics
        """
        if not documents:
            return {}
            
        total_docs = len(documents)
        total_words = sum(doc.get('metadata', {}).get('word_count', 0) for doc in documents)
        total_chars = sum(doc.get('metadata', {}).get('char_count', 0) for doc in documents)
        
        # Get unique sections and years
        sections = set(doc.get('section', '') for doc in documents if doc.get('section'))
        years = set(doc.get('year', '') for doc in documents if doc.get('year'))
        
        avg_words = total_words / total_docs if total_docs > 0 else 0
        avg_chars = total_chars / total_docs if total_docs > 0 else 0
        
        stats = {
            'total_documents': total_docs,
            'total_words': total_words,
            'total_characters': total_chars,
            'average_words_per_doc': round(avg_words, 2),
            'average_chars_per_doc': round(avg_chars, 2),
            'unique_sections': len(sections),
            'unique_years': len(years),
            'sections': list(sections),
            'years': list(years),
            'processed_at': datetime.now().isoformat()
        }
        
        return stats


def main():
    """
    Main function for testing the data loader
    """
    logging.basicConfig(level=logging.INFO)
    
    # Initialize loader
    loader = LegalDocumentLoader()
    
    # Load raw documents
    print("Loading JSON documents...")
    raw_docs = loader.load_json_documents()
    
    # Process documents
    print("Processing documents...")
    processed_docs = loader.process_documents(raw_docs)
    
    # Save processed documents
    loader.save_processed_documents(processed_docs)
    
    # Get statistics
    stats = loader.get_document_statistics(processed_docs)
    print("\nDocument Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()