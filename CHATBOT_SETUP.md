# Chatbot Setup Guide - AI/ML Backend Integration

## ✅ Changes Made

The `/user/chatbot` page has been updated to use the **Python FastAPI AI/ML Backend** for legal document search with **Gemini AI fallback** when dataset doesn't have answers.

### Updated Files:
1. ✅ `law-frontend-main/src/views/Dashboard/Chatbot.jsx` - Now calls FastAPI backend with source indicators
2. ✅ `law-frontend-main/src/controllers/chatController.js` - Updated to use FastAPI
3. ✅ `law-frontend-main/src/config/apiConfig.js` - New centralized API configuration
4. ✅ `backend/src/services/gemini_service.py` - New Gemini AI service for fallback
5. ✅ `backend/src/api/main.py` - Updated chat endpoint with Gemini fallback logic
6. ✅ `backend/requirements.txt` - Added google-generativeai package

---

## 🚀 Setup Instructions

### Step 1: Start the Python FastAPI Backend

The chatbot requires the Python FastAPI backend to be running on **port 5000**.

```bash
# Navigate to backend directory
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Set up Gemini API key (optional but recommended for fallback)
# Create a .env file in the backend directory:
# GEMINI_API_KEY=your_gemini_api_key_here
# Get your API key from: https://makersuite.google.com/app/apikey

# Initialize the system (first time only)
# This processes documents and builds the vector index
python run_system.py --action setup

# Start the FastAPI server
python src/api/main.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on https://llm.skyzin.com
```

**Alternative:** You can also use uvicorn directly:
```bash
cd backend
uvicorn src.api.main:app --host 127.0.0.1 --port 5000 --reload
```

### Step 2: Verify Backend is Running

Open your browser and visit:
- **API Health Check:** https://llm.skyzin.com/api/health
- **API Documentation:** https://llm.skyzin.com/docs

You should see:
- Health endpoint returns system status
- Swagger UI shows all available endpoints

### Step 3: Start the React Frontend

```bash
# Navigate to frontend directory
cd law-frontend-main

# Install dependencies (if not already done)
npm install

# Start the development server
npm run dev
```

The frontend will run on **https://lawlink.skyzin.com**

### Step 4: Test the Chatbot

1. Navigate to: https://lawlink.skyzin.com/user/chatbot
2. Ask a legal question, for example:
   - "What is Article 21?"
   - "Tell me about the Right to Education Act"
   - "What are fundamental rights?"

The chatbot will:
- ✅ **First check the dataset** - Search through legal documents using the AI/ML backend
- ✅ **Fallback to Gemini AI** - If confidence is low (< 30%) or no results found, uses Gemini as a lawyer assistant
- ✅ Return answers with sources (for dataset answers)
- ✅ Show confidence scores (for dataset answers)
- ✅ Display answer source indicator (Dataset 📚 or AI Assistant 🤖)
- ✅ Display relevant legal sections (for dataset answers)

---

## 🔧 API Configuration

The API endpoints are now centralized in `law-frontend-main/src/config/apiConfig.js`:

```javascript
// AI/ML Backend (Python FastAPI) - Port 5000
AI_BACKEND: {
  baseURL: "https://llm.skyzin.com/api",
  endpoints: {
    chat: "/chat",
    search: "/search",
    health: "/health"
  }
}

// User Management Backend (Node.js) - Port 8000
USER_BACKEND: {
  baseURL: "https://law-api.skyzin.com/api",
  endpoints: {
    auth: "/auth/login",
    // ... other endpoints
  }
}
```

---

## 📡 API Request/Response Format

### Request to FastAPI Backend:
```json
{
  "question": "What is Article 21?",
  "context": "",
  "source_mode": "json_only"
}
```

### Response from FastAPI Backend (Dataset Answer):
```json
{
  "answer": "Based on the legal documents...",
  "sources": [
    {
      "section": "Article 21",
      "title": "Constitution of India",
      "year": "1950",
      "score": 0.95,
      "content_preview": "..."
    }
  ],
  "confidence": 0.95,
  "query_time": 0.123,
  "disclaimer": "This system provides information...",
  "answer_source": "dataset"
}
```

### Response from FastAPI Backend (Gemini Fallback):
```json
{
  "answer": "As a legal assistant, I can help you understand...",
  "sources": [],
  "confidence": 0.5,
  "query_time": 1.456,
  "disclaimer": "This answer is provided by an AI legal assistant...",
  "answer_source": "gemini"
}
```

## 🔄 How Fallback Works

1. **Dataset Search First**: The system searches your legal document database
2. **Confidence Check**: If confidence ≥ 30% and results found → Use dataset answer
3. **Gemini Fallback**: If confidence < 30% or no results → Use Gemini AI as lawyer assistant
4. **Context Sharing**: Even when using Gemini, any relevant dataset context is shared

**Confidence Threshold**: 0.3 (30%) - This can be adjusted in `backend/src/api/main.py`

---

## 🐛 Troubleshooting

### Issue: "Unable to connect to the AI/ML backend"

**Solution:**
1. Check if Python FastAPI backend is running:
   ```bash
   # Check if port 5000 is in use
   netstat -an | findstr :5000  # Windows
   lsof -i :5000                # Mac/Linux
   ```

2. Verify the backend is accessible:
   ```bash
   curl https://llm.skyzin.com/api/health
   ```

3. Check backend logs for errors

### Issue: "No processed documents found"

**Solution:**
```bash
cd backend
python run_system.py --action process
python run_system.py --action index
```

### Issue: "JSON query engine not initialized"

**Solution:**
The backend needs processed documents. Run:
```bash
cd backend
python run_system.py --action setup
```

### Issue: "Gemini service not available" or "GEMINI_API_KEY not found"

**Solution:**
1. Get a Gemini API key from: https://makersuite.google.com/app/apikey
2. Create a `.env` file in the `backend/` directory:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. Restart the FastAPI server
4. **Note**: The chatbot will still work without Gemini, but won't have fallback for questions not in the dataset

### Issue: CORS Errors

**Solution:**
The FastAPI backend already has CORS configured for `https://lawlink.skyzin.com`. If you see CORS errors:
1. Check `backend/src/api/main.py` - CORS middleware should allow `https://lawlink.skyzin.com`
2. Restart the FastAPI server

---

## 📊 What Changed

### Before:
- Chatbot called Node.js backend (port 8000)
- Used Gemini API for all questions
- No legal document search

### After:
- Chatbot calls Python FastAPI backend (port 5000)
- **Smart Two-Tier System**:
  1. **Primary**: Searches legal document database (Constitution, IPC, CrPC, Education Law)
  2. **Fallback**: Uses Gemini AI as lawyer assistant when dataset doesn't have answer
- Returns answers with sources and confidence scores (for dataset answers)
- Shows answer source indicator (Dataset 📚 or AI Assistant 🤖)
- Better user experience with intelligent fallback

---

## 🎯 Next Steps

1. **Start both backends:**
   - Python FastAPI (port 5000) - for chatbot
   - Node.js Express (port 8000) - for user management

2. **Test the chatbot:**
   - Try various legal questions
   - Check that sources are displayed
   - Verify confidence scores

3. **Optional Enhancements:**
   - Add UI to display sources in a collapsible section
   - Show query time to users
   - Add loading states with better UX
   - Implement query history

---

## 📝 Notes

- The chatbot now uses the **AI/ML Backend** exclusively for legal document search
- The Node.js backend's `/api/chat` endpoint (Gemini) is still available but not used by the chatbot
- Both backends can run simultaneously on different ports
- The frontend automatically handles errors and shows helpful messages

---

## ✅ Verification Checklist

- [ ] Python FastAPI backend running on port 5000
- [ ] Documents processed and indexed
- [ ] React frontend running on port 5173
- [ ] Can access `/user/chatbot` page
- [ ] Chatbot returns answers with sources
- [ ] No CORS errors in browser console
- [ ] Backend logs show successful requests

---

**Need Help?** Check the backend logs in `backend/system.log` for detailed error messages.
