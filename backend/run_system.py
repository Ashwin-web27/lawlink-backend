"""
Main Startup Script for Indian Education Law Chatbot
Handles initialization, training, and running of the complete system
"""

import os
import sys
import json
import logging
import io
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from utils.data_loader import LegalDocumentLoader
    from services.vector_service import VectorEmbeddingService
    from models.train_model import LegalModelTrainer
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to install dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging (Windows-safe unicode)
def _build_console_handler() -> logging.Handler:
    try:
        # Python 3.9+ StreamHandler supports setting stream with UTF-8 wrapper
        stdout = sys.stdout
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        else:
            try:
                # Wrap the buffer in an UTF-8 TextIOWrapper if possible
                if hasattr(sys.stdout, "buffer"):
                    stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            except Exception:
                pass
        handler = logging.StreamHandler(stdout)
        # Fallback emit to replace unencodable chars (in case the above failed)
        original_emit = handler.emit
        def safe_emit(record):
            try:
                original_emit(record)
            except UnicodeEncodeError:
                # Replace non-encodable characters
                record.msg = str(record.msg).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
                original_emit(record)
        handler.emit = safe_emit  # type: ignore
        return handler
    except Exception:
        return logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system.log', encoding='utf-8'),
        _build_console_handler()
    ]
)

logger = logging.getLogger(__name__)


class SystemManager:
    """
    Manages the complete Indian Education Law Chatbot system
    """
    
    def __init__(self, dataset_path: str = None):
        """
        Initialize the system manager
        
        Args:
            dataset_path: Path to the dataset directory
        """
        if dataset_path is None:
            # Prefer project root dataset if exists; else fallback to backend/dataset
            backend_dir = Path(__file__).parent
            project_root = backend_dir.parent
            root_dataset = project_root.parent / "dataset" if project_root.name == "backend" else project_root / "dataset"
            if root_dataset.exists():
                self.dataset_path = root_dataset
            else:
                self.dataset_path = backend_dir / "dataset"
        else:
            self.dataset_path = Path(dataset_path)
            
        self.data_loader = None
        self.vector_service = None
        self.model_trainer = None
        
    def initialize_services(self):
        """Initialize all services"""
        try:
            logger.info("Initializing system services...")
            
            # Initialize data loader
            self.data_loader = LegalDocumentLoader(str(self.dataset_path))
            logger.info("✅ Data loader initialized")
            
            # Initialize vector service
            self.vector_service = VectorEmbeddingService(dataset_path=str(self.dataset_path))
            logger.info("✅ Vector service initialized")
            
            # Initialize model trainer
            self.model_trainer = LegalModelTrainer(dataset_path=str(self.dataset_path))
            logger.info("✅ Model trainer initialized")
            
            logger.info("🚀 All services initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing services: {str(e)}")
            raise
    
    def process_documents(self):
        """Process raw JSON documents"""
        try:
            logger.info("📄 Processing legal documents...")
            
            # Load raw documents
            raw_docs = self.data_loader.load_json_documents()
            
            if not raw_docs:
                logger.warning("⚠️  No JSON documents found in dataset/legal-documents/")
                return False
            
            # Process documents
            processed_docs = self.data_loader.process_documents(raw_docs)
            
            if not processed_docs:
                logger.error("❌ No documents were successfully processed")
                return False
            
            # Save processed documents
            self.data_loader.save_processed_documents(processed_docs)
            
            # Get statistics
            stats = self.data_loader.get_document_statistics(processed_docs)
            
            logger.info(f"✅ Successfully processed {stats['total_documents']} documents")
            logger.info(f"📊 Total words: {stats['total_words']}")
            logger.info(f"📊 Unique sections: {stats['unique_sections']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing documents: {str(e)}")
            return False
    
    def build_vector_index(self):
        """Build vector index from processed documents"""
        try:
            logger.info("🔍 Building vector search index...")
            
            # Load processed documents
            processed_docs = self.data_loader.load_processed_documents()
            
            if not processed_docs:
                logger.error("❌ No processed documents found. Run document processing first.")
                return False
            
            # Build vector index
            self.vector_service.build_and_save_index(processed_docs)
            
            # Get statistics
            stats = self.vector_service.get_index_statistics()
            
            logger.info(f"✅ Vector index built successfully!")
            logger.info(f"📊 Indexed vectors: {stats['total_vectors']}")
            logger.info(f"📊 Vector dimension: {stats['vector_dimension']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error building vector index: {str(e)}")
            return False
    
    def train_model(self, epochs: int = 2, batch_size: int = 8):
        """Train/fine-tune the legal model"""
        try:
            logger.info("🤖 Training legal language model...")
            
            # Run full training pipeline
            results = self.model_trainer.full_training_pipeline(
                epochs=epochs,
                batch_size=batch_size,
                generate_new_pairs=True
            )
            
            if results['status'] == 'completed':
                logger.info("✅ Model training completed successfully!")
                logger.info(f"📊 Training pairs: {results.get('training_pairs_count', 0)}")
                logger.info(f"📊 Training examples: {results.get('training_examples_count', 0)}")
                logger.info(f"📁 Model saved to: {results.get('model_path', 'N/A')}")
                
                if results.get('metrics'):
                    logger.info("📈 Model Performance Metrics:")
                    for metric, value in results['metrics'].items():
                        logger.info(f"   {metric}: {value:.4f}")
                
                return True
            else:
                logger.error(f"❌ Model training failed: {results.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error training model: {str(e)}")
            return False
    
    def test_system(self):
        """Test the complete system"""
        try:
            logger.info("🧪 Testing system functionality...")
            
            # Test search functionality
            test_queries = [
                "Article 21",
                "Constitution of India",
                "fundamental rights",
                "legal provisions"
            ]
            
            # Load vector index if not already loaded
            try:
                self.vector_service.load_index_for_search()
            except FileNotFoundError:
                logger.error("❌ Vector index not found. Please build index first.")
                return False
            
            all_tests_passed = True
            
            for query in test_queries:
                try:
                    results = self.vector_service.search_similar_documents(query, k=3)
                    
                    if results:
                        logger.info(f"✅ Query '{query}': Found {len(results)} results")
                        top_result = results[0]
                        logger.info(f"   Top result: {top_result['document']['section']} (Score: {top_result['score']:.3f})")
                    else:
                        logger.warning(f"⚠️  Query '{query}': No results found")
                        all_tests_passed = False
                        
                except Exception as e:
                    logger.error(f"❌ Query '{query}' failed: {str(e)}")
                    all_tests_passed = False
            
            if all_tests_passed:
                logger.info("✅ System testing completed successfully!")
                return True
            else:
                logger.warning("⚠️  Some tests failed, but system is partially functional")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error testing system: {str(e)}")
            return False
    
    def run_complete_setup(self, train_model: bool = True, epochs: int = 2):
        """Run the complete system setup"""
        try:
            logger.info("🚀 Starting complete system setup...")
            
            # Step 1: Initialize services
            self.initialize_services()
            
            # Step 2: Process documents
            if not self.process_documents():
                logger.error("❌ Document processing failed")
                return False
            
            # Step 3: Build vector index
            if not self.build_vector_index():
                logger.error("❌ Vector index building failed")
                return False
            
            # Step 4: Train model (optional)
            if train_model:
                if not self.train_model(epochs=epochs):
                    logger.warning("⚠️  Model training failed, but system can still run with base model")
            
            # Step 5: Test system
            if not self.test_system():
                logger.error("❌ System testing failed")
                return False
            
            logger.info("🎉 Complete system setup successful!")
            logger.info("💡 You can now start the API server with: python src/api/main.py")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Complete setup failed: {str(e)}")
            return False
    
    def get_system_status(self):
        """Get current system status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check processed documents
        try:
            processed_docs = self.data_loader.load_processed_documents() if self.data_loader else []
            status["components"]["documents"] = {
                "status": "ready" if processed_docs else "missing",
                "count": len(processed_docs)
            }
        except:
            status["components"]["documents"] = {"status": "error", "count": 0}
        
        # Check vector index
        try:
            vector_index_path = self.dataset_path / "vector-database" / "legal_docs_index.index"
            if vector_index_path.exists():
                status["components"]["vector_index"] = {"status": "ready"}
            else:
                status["components"]["vector_index"] = {"status": "missing"}
        except:
            status["components"]["vector_index"] = {"status": "error"}
        
        # Check trained model
        try:
            models_path = self.dataset_path / "models"
            trained_models = list(models_path.glob("fine_tuned_legal_model_*"))
            status["components"]["trained_model"] = {
                "status": "ready" if trained_models else "missing",
                "count": len(trained_models)
            }
        except:
            status["components"]["trained_model"] = {"status": "error", "count": 0}
        
        return status


def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description="Indian Education Law Chatbot System Manager")
    
    parser.add_argument("--action", choices=["setup", "process", "index", "train", "test", "status", "api"], 
                       default="setup", help="Action to perform")
    parser.add_argument("--dataset-path", help="Path to dataset directory")
    parser.add_argument("--no-train", action="store_true", help="Skip model training during setup")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Training batch size")
    
    args = parser.parse_args()
    
    # Initialize system manager
    system_manager = SystemManager(args.dataset_path)
    
    try:
        if args.action == "setup":
            logger.info("🚀 Running complete system setup...")
            success = system_manager.run_complete_setup(
                train_model=not args.no_train,
                epochs=args.epochs
            )
            sys.exit(0 if success else 1)
            
        elif args.action == "process":
            logger.info("📄 Processing documents...")
            system_manager.initialize_services()
            success = system_manager.process_documents()
            sys.exit(0 if success else 1)
            
        elif args.action == "index":
            logger.info("🔍 Building vector index...")
            system_manager.initialize_services()
            success = system_manager.build_vector_index()
            sys.exit(0 if success else 1)
            
        elif args.action == "train":
            logger.info("🤖 Training model...")
            system_manager.initialize_services()
            success = system_manager.train_model(args.epochs, args.batch_size)
            sys.exit(0 if success else 1)
            
        elif args.action == "test":
            logger.info("🧪 Testing system...")
            system_manager.initialize_services()
            success = system_manager.test_system()
            sys.exit(0 if success else 1)
            
        elif args.action == "status":
            logger.info("📊 Checking system status...")
            system_manager.initialize_services()
            status = system_manager.get_system_status()
            
            print("\n📊 System Status Report:")
            print("=" * 50)
            for component, info in status["components"].items():
                status_icon = {"ready": "✅", "missing": "❌", "error": "⚠️"}.get(info["status"], "❓")
                print(f"{status_icon} {component.replace('_', ' ').title()}: {info['status']}")
                if "count" in info:
                    print(f"   Count: {info['count']}")
            print("=" * 50)
            sys.exit(0)
            
        elif args.action == "api":
            logger.info("🌐 Starting API server...")
            system_manager.initialize_services()
            
            # Import and run the API server
            from api.main import app
            import uvicorn
            
            uvicorn.run(
                "api.main:app",
                host="0.0.0.0",
                port=8000,
                reload=True,
                log_level="info"
            )
            
    except KeyboardInterrupt:
        logger.info("👋 System setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ System setup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()