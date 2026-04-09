"""
Gemini AI Service for Legal Chatbot
Provides fallback to Gemini API when dataset doesn't have sufficient information
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Gemini fallback will not work.")


class GeminiService:
    """
    Service for interacting with Google Gemini API
    Acts as a lawyer assistant when dataset doesn't have answers
    """
    
    def __init__(self):
        """Initialize Gemini service"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini SDK not available. Install with: pip install google-generativeai")
            return
            
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables. Gemini fallback disabled.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            # Use gemini-1.5-flash (stable and widely available)
            # You can change to gemini-2.0-flash-exp if you have access
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("✅ Gemini service initialized successfully with model: gemini-1.5-flash")
        except Exception as e:
            logger.error(f"Error initializing Gemini: {str(e)}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini service is available"""
        return GEMINI_AVAILABLE and self.api_key is not None and self.model is not None
    
    def generate_legal_answer(self, question: str, context: str = "") -> Optional[str]:
        """
        Generate a legal answer using Gemini AI as a lawyer assistant
        
        Args:
            question: User's legal question
            context: Optional context from dataset search (even if low confidence)
            
        Returns:
            Generated answer or None if service unavailable
        """
        if not self.is_available():
            return None
        
        try:
            # System prompt - act as a lawyer assistant
            system_prompt = """You are an experienced legal assistant specializing in Indian law. 
You provide general legal information and guidance based on Indian legal framework.

IMPORTANT GUIDELINES:
- Focus ONLY on Indian laws: IPC, CrPC, Evidence Act, Constitution of India, Indian Contract Act, 
  Family Law, Property Law, IT Act, Consumer Law, Labour Law, Education Law, and other Indian statutes.
- Do NOT mention US, UK, or other foreign laws.
- Provide clear, simple explanations in plain language.
- You are NOT providing professional legal advice - you are providing general legal information.
- Always suggest consulting a qualified advocate for specific legal matters.
- If the question is not related to Indian law, politely explain that you specialize in Indian legal matters.

Be helpful, professional, and empathetic. Structure your answer clearly with proper formatting."""

            # Build the prompt
            prompt_parts = [system_prompt]
            
            # Add context if available (even if low confidence, it might have some relevance)
            if context:
                prompt_parts.append(f"\n\nContext from legal database (may be limited):\n{context}")
            
            prompt_parts.append(f"\n\nUser Question: {question}")
            prompt_parts.append("\n\nPlease provide a helpful legal answer as a lawyer assistant:")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Clean the response
            answer = response.text.strip()
            
            # Remove any repeated user question
            if answer.lower().startswith(question.lower()):
                answer = answer[len(question):].strip()
            
            # Add disclaimer
            answer += "\n\n**Note:** This answer is provided by an AI legal assistant and is for informational purposes only. It is not a substitute for professional legal advice. Please consult a qualified advocate for specific legal matters."
            
            logger.info("Gemini answer generated successfully")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating Gemini answer: {str(e)}")
            return None
    
    def clean_reply(self, user_message: str, ai_reply: str) -> str:
        """
        Clean AI reply to remove repeated user message
        
        Args:
            user_message: Original user message
            ai_reply: AI generated reply
            
        Returns:
            Cleaned reply
        """
        if not ai_reply:
            return ""
        
        cleaned = ai_reply.strip()
        lower_user = user_message.lower().strip()
        
        # Remove user message if it appears at the start
        if cleaned.lower().startswith(lower_user):
            cleaned = cleaned[len(user_message):].strip()
        
        # Remove user message anywhere (case insensitive)
        import re
        cleaned = re.sub(re.escape(user_message), "", cleaned, flags=re.IGNORECASE).strip()
        
        return cleaned


# Global instance
_gemini_service: Optional[GeminiService] = None

def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
