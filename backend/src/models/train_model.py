"""
Model Training Pipeline for Indian Education Law Chatbot
Handles automatic training and fine-tuning of models from JSON legal documents
"""

import os
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime
import numpy as np

# Import required libraries
try:
    from sentence_transformers import SentenceTransformer, InputExample, losses
    from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
    from torch.utils.data import DataLoader
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    raise ImportError(f"Required packages not installed: {e}")

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.data_loader import LegalDocumentLoader
    from services.vector_service import VectorEmbeddingService
except ImportError as e:
    print(f"Import error: {e}")

logger = logging.getLogger(__name__)


class LegalModelTrainer:
    """
    Handles training and fine-tuning of models for legal document processing
    """
    
    def __init__(self, dataset_path: str = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the model trainer
        
        Args:
            dataset_path: Path to the dataset directory
            model_name: Base model to fine-tune
        """
        # Set up paths
        if dataset_path is None:
            current_dir = Path(__file__).parent.parent.parent
            self.dataset_path = current_dir / "dataset"
        else:
            self.dataset_path = Path(dataset_path)
            
        self.models_path = self.dataset_path / "models"
        self.training_data_path = self.dataset_path / "training-data"
        self.qa_pairs_path = self.training_data_path / "qa-pairs"
        
        # Create directories
        self.models_path.mkdir(exist_ok=True, parents=True)
        self.qa_pairs_path.mkdir(exist_ok=True, parents=True)
        
        self.base_model_name = model_name
        self.model = None
        
        # Initialize data loader
        self.data_loader = LegalDocumentLoader(str(self.dataset_path))
        
    def generate_training_pairs(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate question-answer pairs from legal documents for training
        
        Args:
            documents: List of processed legal documents
            
        Returns:
            List of training pairs
        """
        training_pairs = []
        
        logger.info(f"Generating training pairs from {len(documents)} documents...")
        
        for doc in documents:
            doc_id = doc.get('id', '')
            title = doc.get('title', '')
            section = doc.get('section', '')
            content = doc.get('content', '')
            year = doc.get('year', '')
            
            if not content.strip():
                continue
            
            # Generate various types of questions for each document
            questions = self._generate_questions_for_document(doc)
            
            for question_data in questions:
                training_pair = {
                    'question': question_data['question'],
                    'answer': question_data['answer'],
                    'context': content,
                    'document_id': doc_id,
                    'section': section,
                    'title': title,
                    'year': year,
                    'question_type': question_data['type'],
                    'generated_at': datetime.now().isoformat()
                }
                
                training_pairs.append(training_pair)
        
        logger.info(f"Generated {len(training_pairs)} training pairs")
        return training_pairs
    
    def _generate_questions_for_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate specific questions for a legal document
        
        Args:
            doc: Document dictionary
            
        Returns:
            List of question-answer pairs
        """
        questions = []
        
        doc_id = doc.get('id', '')
        title = doc.get('title', '')
        section = doc.get('section', '')
        content = doc.get('content', '')
        year = doc.get('year', '')
        
        # Type 1: Direct reference questions
        if section:
            questions.append({
                'question': f"What does {section} say?",
                'answer': f"{section} from {title} ({year}) states: {content}",
                'type': 'direct_reference'
            })
            
            questions.append({
                'question': f"Explain {section}",
                'answer': f"According to {section} of {title} ({year}): {content}",
                'type': 'explanation'
            })
        
        # Type 2: Content-based questions
        if "Article" in section:
            questions.append({
                'question': f"What are the provisions of {section}?",
                'answer': f"The provisions of {section} include: {content}",
                'type': 'provisions'
            })
        
        # Type 3: General topic questions (extract keywords)
        keywords = self._extract_keywords(content)
        for keyword in keywords[:2]:  # Limit to 2 keywords per document
            questions.append({
                'question': f"What does Indian law say about {keyword}?",
                'answer': f"According to {section} of {title} ({year}), regarding {keyword}: {content}",
                'type': 'topic_based'
            })
        
        # Type 4: Year-based questions
        if year:
            questions.append({
                'question': f"What legal provisions were established in {year}?",
                'answer': f"In {year}, {title} established: {content}",
                'type': 'year_based'
            })
        
        return questions
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        Extract important keywords from legal text
        
        Args:
            text: Legal text content
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction (can be improved with NLP libraries)
        legal_terms = [
            'rights', 'education', 'fundamental', 'constitution', 'law',
            'provision', 'legal', 'court', 'judgment', 'regulation',
            'policy', 'government', 'citizen', 'freedom', 'equality'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for term in legal_terms:
            if term in text_lower:
                found_keywords.append(term)
                
        return found_keywords[:max_keywords]
    
    def save_training_pairs(self, training_pairs: List[Dict[str, Any]], filename: str = "generated_qa_pairs.json"):
        """
        Save generated training pairs to file
        
        Args:
            training_pairs: List of training pairs
            filename: Output filename
        """
        output_path = self.qa_pairs_path / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(training_pairs, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(training_pairs)} training pairs to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving training pairs: {str(e)}")
            raise
    
    def load_training_pairs(self, filename: str = "generated_qa_pairs.json") -> List[Dict[str, Any]]:
        """
        Load training pairs from file
        
        Args:
            filename: Input filename
            
        Returns:
            List of training pairs
        """
        input_path = self.qa_pairs_path / filename
        
        if not input_path.exists():
            logger.warning(f"Training pairs file not found: {input_path}")
            return []
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                training_pairs = json.load(f)
                
            logger.info(f"Loaded {len(training_pairs)} training pairs from {input_path}")
            return training_pairs
            
        except Exception as e:
            logger.error(f"Error loading training pairs: {str(e)}")
            return []
    
    def prepare_training_data(self, training_pairs: List[Dict[str, Any]]) -> Tuple[List[InputExample], List[InputExample]]:
        """
        Prepare training data in the format required by sentence-transformers
        
        Args:
            training_pairs: List of training pairs
            
        Returns:
            Tuple of (train_examples, eval_examples)
        """
        examples = []
        
        for pair in training_pairs:
            question = pair.get('question', '')
            answer = pair.get('answer', '')
            context = pair.get('context', '')
            
            if question and answer:
                # Create positive example (question matches answer)
                example = InputExample(texts=[question, answer], label=1.0)
                examples.append(example)
                
                # Create additional example with context
                if context:
                    context_example = InputExample(texts=[question, context], label=0.8)
                    examples.append(context_example)
        
        # Split into train and eval
        train_examples, eval_examples = train_test_split(
            examples, test_size=0.2, random_state=42
        )
        
        logger.info(f"Created {len(train_examples)} training examples and {len(eval_examples)} evaluation examples")
        
        return train_examples, eval_examples
    
    def fine_tune_model(self, 
                       train_examples: List[InputExample], 
                       eval_examples: List[InputExample],
                       epochs: int = 3,
                       batch_size: int = 16,
                       learning_rate: float = 2e-5) -> str:
        """
        Fine-tune the sentence transformer model
        
        Args:
            train_examples: Training examples
            eval_examples: Evaluation examples
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate
            
        Returns:
            Path to the fine-tuned model
        """
        try:
            # Load base model
            logger.info(f"Loading base model: {self.base_model_name}")
            self.model = SentenceTransformer(self.base_model_name)
            
            # Prepare data loaders
            train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
            
            # Define loss function
            train_loss = losses.CosineSimilarityLoss(self.model)
            
            # Set up evaluation
            evaluator = None
            if eval_examples:
                # Create evaluation pairs
                eval_sentences1 = [example.texts[0] for example in eval_examples]
                eval_sentences2 = [example.texts[1] for example in eval_examples]
                eval_scores = [example.label for example in eval_examples]
                
                evaluator = EmbeddingSimilarityEvaluator(
                    eval_sentences1, eval_sentences2, eval_scores,
                    name="legal_eval"
                )
            
            # Set output path
            model_output_path = self.models_path / f"fine_tuned_legal_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Starting fine-tuning for {epochs} epochs...")
            
            # Train the model
            self.model.fit(
                train_objectives=[(train_dataloader, train_loss)],
                epochs=epochs,
                evaluator=evaluator,
                evaluation_steps=100,
                output_path=str(model_output_path),
                save_best_model=True,
                optimizer_params={'lr': learning_rate}
            )
            
            logger.info(f"Fine-tuning completed! Model saved to: {model_output_path}")
            
            return str(model_output_path)
            
        except Exception as e:
            logger.error(f"Error during model fine-tuning: {str(e)}")
            raise
    
    def evaluate_model(self, model_path: str, test_pairs: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate the fine-tuned model
        
        Args:
            model_path: Path to the fine-tuned model
            test_pairs: Test question-answer pairs
            
        Returns:
            Dictionary of evaluation metrics
        """
        try:
            # Load the fine-tuned model
            model = SentenceTransformer(model_path)
            
            # Prepare test data
            questions = [pair['question'] for pair in test_pairs]
            answers = [pair['answer'] for pair in test_pairs]
            
            # Generate embeddings
            question_embeddings = model.encode(questions)
            answer_embeddings = model.encode(answers)
            
            # Calculate similarity scores
            similarities = cosine_similarity(question_embeddings, answer_embeddings)
            
            # Extract diagonal (question-answer pairs)
            pair_similarities = np.diag(similarities)
            
            # Calculate metrics
            metrics = {
                'mean_similarity': float(np.mean(pair_similarities)),
                'median_similarity': float(np.median(pair_similarities)),
                'std_similarity': float(np.std(pair_similarities)),
                'min_similarity': float(np.min(pair_similarities)),
                'max_similarity': float(np.max(pair_similarities)),
                'high_similarity_ratio': float(np.sum(pair_similarities > 0.7) / len(pair_similarities)),
                'low_similarity_ratio': float(np.sum(pair_similarities < 0.3) / len(pair_similarities))
            }
            
            logger.info("Model evaluation completed:")
            for metric, value in metrics.items():
                logger.info(f"  {metric}: {value:.4f}")
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error during model evaluation: {str(e)}")
            raise
    
    def full_training_pipeline(self, 
                             epochs: int = 3, 
                             batch_size: int = 16,
                             generate_new_pairs: bool = True) -> Dict[str, Any]:
        """
        Complete training pipeline from documents to fine-tuned model
        
        Args:
            epochs: Number of training epochs
            batch_size: Batch size for training
            generate_new_pairs: Whether to generate new training pairs
            
        Returns:
            Dictionary with training results
        """
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'model_path': None,
            'metrics': None,
            'error': None
        }
        
        try:
            logger.info("Starting full training pipeline...")
            
            # Load documents
            processed_docs = self.data_loader.load_processed_documents()
            
            if not processed_docs:
                logger.info("No processed documents found. Processing raw documents...")
                raw_docs = self.data_loader.load_json_documents()
                if raw_docs:
                    processed_docs = self.data_loader.process_documents(raw_docs)
                    self.data_loader.save_processed_documents(processed_docs)
                else:
                    raise ValueError("No documents found for training!")
            
            # Generate or load training pairs
            if generate_new_pairs:
                logger.info("Generating new training pairs...")
                training_pairs = self.generate_training_pairs(processed_docs)
                self.save_training_pairs(training_pairs)
            else:
                logger.info("Loading existing training pairs...")
                training_pairs = self.load_training_pairs()
                
            if not training_pairs:
                raise ValueError("No training pairs available!")
            
            # Prepare training data
            train_examples, eval_examples = self.prepare_training_data(training_pairs)
            
            if len(train_examples) < 10:
                raise ValueError(f"Insufficient training examples: {len(train_examples)}")
            
            # Fine-tune model
            model_path = self.fine_tune_model(
                train_examples, eval_examples, 
                epochs=epochs, batch_size=batch_size
            )
            
            # Evaluate model
            test_pairs = training_pairs[-min(50, len(training_pairs)):]  # Use last 50 as test
            metrics = self.evaluate_model(model_path, test_pairs)
            
            results.update({
                'status': 'completed',
                'model_path': model_path,
                'metrics': metrics,
                'training_pairs_count': len(training_pairs),
                'training_examples_count': len(train_examples),
                'eval_examples_count': len(eval_examples)
            })
            
            logger.info("Full training pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Error in training pipeline: {str(e)}")
            results.update({
                'status': 'failed',
                'error': str(e)
            })
        
        return results


def main():
    """
    Main function for testing the training pipeline
    """
    logging.basicConfig(level=logging.INFO)
    
    # Initialize trainer
    trainer = LegalModelTrainer()
    
    # Run full training pipeline
    print("Starting legal model training pipeline...")
    results = trainer.full_training_pipeline(epochs=2, batch_size=8, generate_new_pairs=True)
    
    # Print results
    print("\\nTraining Results:")
    for key, value in results.items():
        if key != 'metrics':
            print(f"  {key}: {value}")
    
    if results.get('metrics'):
        print("\\nModel Evaluation Metrics:")
        for metric, value in results['metrics'].items():
            print(f"  {metric}: {value:.4f}")


if __name__ == "__main__":
    main()